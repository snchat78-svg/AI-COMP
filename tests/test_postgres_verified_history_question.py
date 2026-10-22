from ai_comp.database.postgres_verified_history_question import (
    PostgresVerifiedHistoryQuestionRepository,
)
from ai_comp.database.postgres_generated_question import PostgresGeneratedQuestionRepository
from ai_comp.domain.material_generation import QuestionSourceKind


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self, rows=(), *, total_count=None):
        self.rows = tuple(rows)
        self.total_count = len(self.rows) if total_count is None else total_count
        self.calls = []

    def execute(self, query, params):
        self.calls.append((query, params))
        if not self.rows:
            return FakeCursor([(None,) * 13 + (self.total_count,)])
        return FakeCursor([tuple(row) + (self.total_count,) for row in self.rows])


def row(*, correct_answer="B", appearances=2):
    return (
        "question-source-1",
        "राजस्थान के क्षेत्रफल से संबंधित सही कथन कौन सा है?",
        [
            {"key": "A", "text": "विकल्प एक"},
            {"key": "B", "text": "सही विकल्प"},
            {"key": "C", "text": "विकल्प तीन"},
            {"key": "D", "text": "विकल्प चार"},
        ],
        correct_answer,
        "RAJ_EXAM",
        "Rajasthan recruitment exam",
        2024,
        "MORNING",
        7,
        "https://official.example/paper.pdf",
        "https://official.example/key.pdf",
        ["rajasthan-area"],
        appearances,
    )


def test_repository_returns_historical_question_with_official_paper_key_and_exam_provenance():
    connection = FakeConnection([row()])
    repository = PostgresVerifiedHistoryQuestionRepository(connection)

    questions = repository.list_eligible(limit=50, concept_ids=["rajasthan-area"])

    assert len(questions) == 1
    question = questions[0]
    assert question.generated_question_id == "verified-history:question-source-1"
    assert question.source_kind is QuestionSourceKind.VERIFIED_EXAM_HISTORY
    assert question.correct_option_key == "B"
    assert question.exam_name == "Rajasthan recruitment exam"
    assert question.exam_year == 2024
    assert question.exam_shift == "MORNING"
    assert question.exam_question_number == 7
    assert question.verified_appearance_count == 2
    assert question.source_url == "https://official.example/paper.pdf"
    assert question.answer_key_source_url == "https://official.example/key.pdf"
    assert connection.calls[0][1] == (
        None, None, None, None, None, None, None, None, None, None,
        ["rajasthan-area"], ["rajasthan-area"], 50, 0,
    )


def test_repository_query_fails_closed_unless_official_paper_and_matched_official_key_are_verified():
    connection = FakeConnection()
    repository = PostgresVerifiedHistoryQuestionRepository(connection)

    assert repository.list_eligible(limit=10) == ()
    query = connection.calls[0][0]
    for required_gate in (
        "pair.pair_status = 'MATCHED'",
        "qv.status = 'VERIFIED'",
        "qv.evidence_type = 'OFFICIAL_PAPER'",
        "kv.status = 'VERIFIED'",
        "kv.evidence_type = 'OFFICIAL_ANSWER_KEY'",
        "resolved.status = 'RESOLVED'",
        "resolved.selected_option_key = a.correct_answer",
        "qs.priority = 'OFFICIAL'",
        "ks.priority = 'OFFICIAL'",
        "qv.source_url LIKE 'https://%%'",
        "kv.source_url LIKE 'https://%%'",
        "options.option_count = 4",
    ):
        assert required_gate in query


def test_repository_normalizes_key_case_to_the_exact_paper_option_key():
    connection = FakeConnection([row(correct_answer="b")])

    question = PostgresVerifiedHistoryQuestionRepository(connection).list_eligible(limit=1)[0]

    assert question.correct_option_key == "B"


def test_repository_rejects_invalid_limit_and_ambiguous_concept_filters():
    repository = PostgresVerifiedHistoryQuestionRepository(FakeConnection())

    for bad_limit in (True, 0, -1, 10001):
        try:
            repository.list_eligible(limit=bad_limit)
        except ValueError as exc:
            assert "limit" in str(exc)
        else:
            raise AssertionError("invalid limit must be rejected")


    try:
        repository.list_eligible(source_domain="https://official.example")
    except ValueError as exc:
        assert "source_domain" in str(exc)
    else:
        raise AssertionError("source_domain must be a plain host name")

    try:
        repository.list_eligible(concept_ids=["topic", "topic"])
    except ValueError as exc:
        assert "concept_ids" in str(exc)
    else:
        raise AssertionError("duplicate concept filters must be rejected")


def test_historical_question_cannot_be_written_to_generated_question_table():
    question = PostgresVerifiedHistoryQuestionRepository._from_row(row())
    connection = FakeConnection()

    try:
        PostgresGeneratedQuestionRepository(connection).save(question)
    except ValueError as exc:
        assert "historical source tables" in str(exc)
    else:
        raise AssertionError("historical provenance must not be persisted as AI-generated")
    assert connection.calls == []


def test_page_returns_exact_count_with_bounded_pagination_and_appearance_filters():
    connection = FakeConnection([row(appearances=3)], total_count=17)
    repository = PostgresVerifiedHistoryQuestionRepository(connection)

    page = repository.list_eligible_page(
        limit=1,
        offset=4,
        concept_ids=["rajasthan-area"],
        subject_id="Rajasthan Geography",
        exam_id="RAJ_EXAM",
        exam_year=2024,
        exam_shift="MORNING",
    )

    assert page.total_count == 17
    assert len(page.items) == 1
    assert page.items[0].verified_appearance_count == 3
    query, params = connection.calls[0]
    assert "exam_id = %s" in query
    assert "exam_year = %s" in query
    assert "lower(btrim(exam_shift)) = lower(%s)" in query
    # Repeat count is computed before selecting a specific appearance filter.
    assert query.index("COUNT(*) OVER") < query.index("WHERE (%s::TEXT IS NULL OR exam_id = %s)")
    assert params == (
        "Rajasthan Geography", "Rajasthan Geography",
        "RAJ_EXAM", "RAJ_EXAM",
        2024, 2024,
        "MORNING", "MORNING",
        None, None,
        ["rajasthan-area"], ["rajasthan-area"],
        1, 4,
    )


def test_page_preserves_total_count_when_offset_is_beyond_last_row():
    connection = FakeConnection((), total_count=3)
    page = PostgresVerifiedHistoryQuestionRepository(connection).list_eligible_page(
        limit=10,
        offset=500,
        concept_ids=["rajasthan-area"],
    )
    assert page.items == ()
    assert page.total_count == 3


def test_repository_rejects_invalid_exam_filters():
    repository = PostgresVerifiedHistoryQuestionRepository(FakeConnection())
    for kwargs, expected in (
        ({"exam_id": " RAJ_EXAM"}, "exam_id"),
        ({"exam_year": 1800}, "exam_year"),
        ({"exam_shift": "MORNING "}, "exam_shift"),
    ):
        try:
            repository.list_eligible(**kwargs)
        except ValueError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"invalid {expected} must be rejected")
