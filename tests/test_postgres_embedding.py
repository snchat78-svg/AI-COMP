import pytest

from ai_comp.database.models import EmbeddingModelRecord
from ai_comp.database.postgres_embedding import PostgresEmbeddingRepository


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
        if self.results:
            return self.results.pop(0)
        return Result()


def test_embedding_repository_validates_dimensions_and_round_trips_vector():
    conn = Connection()
    repo = PostgresEmbeddingRepository(conn)
    conn.results = [Result(row=(3,)), Result(), Result(row=("[0.1,0.2,0.3]",))]

    repo.save_model(
        EmbeddingModelRecord(
            model_id="m1",
            provider="test",
            model_name="embedding",
            dimensions=3,
        )
    )
    repo.save_embedding("q1", "m1", (0.1, 0.2, 0.3))
    assert repo.get_embedding("q1", "m1") == (0.1, 0.2, 0.3)


def test_embedding_repository_rejects_dimension_mismatch():
    conn = Connection()
    conn.results = [Result(row=(3,))]
    with pytest.raises(ValueError, match="dimension"):
        PostgresEmbeddingRepository(conn).save_embedding("q1", "m1", (0.1, 0.2))


def test_embedding_repository_nearest_neighbors_contract():
    conn = Connection()
    conn.results = [
        Result(row=(3,)),
        Result(rows=[("q2", 0.99), ("q3", 0.91)]),
    ]
    result = PostgresEmbeddingRepository(conn).nearest_neighbors(
        "m1",
        (0.1, 0.2, 0.3),
        limit=2,
        exclude_question_id="q1",
    )

    assert result == (("q2", 0.99), ("q3", 0.91))
    assert "embedding <=>" in conn.calls[1][0]
    assert conn.calls[1][1][-1] == 2
