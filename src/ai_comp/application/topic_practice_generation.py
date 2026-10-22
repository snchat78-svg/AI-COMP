from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from typing import Callable, Sequence

from ai_comp.domain.material_analysis import ImportantFact, ProposedConcept
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedQuestionStatus,
    GenerationSpecification,
    QuestionSourceKind,
)
from ai_comp.domain.topic_question_bank import QuestionBankTopic, TopicOneLinerQA
from ai_comp.material.generation import (
    GenerationQualityPolicy,
    GeneratedQuestionService,
)
from ai_comp.matching.normalization import normalize_question_text


@dataclass(frozen=True)
class TopicPracticeGenerationResult:
    requested_count: int
    accepted_count: int
    one_liner_source_count: int
    previous_paper_source_count: int
    warnings: tuple[str, ...] = ()


class TopicPracticeAlternativeGenerator:
    """Generate new four-option practice MCQs from reviewed source Q&A and verified history.

    Actual exam appearances are only used as source facts; this service stores its
    outputs in generated-question storage and never adds a new exam appearance.
    The supplied provider/verifier are expected to use a configured model provider.
    """

    def __init__(
        self,
        *,
        provider,
        verifier,
        persist_question: Callable[[GeneratedMCQ], None],
        max_source_facts: int = 300,
    ) -> None:
        if not 1 <= max_source_facts <= 1000:
            raise ValueError("max_source_facts must be between 1 and 1000")
        self._provider = provider
        self._verifier = verifier
        self._persist_question = persist_question
        self._max_source_facts = max_source_facts

    def generate(
        self,
        *,
        subject_id: str,
        requested_count: int,
        topics: Sequence[QuestionBankTopic],
        one_liners: Sequence[TopicOneLinerQA],
        previous_questions: Sequence[GeneratedMCQ],
        existing_generated_questions: Sequence[GeneratedMCQ] = (),
    ) -> TopicPracticeGenerationResult:
        if not subject_id.strip() or subject_id != subject_id.strip():
            raise ValueError("subject_id must be a non-empty trimmed string")
        if isinstance(requested_count, bool) or not isinstance(requested_count, int) or not 1 <= requested_count <= 500:
            raise ValueError("requested_count must be between 1 and 500")

        topic_by_id = {topic.concept_id: topic for topic in topics}
        if not topic_by_id:
            return TopicPracticeGenerationResult(
                requested_count, 0, 0, 0,
                ("No canonical topics exist for the selected subject.",),
            )

        # All source facts are explicit Q&A or official-answer-key-verified history.
        # Unreviewed one-liners never enter the generated-question prompt.
        one_liner_sources = [
            item for item in one_liners
            if item.verification_status.value == "VERIFIED"
            and item.importance_score >= 0.5
            and item.concept_id in topic_by_id
        ]
        history_sources = [
            item for item in previous_questions
            if item.source_kind is QuestionSourceKind.VERIFIED_EXAM_HISTORY
            and item.answer_verification is AnswerVerificationStatus.VERIFIED
            and item.status is GeneratedQuestionStatus.ACCEPTED
            and item.concept_ids
            and set(item.concept_ids).intersection(topic_by_id)
        ]

        material_id = f"topic-bank:{uuid.uuid4().hex}"
        facts: list[ImportantFact] = []
        concept_evidence: dict[str, str] = {}

        for item in one_liner_sources:
            source_url = item.source_url or ""
            fact_text = (
                f"Topic one-liner question: {item.question_text}\n"
                f"Verified direct answer: {item.answer_text}\n"
                f"Source URL: {source_url}"
            )
            facts.append(
                ImportantFact(
                    fact_id=f"one-liner:{item.one_liner_id}",
                    material_id=material_id,
                    fact_text=fact_text,
                    evidence_text=item.source_evidence,
                    importance_score=item.importance_score,
                    confidence=1.0,
                    fact_type="VERIFIED_ONE_LINER_QA",
                )
            )
            concept_evidence.setdefault(item.concept_id, item.source_evidence)

        for item in history_sources:
            option_map = {option.key.strip().upper(): option.text for option in item.options}
            answer_text = option_map.get(item.correct_option_key.strip().upper())
            if not answer_text:
                continue
            fact_id = f"verified-history:{item.generated_question_id}"
            provenance = " | ".join(item.answer_verification_evidence)
            facts.append(
                ImportantFact(
                    fact_id=fact_id,
                    material_id=material_id,
                    fact_text=(
                        f"Verified previous-exam question: {item.stem}\n"
                        f"Official-answer-key-verified answer: {answer_text}\n"
                        f"Exam: {item.exam_name or item.exam_id or 'Verified exam history'} "
                        f"{item.exam_year or ''}"
                    ),
                    evidence_text=provenance,
                    importance_score=max(0.5, min(1.0, item.importance_score)),
                    confidence=1.0,
                    fact_type="VERIFIED_PREVIOUS_EXAM_ANSWER",
                )
            )
            for concept_id in set(item.concept_ids).intersection(topic_by_id):
                concept_evidence.setdefault(concept_id, provenance)

        facts = facts[: self._max_source_facts]
        if not facts:
            return TopicPracticeGenerationResult(
                requested_count, 0, len(one_liner_sources), len(history_sources),
                ("No verified, source-backed Q&A or previous-paper answers are available for this subject.",),
            )

        concepts = tuple(
            ProposedConcept(
                concept_candidate_id=concept_id,
                material_id=material_id,
                label=topic.label,
                subject=topic.subject,
                topic=topic.topic,
                subtopic=topic.subtopic,
                evidence_text=concept_evidence.get(concept_id, topic.label),
                confidence=1.0,
            )
            for concept_id, topic in sorted(topic_by_id.items())
        )
        allowed_concept_ids = set(topic_by_id)
        allowed_fact_ids = {fact.fact_id for fact in facts}

        # Do not recycle source exam stems or existing generated stems as "alternatives".
        seen_stems = {
            normalize_question_text(item.stem)
            for item in (*previous_questions, *existing_generated_questions)
            if normalize_question_text(item.stem)
        }
        accepted_count = 0
        warnings: list[str] = []
        rounds = min(6, max(1, math.ceil(requested_count / 100) + 1))

        for _ in range(rounds):
            remaining = requested_count - accepted_count
            if remaining <= 0:
                break
            batch_count = min(100, remaining)
            specification = GenerationSpecification(
                generation_id=f"topic-generation:{uuid.uuid4().hex}",
                material_id=material_id,
                fact_ids=tuple(fact.fact_id for fact in facts),
                concept_ids=tuple(topic_by_id),
                requested_count=batch_count,
                difficulty="MEDIUM",
                language="hi",
            )
            service = GeneratedQuestionService(
                self._provider,
                self._verifier,
                repository=None,
                policy=GenerationQualityPolicy(
                    min_fact_confidence=0.80,
                    min_fact_importance=0.50,
                    min_answer_confidence=0.90,
                    min_quality_score=0.80,
                    reject_if_duplicate=False,
                ),
            )
            result = service.generate(
                specification,
                facts=facts,
                concepts=concepts,
            )
            warnings.extend(result.warnings)
            new_in_batch = 0
            for question in result.questions:
                key = normalize_question_text(question.stem)
                if not key or key in seen_stems:
                    continue
                if not question.fact_ids or not set(question.fact_ids).issubset(allowed_fact_ids):
                    warnings.append("Skipped a generated question with unknown source-fact references.")
                    continue
                if not question.concept_ids or not set(question.concept_ids).issubset(allowed_concept_ids):
                    warnings.append("Skipped a generated question that was not mapped to this subject's concepts.")
                    continue
                if question.source_kind is not QuestionSourceKind.AI_GENERATED:
                    warnings.append("Skipped an item that was incorrectly labelled as historical.")
                    continue
                if (
                    question.answer_verification is not AnswerVerificationStatus.VERIFIED
                    or question.status is not GeneratedQuestionStatus.ACCEPTED
                    or len(question.options) != 4
                ):
                    warnings.append("Skipped a generated MCQ that failed answer or four-option checks.")
                    continue
                self._persist_question(question)
                seen_stems.add(key)
                accepted_count += 1
                new_in_batch += 1
                if accepted_count >= requested_count:
                    break
            if new_in_batch == 0:
                # Repeated or low-confidence generations should not trigger an
                # unbounded model-call loop when this subject's evidence is thin.
                break

        return TopicPracticeGenerationResult(
            requested_count=requested_count,
            accepted_count=accepted_count,
            one_liner_source_count=len(one_liner_sources),
            previous_paper_source_count=len(history_sources),
            warnings=tuple(warnings[:50]),
        )


__all__ = ["TopicPracticeAlternativeGenerator", "TopicPracticeGenerationResult"]
