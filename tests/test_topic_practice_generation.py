from __future__ import annotations

from datetime import datetime, timezone

from ai_comp.application.topic_practice_generation import TopicPracticeAlternativeGenerator
from ai_comp.domain.material_generation import (
    AnswerVerificationResult,
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
    QuestionSourceKind,
)
from ai_comp.domain.topic_question_bank import (
    OneLinerVerificationStatus,
    QuestionBankTopic,
    TopicOneLinerQA,
)


class _VerifiedProvider:
    def __init__(self, stems: list[str]) -> None:
        self.stems = stems

    def generate(self, specification, facts, concepts):
        result = []
        for index in range(specification.requested_count):
            stem = self.stems[index % len(self.stems)]
            result.append(
                GeneratedMCQ(
                    generated_question_id=f"generated-test-{index}-{specification.generation_id}",
                    generation_id=specification.generation_id,
                    material_id=specification.material_id,
                    stem=stem,
                    options=(
                        GeneratedOption("A", "Correct answer"),
                        GeneratedOption("B", "Distractor two"),
                        GeneratedOption("C", "Distractor three"),
                        GeneratedOption("D", "Distractor four"),
                    ),
                    correct_option_key="A",
                    explanation="The correct answer is supported by the supplied source fact.",
                    fact_ids=(facts[0].fact_id,),
                    concept_ids=(concepts[0].concept_candidate_id,),
                    difficulty="MEDIUM",
                    importance_score=0.9,
                    quality_score=0.95,
                )
            )
        return tuple(result)


class _EvidenceVerifier:
    def verify(self, question, facts, concepts):
        matching = next(item for item in facts if item.fact_id in question.fact_ids)
        return AnswerVerificationResult(
            status=AnswerVerificationStatus.VERIFIED,
            evidence=(matching.fact_text,),
            confidence=0.99,
        )


def _topic() -> QuestionBankTopic:
    return QuestionBankTopic(
        concept_id="concept-rivers",
        label="Rivers",
        subject="Rajasthan Geography",
        topic="Rivers",
        subtopic="Luni",
        verified_one_liner_count=1,
    )


def _one_liner() -> TopicOneLinerQA:
    now = datetime(2026, 10, 22, tzinfo=timezone.utc)
    return TopicOneLinerQA(
        one_liner_id="ol-luni-1",
        concept_id="concept-rivers",
        question_text="Which river is associated with the Luni river system?",
        answer_text="Luni River",
        language_code="en",
        source_url="https://example.gov.in/rajasthan-rivers",
        source_evidence="Official geography reference: Luni River.",
        verification_status=OneLinerVerificationStatus.VERIFIED,
        importance_score=0.9,
        reviewed_at=now,
        created_at=now,
        updated_at=now,
    )


def _historical(stem: str = "Which river question appeared in the past paper?") -> GeneratedMCQ:
    return GeneratedMCQ(
        generated_question_id="verified-history:historical-q1",
        generation_id="verified-exam-history",
        material_id="verified-paper:historical-q1",
        stem=stem,
        options=(
            GeneratedOption("A", "Luni River"),
            GeneratedOption("B", "River B"),
            GeneratedOption("C", "River C"),
            GeneratedOption("D", "River D"),
        ),
        correct_option_key="A",
        explanation="The answer matches the linked official answer key.",
        fact_ids=(),
        concept_ids=("concept-rivers",),
        difficulty="MEDIUM",
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("Official answer key: https://example.gov.in/answer-key",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=1.0,
        source_kind=QuestionSourceKind.VERIFIED_EXAM_HISTORY,
        source_url="https://example.gov.in/paper",
        answer_key_source_url="https://example.gov.in/answer-key",
        exam_name="Example Exam",
        exam_id="example-exam",
        exam_year=2025,
        exam_question_number=12,
        verified_appearance_count=1,
    )


def test_alternative_mcqs_are_answer_verified_and_persisted_as_generated() -> None:
    saved = []
    generator = TopicPracticeAlternativeGenerator(
        provider=_VerifiedProvider(["A new practice question with four options?"]),
        verifier=_EvidenceVerifier(),
        persist_question=saved.append,
    )

    result = generator.generate(
        subject_id="Rajasthan Geography",
        requested_count=1,
        topics=(_topic(),),
        one_liners=(_one_liner(),),
        previous_questions=(_historical(),),
    )

    assert result.accepted_count == 1
    assert result.one_liner_source_count == 1
    assert result.previous_paper_source_count == 1
    assert len(saved) == 1
    assert saved[0].status is GeneratedQuestionStatus.ACCEPTED
    assert saved[0].answer_verification is AnswerVerificationStatus.VERIFIED
    assert len(saved[0].options) == 4
    assert saved[0].source_kind is QuestionSourceKind.AI_GENERATED
    assert saved[0].fact_ids == ("one-liner:ol-luni-1",)


def test_previous_exam_stem_is_not_reused_as_an_alternative() -> None:
    original_stem = "Which river question appeared in the past paper?"
    saved = []
    generator = TopicPracticeAlternativeGenerator(
        provider=_VerifiedProvider([original_stem]),
        verifier=_EvidenceVerifier(),
        persist_question=saved.append,
    )

    result = generator.generate(
        subject_id="Rajasthan Geography",
        requested_count=1,
        topics=(_topic(),),
        one_liners=(_one_liner(),),
        previous_questions=(_historical(original_stem),),
    )

    assert result.accepted_count == 0
    assert saved == []
