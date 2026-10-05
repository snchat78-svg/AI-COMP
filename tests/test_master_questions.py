import pytest
from ai_comp.domain.master_questions import (
    MasterAssignmentStatus,
    MasterMembershipType,
    MasterQuestion,
    MasterQuestionMembership,
)
from ai_comp.domain.matching import MatchType, QuestionMatch
from ai_comp.domain.questions import QuestionCandidate, QuestionKind, QuestionOption
from ai_comp.master.policy import MasterAssignmentPolicy
from ai_comp.master.repository import InMemoryMasterQuestionRepository
from ai_comp.master.service import MasterQuestionService


def question(question_id: str, stem: str) -> QuestionCandidate:
    return QuestionCandidate(
        question_id=question_id,
        document_id=f"doc-{question_id}",
        document_sha256="a" * 64,
        question_number=1,
        stem=stem,
        options=(QuestionOption("A", "एक"), QuestionOption("B", "दो")),
        kind=QuestionKind.MCQ,
        raw_text=stem,
        start_line=1,
        end_line=3,
    )


def seed_master(repo, master_id, question_id):
    q = question(question_id, f"question {question_id}")
    repo.save_master(
        MasterQuestion(
            master_question_id=master_id,
            canonical_question_id=q.question_id,
            stem=q.stem,
            options=q.options,
            kind=q.kind,
        )
    )
    repo.save_membership(
        MasterQuestionMembership(
            master_question_id=master_id,
            question_id=question_id,
            relationship=MasterMembershipType.CANONICAL,
            confidence=1.0,
        )
    )


def test_new_question_without_equivalent_match_creates_master():
    repo = InMemoryMasterQuestionRepository()
    q = question("q1", "भारत की राजधानी क्या है?")

    result = MasterQuestionService(repo).assign(q)

    assert result.status is MasterAssignmentStatus.CREATED
    assert result.master_question_id == "master:q1"
    assert result.relationship is MasterMembershipType.CANONICAL
    assert repo.get_master_for_question("q1").master_question_id == "master:q1"


def test_exact_match_assigns_existing_master():
    repo = InMemoryMasterQuestionRepository()
    seed_master(repo, "m1", "q1")
    result = MasterQuestionService(repo).assign(
        question("q2", "same"),
        (QuestionMatch("q2", "q1", MatchType.EXACT, 1.0),),
    )

    assert result.status is MasterAssignmentStatus.ASSIGNED
    assert result.master_question_id == "m1"
    assert result.relationship is MasterMembershipType.EXACT


def test_same_concept_does_not_merge_master():
    repo = InMemoryMasterQuestionRepository()
    seed_master(repo, "m1", "q1")
    result = MasterQuestionService(repo).assign(
        question("q2", "same concept"),
        (QuestionMatch("q2", "q1", MatchType.SAME_CONCEPT, 0.99),),
    )

    assert result.status is MasterAssignmentStatus.CREATED
    assert result.master_question_id == "master:q2"


def test_rephrased_requires_threshold_and_margin():
    repo = InMemoryMasterQuestionRepository()
    seed_master(repo, "m1", "q1")
    seed_master(repo, "m2", "q3")

    q = question("q2", "rephrased")
    matches = (
        QuestionMatch("q2", "q1", MatchType.REPHRASED, 0.94),
        QuestionMatch("q2", "q3", MatchType.REPHRASED, 0.93),
    )
    result = MasterQuestionService(
        repo,
        MasterAssignmentPolicy(
            min_rephrased_confidence=0.90,
            min_confidence_margin=0.05,
        ),
    ).assign(q, matches)

    assert result.status is MasterAssignmentStatus.AMBIGUOUS
    assert result.competing_master_ids == ("m1", "m2")


def test_rephrased_with_safe_margin_assigns():
    repo = InMemoryMasterQuestionRepository()
    seed_master(repo, "m1", "q1")

    result = MasterQuestionService(repo).assign(
        question("q2", "rephrased"),
        (QuestionMatch("q2", "q1", MatchType.REPHRASED, 0.96),),
    )

    assert result.status is MasterAssignmentStatus.ASSIGNED
    assert result.relationship is MasterMembershipType.REPHRASED


def test_already_assigned_is_idempotent():
    repo = InMemoryMasterQuestionRepository()
    seed_master(repo, "m1", "q1")

    result = MasterQuestionService(repo).assign(question("q1", "same"))

    assert result.status is MasterAssignmentStatus.ALREADY_ASSIGNED
    assert result.master_question_id == "m1"


def test_low_confidence_rephrased_match_creates_new_master():
    repo = InMemoryMasterQuestionRepository()
    seed_master(repo, "m1", "q1")

    result = MasterQuestionService(repo).assign(
        question("q2", "uncertain"),
        (QuestionMatch("q2", "q1", MatchType.REPHRASED, 0.89),),
    )

    assert result.status is MasterAssignmentStatus.CREATED
    assert result.master_question_id == "master:q2"


def test_two_exact_matches_from_different_masters_are_ambiguous():
    repo = InMemoryMasterQuestionRepository()
    seed_master(repo, "m1", "q1")
    seed_master(repo, "m2", "q3")

    result = MasterQuestionService(repo).assign(
        question("q2", "duplicate"),
        (
            QuestionMatch("q2", "q1", MatchType.EXACT, 1.0),
            QuestionMatch("q2", "q3", MatchType.EXACT, 1.0),
        ),
    )

    assert result.status is MasterAssignmentStatus.AMBIGUOUS
    assert result.competing_master_ids == ("m1", "m2")


def test_related_topic_never_assigns_existing_master():
    repo = InMemoryMasterQuestionRepository()
    seed_master(repo, "m1", "q1")

    result = MasterQuestionService(repo).assign(
        question("q2", "related"),
        (QuestionMatch("q2", "q1", MatchType.RELATED_TOPIC, 0.99),),
    )

    assert result.status is MasterAssignmentStatus.CREATED
    assert result.master_question_id == "master:q2"


def test_inmemory_repository_prevents_two_canonical_questions_for_one_master_identity():
    repo = InMemoryMasterQuestionRepository()
    seed_master(repo, "m1", "q1")

    q = question("q2", "other")
    from ai_comp.domain.master_questions import MasterQuestion

    with pytest.raises(ValueError, match="canonical question is already owned"):
        repo.save_master(
            MasterQuestion(
                master_question_id="m2",
                canonical_question_id="q1",
                stem=q.stem,
                options=q.options,
                kind=q.kind,
            )
        )
