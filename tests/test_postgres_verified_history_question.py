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
    def __init__(self, rows=()):
        self.rows = tuple(rows)
        self.calls = []

    def execute(self, query, params):
        self.calls.append((query, params))
        return FakeCursor(self.rows)


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
    assert connection.calls[0][1] == (["rajasthan-area"], ["rajasthan-area"], 50)


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
