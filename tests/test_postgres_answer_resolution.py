from ai_comp.database.postgres_answer_resolution import (
    PostgresAnswerResolutionRepository,
)
from ai_comp.domain.answers import (
    AnswerResolution,
    AnswerResolutionMethod,
    AnswerResolutionStatus,
)


class FakeResult:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows=()):
        self.rows = rows
        self.calls = []

    def transaction(self):
        class Tx:
            def __enter__(inner):
                return inner
            def __exit__(inner, exc_type, exc, tb):
                return False
        return Tx()

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return FakeResult(self.rows)


def test_answer_resolution_repository_round_trip_contract():
    connection = FakeConnection(
        rows=[
            (
                "q1",
                "doc1",
                1,
                "B",
                "B",
                "RESOLVED",
                "DIRECT_OPTION_KEY",
                10,
                "",
            )
        ]
    )
    repository = PostgresAnswerResolutionRepository(connection)
    resolution = AnswerResolution(
        question_id="q1",
        document_id="doc1",
        question_number=1,
        answer_key="B",
        selected_option_key="B",
        status=AnswerResolutionStatus.RESOLVED,
        method=AnswerResolutionMethod.DIRECT_OPTION_KEY,
        source_line=10,
    )

    repository.save(resolution)
    loaded = repository.get_for_question("q1")[0]

    assert loaded == resolution
    assert "question_answer_records" in connection.calls[0][0]
    assert "question_answer_records" in connection.calls[1][0]
