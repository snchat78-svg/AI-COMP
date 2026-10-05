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
