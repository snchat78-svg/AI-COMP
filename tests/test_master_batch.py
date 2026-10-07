from ai_comp.domain.matching import MatchType, QuestionMatch
from ai_comp.domain.questions import QuestionCandidate, QuestionKind, QuestionOption
from ai_comp.master.batch import MasterQuestionBatchService
from ai_comp.master.repository import InMemoryMasterQuestionRepository


def question(question_id: str, number: int) -> QuestionCandidate:
    return QuestionCandidate(
        question_id=question_id,
        document_id="doc",
        document_sha256="a" * 64,
        question_number=number,
        stem=f"Question {question_id}",
        options=(QuestionOption("A", "एक"), QuestionOption("B", "दो")),
        kind=QuestionKind.MCQ,
        raw_text=f"Question {question_id}",
        start_line=number,
        end_line=number + 2,
    )


def test_exact_component_is_grouped_without_input_order_dependency():
    repo = InMemoryMasterQuestionRepository()
    service = MasterQuestionBatchService(repo)

    result = service.assign_many(
        (question("q3", 3), question("q1", 1), question("q2", 2)),
        (
            QuestionMatch("q1", "q3", MatchType.EXACT, 1.0),
            QuestionMatch("q2", "q3", MatchType.EXACT, 1.0),
        ),
    )

    assert [item.master_question_id for item in result] == [
        "master:q1",
        "master:q1",
        "master:q1",
    ]
    assert result[0].status.value == "CREATED"
    assert result[1].relationship.value == "EXACT"


def test_same_concept_is_not_used_for_batch_master_grouping():
    repo = InMemoryMasterQuestionRepository()
    service = MasterQuestionBatchService(repo)

    result = service.assign_many(
        (question("q1", 1), question("q2", 2)),
        (QuestionMatch("q1", "q2", MatchType.SAME_CONCEPT, 0.99),),
    )

    assert result[0].master_question_id != result[1].master_question_id


def test_rephrased_batch_assignment_uses_selected_existing_master():
    from ai_comp.domain.master_questions import MasterQuestion, MasterQuestionMembership, MasterMembershipType
    from ai_comp.master.repository import InMemoryMasterQuestionRepository

    repo = InMemoryMasterQuestionRepository()
    base = question("existing", 1)
    repo.save_master(
        MasterQuestion(
            master_question_id="m1",
            canonical_question_id="existing",
            stem=base.stem,
            options=base.options,
            kind=base.kind,
        )
    )
    repo.save_membership(
        MasterQuestionMembership(
            master_question_id="m1",
            question_id="existing",
            relationship=MasterMembershipType.CANONICAL,
            confidence=1.0,
        )
    )

    result = MasterQuestionBatchService(repo).assign_many(
        (question("q1", 2),),
        (QuestionMatch("q1", "existing", MatchType.REPHRASED, 0.96),),
    )[0]

    assert result.master_question_id == "m1"
    assert result.relationship is MasterMembershipType.REPHRASED
    assert repo.get_membership_for_question("q1").master_question_id == "m1"


def test_batch_preserves_preassigned_question_status():
    from ai_comp.domain.master_questions import MasterMembershipType, MasterQuestion, MasterQuestionMembership

    repo = InMemoryMasterQuestionRepository()
    q1 = question("q1", 1)
    repo.save_master(
        MasterQuestion(
            master_question_id="m1",
            canonical_question_id="q1",
            stem=q1.stem,
            options=q1.options,
            kind=q1.kind,
        )
    )
    repo.save_membership(
        MasterQuestionMembership(
            master_question_id="m1",
            question_id="q1",
            relationship=MasterMembershipType.CANONICAL,
            confidence=1.0,
        )
    )

    result = MasterQuestionBatchService(repo).assign_many(
        (q1,),
    )[0]

    assert result.status.value == "ALREADY_ASSIGNED"
    assert result.master_question_id == "m1"
