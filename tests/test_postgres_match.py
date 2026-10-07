from ai_comp.database.postgres_match import PostgresMatchRepository
from ai_comp.domain.matching import MatchType, QuestionMatch


class Result:
    def __init__(self, row=None, rows=()):
        self.row = row
        self.rows = list(rows)

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class Connection:
    def __init__(self):
        self.calls = []
        self.results = []

    def transaction(self):
        class Tx:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
        return Tx()

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return self.results.pop(0) if self.results else Result()


def test_match_repository_canonicalizes_symmetric_pair():
    conn = Connection()
    conn.results = [Result(row=(7,))]
    PostgresMatchRepository(conn).save(
        QuestionMatch("q2", "q1", MatchType.EXACT, 1.0)
    )

    assert conn.calls[0][1][:2] == ("q1", "q2")
    assert "ON CONFLICT (left_question_id, right_question_id)" in conn.calls[0][0]


def test_match_repository_reads_evidence():
    conn = Connection()
    conn.results = [
        Result(rows=[(7, "q1", "q2", "REPHRASED", 0.96)]),
        Result(rows=[("embedding_cosine", 0.96, "semantic")]),
    ]
    result = PostgresMatchRepository(conn).get_for_question("q1")[0]

    assert result.left_question_id == "q1"
    assert result.right_question_id == "q2"
    assert result.match_type is MatchType.REPHRASED
    assert result.confidence == 0.96
    assert result.evidence[0].method == "embedding_cosine"
