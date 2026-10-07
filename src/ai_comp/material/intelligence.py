from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from ai_comp.domain.material_generation import GeneratedMCQ
from ai_comp.domain.question_intelligence import (
    DifficultyLevel,
    QuestionIntelligenceInput,
    QuestionIntelligencePolicy,
    QuestionIntelligenceScore,
    RankedQuestionCandidate,
)


class QuestionIntelligenceService:
    """Scores accepted generated questions without creating historical claims."""

    def __init__(self, policy: QuestionIntelligencePolicy | None = None) -> None:
        self.policy = policy or QuestionIntelligencePolicy()

    def score(self, question: GeneratedMCQ, evidence: QuestionIntelligenceInput) -> QuestionIntelligenceScore:
        if question.status.value != "ACCEPTED":
            raise ValueError("only accepted generated questions can enter intelligence scoring")
        if evidence.generated_question_id != question.generated_question_id:
            raise ValueError("intelligence evidence does not match question")

        difficulty_score = self._difficulty_score(evidence)
        difficulty = self._difficulty_level(difficulty_score, evidence.requested_difficulty)
        importance = self._importance_score(evidence)
        selection = (
            self.policy.selection_importance_weight * importance
            + self.policy.selection_novelty_weight * evidence.novelty_score
            + self.policy.selection_coverage_weight * evidence.coverage_score
        )
        return QuestionIntelligenceScore(
            generated_question_id=question.generated_question_id,
            difficulty=difficulty,
            difficulty_score=difficulty_score,
            importance_score=importance,
            novelty_score=evidence.novelty_score,
            coverage_score=evidence.coverage_score,
            selection_score=max(0.0, min(1.0, selection)),
        )

    def rank(
        self,
        questions: Sequence[GeneratedMCQ],
        evidence_by_question: Mapping[str, QuestionIntelligenceInput],
        *,
        limit: int | None = None,
    ) -> tuple[RankedQuestionCandidate, ...]:
        scored = [
            self.score(question, evidence_by_question[question.generated_question_id])
            for question in questions
        ]
        scored.sort(
            key=lambda item: (-item.selection_score, -item.importance_score, item.generated_question_id)
        )
        if limit is not None:
            if limit < 1:
                raise ValueError("limit must be positive")
            scored = scored[:limit]
        return tuple(
            RankedQuestionCandidate(
                question_id=item.generated_question_id,
                score=item,
                rank=index,
            )
            for index, item in enumerate(scored, start=1)
        )

    def _importance_score(self, evidence: QuestionIntelligenceInput) -> float:
        avg_importance = self._average(evidence.fact_importance_scores)
        avg_fact_confidence = self._average(evidence.fact_confidences)
        avg_concept_confidence = self._average(evidence.concept_confidences)
        # Frequency is capped: ten appearances are strong evidence, but not
        # an unlimited importance multiplier.
        frequency = min(evidence.verified_appearance_count, 10) / 10.0
        return max(
            0.0,
            min(
                1.0,
                self.policy.fact_importance_weight * avg_importance
                + self.policy.historical_frequency_weight * frequency
                + self.policy.fact_confidence_weight * avg_fact_confidence
                + self.policy.concept_confidence_weight * avg_concept_confidence,
            ),
        )

    @staticmethod
    def _difficulty_score(evidence: QuestionIntelligenceInput) -> float:
        if evidence.difficulty_signal is not None:
            return evidence.difficulty_signal
        return {
            DifficultyLevel.EASY: 0.25,
            DifficultyLevel.MEDIUM: 0.55,
            DifficultyLevel.HARD: 0.80,
        }[evidence.requested_difficulty]

    @staticmethod
    def _difficulty_level(score: float, requested: DifficultyLevel) -> DifficultyLevel:
        # Preserve an explicit provider signal when present, otherwise use
        # conservative bands around the requested difficulty.
        if score < 0.40:
            return DifficultyLevel.EASY
        if score < 0.70:
            return DifficultyLevel.MEDIUM
        return DifficultyLevel.HARD

    @staticmethod
    def _average(values: Iterable[float]) -> float:
        values = tuple(values)
        return sum(values) / len(values) if values else 0.0
