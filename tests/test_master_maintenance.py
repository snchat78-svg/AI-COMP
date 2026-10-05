import pytest

from ai_comp.domain.master_questions import (
    MasterMembershipType,
    MasterQuestion,
    MasterQuestionMembership,
    MasterQuestionStatus,
)
from ai_comp.domain.questions import QuestionKind, QuestionOption
from ai_comp.master.maintenance import MasterQuestionMaintenanceService
from ai_comp.master.policy import MasterAssignmentPolicy
from ai_comp.master.query import MasterQuestionQuery, MasterQuestionReadService
from ai_comp.master.repository import InMemoryMasterQuestionRepository


def master(master_id, question_id, *, concept_id=None):
    return MasterQuestion(
        master_question_id=master_id,
        canonical_question_id=question_id,
        stem=f"question {question_id}",
        options=(QuestionOption("A", "एक"),),
        kind=QuestionKind.MCQ,
        concept_id=concept_id,
    )


def membership(master_id, question_id, relationship, confidence=1.0):
    return MasterQuestionMembership(
        master_question_id=master_id,
        question_id=question_id,
        relationship=relationship,
        confidence=confidence,
    )


def seed(repo, master_id, question_id):
    repo.save_master(master(master_id, question_id))
    repo.save_membership(
        membership(master_id, question_id, MasterMembershipType.CANONICAL)
    )


def test_master_read_view_reports_membership_counts():
    repo = InMemoryMasterQuestionRepository()
    seed(repo, "m1", "q1")
    repo.save_membership(membership("m1", "q2", MasterMembershipType.EXACT))
    repo.save_membership(
        membership("m1", "q3", MasterMembershipType.REPHRASED, 0.96)
    )

    view = MasterQuestionReadService(repo).get_view("m1")

    assert view is not None
    assert view.member_count == 3
    assert view.exact_count == 1
    assert view.rephrased_count == 1


def test_master_query_filters_status_and_concept_and_bounds_page():
    repo = InMemoryMasterQuestionRepository()
    seed(repo, "m1", "q1")
    repo.save_master(master("m2", "q2", concept_id="C1"))
    repo.save_membership(membership("m2", "q2", MasterMembershipType.CANONICAL))
    repo.save_master(
        MasterQuestion(
            master_question_id="m3",
            canonical_question_id="q3",
            stem="question q3",
            options=(QuestionOption("A", "एक"),),
            kind=QuestionKind.MCQ,
        )
    )
    repo.save_master(
        MasterQuestion(
            master_question_id="m3",
            canonical_question_id="q3",
            stem="question q3",
            options=(QuestionOption("A", "एक"),),
            kind=QuestionKind.MCQ,
            status=MasterQuestionStatus.RETIRED,
        )
    )

    views = MasterQuestionReadService(repo).list_views(
        MasterQuestionQuery(
            status=MasterQuestionStatus.ACTIVE,
            concept_id="C1",
            limit=10,
        )
    )

    assert [item.master_question_id for item in views] == ["m2"]


def test_merge_moves_canonical_membership_as_exact_and_marks_source_merged():
    repo = InMemoryMasterQuestionRepository()
    seed(repo, "m1", "q1")
    repo.save_membership(
        membership("m1", "q2", MasterMembershipType.REPHRASED, 0.95)
    )
    seed(repo, "m2", "q3")

    result = MasterQuestionMaintenanceService(repo).merge(
        "m1",
        "m2",
        reason="manual duplicate review",
    )

    assert result.moved_question_count == 2
    assert repo.get_master("m1").status is MasterQuestionStatus.MERGED
    assert repo.get_master("m1").merged_into_master_id == "m2"

    moved = repo.get_membership_for_question("q1")
    assert moved is not None
    assert moved.master_question_id == "m2"
    assert moved.relationship is MasterMembershipType.EXACT
    assert len(repo.get_memberships_for_master("m2")) == 3


def test_repair_moves_noncanonical_membership_and_preserves_one_master_rule():
    repo = InMemoryMasterQuestionRepository()
    seed(repo, "m1", "q1")
    repo.save_membership(membership("m1", "q2", MasterMembershipType.REPHRASED, 0.91))
    seed(repo, "m2", "q3")

    result = MasterQuestionMaintenanceService(repo).repair(
        "q2",
        "m2",
        relationship=MasterMembershipType.EXACT,
        confidence=1.0,
        reason="manual evidence review",
    )

    assert result.source_master_id == "m1"
    assert result.target_master_id == "m2"
    assert repo.get_membership_for_question("q2").master_question_id == "m2"
    assert len(repo.get_memberships_for_master("m1")) == 1
    assert len(repo.get_memberships_for_master("m2")) == 2


def test_repair_rejects_canonical_membership():
    repo = InMemoryMasterQuestionRepository()
    seed(repo, "m1", "q1")
    seed(repo, "m2", "q2")

    with pytest.raises(ValueError, match="canonical membership"):
        MasterQuestionMaintenanceService(repo).repair(
            "q1",
            "m2",
            relationship=MasterMembershipType.EXACT,
            confidence=1.0,
            reason="bad data",
        )


def test_maintenance_requires_reason_for_auditability():
    repo = InMemoryMasterQuestionRepository()
    seed(repo, "m1", "q1")
    seed(repo, "m2", "q2")

    with pytest.raises(ValueError, match="reason"):
        MasterQuestionMaintenanceService(repo).merge(
            "m1",
            "m2",
            reason=" ",
        )
