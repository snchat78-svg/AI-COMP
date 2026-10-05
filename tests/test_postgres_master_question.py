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
    conn.results = [
        Result(row=("ACTIVE",)),
        Result(row=("m2", "q1", "CANONICAL", 1.0)),
    ]

    import pytest

    with pytest.raises(Exception, match="already assigned"):
        PostgresMasterQuestionRepository(conn).save_membership(membership())


def test_master_repository_lists_masters_with_filters_and_paging():
    conn = Connection()
    conn.results = [
        Result(rows=[master_row()]),
        Result(rows=[("A", "एक"), ("B", "दो")]),
    ]

    masters = PostgresMasterQuestionRepository(conn).list_masters(
        status=MasterQuestionStatus.ACTIVE,
        concept_id=None,
        limit=10,
        offset=0,
    )

    assert masters == (master(),)
    assert conn.calls[0][1] == ("ACTIVE", 10, 0)


def test_master_repository_merge_moves_source_memberships_and_audits():
    conn = Connection()
    conn.results = [
        Result(rows=[("m1", "ACTIVE"), ("m2", "ACTIVE")]),
        Result(rows=[("q1", "CANONICAL", 1.0)]),
    ]

    moved = PostgresMasterQuestionRepository(conn).merge_masters(
        "m1",
        "m2",
        reason="duplicate review",
    )

    assert moved == 1
    assert "UPDATE master_questions" in conn.calls[-2][0]
    assert "master_merge_events" in conn.calls[-1][0]
    assert conn.calls[2][1] == ("m2", "q1", "EXACT", 1.0)


def test_master_repository_repair_moves_membership_and_audits():
    conn = Connection()
    conn.results = [
        Result(row=("ACTIVE",)),
        Result(row=("m1", "REPHRASED", 0.91)),
        Result(row=("ACTIVE",)),
    ]

    PostgresMasterQuestionRepository(conn).reassign_question(
        "q2",
        "m2",
        relationship=MasterMembershipType.EXACT,
        confidence=1.0,
        reason="manual correction",
    )

    assert "DELETE FROM master_question_memberships" in conn.calls[3][0]
    assert "INSERT INTO master_question_memberships" in conn.calls[4][0]
    assert "master_repair_events" in conn.calls[5][0]


def test_master_repository_rejects_membership_to_inactive_master():
    conn = Connection()
    conn.results = [Result(row=("MERGED",))]

    import pytest

    with pytest.raises(Exception, match="not active"):
        PostgresMasterQuestionRepository(conn).save_membership(
            membership()
        )
