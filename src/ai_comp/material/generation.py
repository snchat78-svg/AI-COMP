from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol, Sequence

from ai_comp.domain.material_analysis import ImportantFact, ProposedConcept
from ai_comp.domain.material_matching import MaterialMatchingResult
from ai_comp.domain.material_generation import (
    AnswerVerificationResult,
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
    GenerationResult,
    GenerationSpecification,
)
from ai_comp.matching.normalization import normalize_question_text


class QuestionGenerationProvider(Protocol):
    def generate(
        self,
        specification: GenerationSpecification,
        facts: Sequence[ImportantFact],
        concepts: Sequence[ProposedConcept],
    ) -> Sequence[GeneratedMCQ]: ...


class AnswerVerifier(Protocol):
    def verify(
        self,
        question: GeneratedMCQ,
        facts: Sequence[ImportantFact],
        concepts: Sequence[ProposedConcept],
    ) -> AnswerVerificationResult: ...


class GeneratedQuestionRepository(Protocol):
    def save(self, question: GeneratedMCQ) -> None: ...


@dataclass(frozen=True)
class GenerationQualityPolicy:
    min_fact_confidence: float = 0.80
    min_fact_importance: float = 0.50
    min_answer_confidence: float = 0.90
    min_quality_score: float = 0.80
    reject_if_duplicate: bool = True

    def __post_init__(self) -> None:
        for name in (
            "min_fact_confidence",
            "min_fact_importance",
            "min_answer_confidence",
            "min_quality_score",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


class GenerationQualityController:
    """Fail-closed quality gate for generated MCQs."""

    def __init__(self, policy: GenerationQualityPolicy | None = None) -> None:
        self.policy = policy or GenerationQualityPolicy()

    def validate(
        self,
        question: GeneratedMCQ,
        *,
        answer: AnswerVerificationResult,
        duplicate_master_id: str | None,
        source_facts: Sequence[ImportantFact],
    ) -> tuple[GeneratedMCQ, tuple[str, ...]]:
        reasons: list[str] = []
        facts_by_id = {fact.fact_id: fact for fact in source_facts}

        if any(fact_id not in facts_by_id for fact_id in question.fact_ids):
            reasons.append("question references an unknown source fact")

        if not question.fact_ids and not question.concept_ids:
            reasons.append("question has no source grounding")

        for fact_id in question.fact_ids:
            fact = facts_by_id.get(fact_id)
            if fact is None:
                continue
            if fact.confidence < self.policy.min_fact_confidence:
                reasons.append("source fact confidence is below generation threshold")
            if fact.importance_score < self.policy.min_fact_importance:
                reasons.append("source fact importance is below generation threshold")

        if answer.status is not AnswerVerificationStatus.VERIFIED:
            reasons.append(f"answer verification status is {answer.status.value}")
        if answer.confidence < self.policy.min_answer_confidence:
            reasons.append("answer verification confidence is below threshold")

        if answer.status is AnswerVerificationStatus.VERIFIED:
            allowed_evidence = {
                item
                for fact in source_facts
                for item in (fact.fact_text, fact.evidence_text)
            }
            if any(item not in allowed_evidence for item in answer.evidence):
                reasons.append("answer verification evidence is not grounded in source facts")

        if [option.key.strip().upper() for option in question.options] != ["A", "B", "C", "D"]:
            reasons.append("generated MCQ options must use A, B, C, D")

        if duplicate_master_id and self.policy.reject_if_duplicate:
            reasons.append("generated question duplicates an existing master question")

        if question.quality_score < self.policy.min_quality_score:
            reasons.append("quality score is below threshold")

        status = (
            GeneratedQuestionStatus.ACCEPTED
            if not reasons
            else GeneratedQuestionStatus.REJECTED
        )
        updated = GeneratedMCQ(
            **{
                **question.__dict__,
                "answer_verification": answer.status,
                "answer_verification_evidence": answer.evidence,
                "status": status,
                "duplicate_of_master_question_id": duplicate_master_id,
            }
        )
        return updated, tuple(reasons)


class GeneratedQuestionService:
    def __init__(
        self,
        provider: QuestionGenerationProvider,
        verifier: AnswerVerifier,
        *,
        repository: GeneratedQuestionRepository | None = None,
        duplicate_finder=None,
        policy: GenerationQualityPolicy | None = None,
    ) -> None:
        self.provider = provider
        self.verifier = verifier
        self.repository = repository
        self.duplicate_finder = duplicate_finder
        self.quality = GenerationQualityController(policy)

    def build_specification(
        self,
        *,
        material_id: str,
        facts: Sequence[ImportantFact],
        concepts: Sequence[ProposedConcept],
        matching: MaterialMatchingResult,
        requested_count: int = 1,
        difficulty: str = "MEDIUM",
        language: str = "hi",
    ) -> GenerationSpecification:
        return GenerationSpecification(
            generation_id=self._generation_id(
                material_id,
                tuple(fact.fact_id for fact in facts),
                tuple(concept.concept_candidate_id for concept in concepts),
            ),
            material_id=material_id,
            fact_ids=tuple(fact.fact_id for fact in facts),
            concept_ids=tuple(
                concept.concept_candidate_id for concept in concepts
            ),
            existing_master_question_ids=tuple(
                sorted(
                    {
                        match.master_question_id
                        for match in matching.existing_question_matches
                    }
                )
            ),
            requested_count=requested_count,
            difficulty=difficulty,
            language=language,
        )

    def generate(
        self,
        specification: GenerationSpecification,
        *,
        facts: Sequence[ImportantFact],
        concepts: Sequence[ProposedConcept],
    ) -> GenerationResult:
        if any(fact.material_id != specification.material_id for fact in facts):
            raise ValueError("all facts must belong to the specification material")
        if any(concept.material_id != specification.material_id for concept in concepts):
            raise ValueError("all concepts must belong to the specification material")

        generated = tuple(
            self.provider.generate(specification, facts, concepts)
        )
        accepted: list[GeneratedMCQ] = []
        rejected: list[str] = []
        warnings: list[str] = []

        for question in generated:
            if question.generation_id != specification.generation_id:
                raise ValueError("generated question has wrong generation_id")
            if question.material_id != specification.material_id:
                raise ValueError("generated question has wrong material_id")

            answer = self.verifier.verify(question, facts, concepts)
            duplicate = (
                self.duplicate_finder(question)
                if self.duplicate_finder is not None
                else None
            )
            updated, reasons = self.quality.validate(
                question,
                answer=answer,
                duplicate_master_id=duplicate,
                source_facts=facts,
            )
            if updated.status is GeneratedQuestionStatus.ACCEPTED:
                accepted.append(updated)
                if self.repository is not None:
                    self.repository.save(updated)
            else:
                rejected.append(updated.generated_question_id)
                warnings.extend(
                    f"{updated.generated_question_id}: {reason}"
                    for reason in reasons
                )
                if self.repository is not None:
                    self.repository.save(updated)

        if len(accepted) > specification.requested_count:
            accepted = accepted[: specification.requested_count]
        return GenerationResult(
            specification=specification,
            questions=tuple(accepted),
            rejected_question_ids=tuple(rejected),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _generation_id(
        material_id: str,
        fact_ids: tuple[str, ...],
        concept_ids: tuple[str, ...],
    ) -> str:
        payload = "|".join(
            [material_id, *sorted(fact_ids), *sorted(concept_ids)]
        )
        return "generation:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


class StaticQuestionGenerationProvider:
    """Deterministic provider for tests; never claims historical provenance."""

    def __init__(self, questions: Sequence[GeneratedMCQ]) -> None:
        self.questions = tuple(questions)

    def generate(self, specification, facts, concepts):
        return self.questions


class MasterQuestionDuplicateFinder:
    """Deterministic duplicate finder; semantic matching is optional and fail-closed."""

    def __init__(self, master_repository, *, embedding=None, threshold: float = 0.97, margin: float = 0.05):
        self.master_repository = master_repository
        self.embedding = embedding
        self.threshold = threshold
        self.margin = margin
        if not 0.0 < threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        if not 0.0 <= margin <= 1.0:
            raise ValueError("margin must be between 0 and 1")

    def __call__(self, question: GeneratedMCQ) -> str | None:
        from ai_comp.domain.master_questions import MasterQuestionStatus
        masters = self.master_repository.list_masters(
            status=MasterQuestionStatus.ACTIVE,
            limit=1000,
        )
        key = normalize_question_text(question.stem)
        exact = sorted(
            master.master_question_id
            for master in masters
            if normalize_question_text(master.stem) == key
        )
        if exact:
            return exact[0]

        if self.embedding is None:
            return None

        scored = sorted(
            (
                (self._cosine(self.embedding(question.stem), self.embedding(master.stem)), master)
                for master in masters
            ),
            key=lambda item: (-item[0], item[1].master_question_id),
        )
        eligible = [item for item in scored if item[0] >= self.threshold]
        if not eligible:
            return None
        best_score, best = eligible[0]
        second_score = eligible[1][0] if len(eligible) > 1 else 0.0
        if len(eligible) > 1 and best_score - second_score < self.margin:
            return None
        return best.master_question_id

    @staticmethod
    def _cosine(a, b) -> float:
        if not a or not b or len(a) != len(b):
            raise ValueError("embedding vectors must be non-empty and same length")
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)


class FactGroundedAnswerVerifier:
    """Conservative local verifier: accepted answers must have explicit fact evidence."""

    def verify(self, question, facts, concepts):
        facts_by_id = {fact.fact_id: fact for fact in facts}
        answer_text = next(
            option.text
            for option in question.options
            if option.key.strip().upper() == question.correct_option_key.strip().upper()
        )
        evidence = []
        for fact_id in question.fact_ids:
            fact = facts_by_id.get(fact_id)
            if fact is None:
                continue
            if answer_text.casefold() in fact.fact_text.casefold() or answer_text.casefold() in fact.evidence_text.casefold():
                evidence.append(fact.evidence_text)
        if evidence:
            return AnswerVerificationResult(
                status=AnswerVerificationStatus.VERIFIED,
                evidence=tuple(evidence),
                confidence=0.98,
            )
        return AnswerVerificationResult(
            status=AnswerVerificationStatus.UNCERTAIN,
            confidence=0.0,
        )
