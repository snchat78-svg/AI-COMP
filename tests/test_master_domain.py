import pytest

from ai_comp.domain.master_questions import (
    MasterMembershipType,
    MasterQuestion,
    MasterQuestionStatus,
)
from ai_comp.domain.questions import QuestionKind, QuestionOption


def master(**overrides):
    values = dict(
        master_question_id="m1",
        canonical_question_id="q1",
        stem="Question",
        options=(QuestionOption("A", "One"),),
        kind=QuestionKind.MCQ,
    )
    values.update(overrides)
    return MasterQuestion(**values)


def test_merged_master_requires_target():
    with pytest.raises(ValueError, match="merged_into_master_id"):
        master(status=MasterQuestionStatus.MERGED)


def test_active_master_cannot_reference_merge_target():
    with pytest.raises(ValueError, match="only merged"):
        master(
            status=MasterQuestionStatus.ACTIVE,
            merged_into_master_id="m2",
        )


def test_membership_relationship_is_equivalence_only():
    assert tuple(item.value for item in MasterMembershipType) == (
        "CANONICAL",
        "EXACT",
        "REPHRASED",
    )
