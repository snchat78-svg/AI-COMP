from ai_comp.database.postgres_concept import PostgresConceptRepository
from ai_comp.domain.matching import ConceptRecord


class Result:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class Connection:
    def __init__(self, row=None):
        self.row = row
        self.calls = []

    def transaction(self):
        class Tx:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
        return Tx()

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return Result(self.row)


def test_concept_repository_round_trip_contract():
    conn = Connection(("C1", "Rajasthan Geography", "Geography", "Districts", None))
    repo = PostgresConceptRepository(conn)

    concept = ConceptRecord(
        concept_id="C1",
        label="Rajasthan Geography",
        subject="Geography",
        topic="Districts",
    )
    repo.save(concept)
    assert repo.get("C1") == concept
    repo.link_question("q1", "C1")

    assert "INSERT INTO concepts" in conn.calls[0][0]
    assert "question_concepts" in conn.calls[2][0]
