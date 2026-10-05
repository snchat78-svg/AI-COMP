from ai_comp.database.postgres_master_question import PostgresMasterQuestionRepository
from ai_comp.domain.master_questions import (
    MasterMembershipType,
    MasterQuestion,
    MasterQuestionMembership,
    MasterQuestionStatus,
)
from ai_comp.domain.questions import QuestionKind, QuestionOption


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


def master():
    return MasterQuestion(
        master_question_id="m1",
        canonical_question_id="q1",
        stem="राजस्थान का उदाहरण?",
        options=(
            QuestionOption("A", "एक"),
            QuestionOption("B", "दो"),
        ),
        kind=QuestionKind.MCQ,
        status=MasterQuestionStatus.ACTIVE,
    )


def membership():
    return MasterQuestionMembership(
        master_question_id="m1",
        question_id="q1",
        relationship=MasterMembershipType.CANONICAL,
        confidence=1.0,
    )


def master_row():
    return ("m1", "q1", "राजस्थान का उदाहरण?", "MCQ", None, "ACTIVE", None)


def test_master_repository_writes_ordered_options():
    conn = Connection()
    repo = PostgresMasterQuestionRepository(conn)

    repo.save_master(master())

    assert "INSERT INTO master_questions" in conn.calls[0][0]
    assert conn.calls[1][1] == ("m1",)
    assert conn.calls[2][1] == ("m1", "A", "एक", 1)
    assert conn.calls[3][1] == ("m1", "B", "दो", 2)


def test_master_repository_reads_master_and_options():
    conn = Connection()
    conn.results = [
        Result(row=master_row()),
        Result(rows=[("A", "एक"), ("B", "दो")]),
    ]

    loaded = PostgresMasterQuestionRepository(conn).get_master("m1")

    assert loaded == master()


def test_master_repository_reads_question_membership():
    conn = Connection()
    conn.results = [Result(row=("m1", "q1", "CANONICAL", 1.0))]

    loaded = PostgresMasterQuestionRepository(conn).get_membership_for_question("q1")

    assert loaded == membership()


def test_master_repository_rejects_different_existing_membership():
    conn = Connection()
    conn.results = [Result(row=("m2", "q1", "CANONICAL", 1.0))]

    import pytest

    with pytest.raises(Exception, match="already assigned"):
        PostgresMasterQuestionRepository(conn).save_membership(membership())
