from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai_comp.domain.material_generation import GeneratedMCQ, GeneratedQuestionStatus
from ai_comp.domain.learning_recommendation import (
    LearningRecommendation,
    LearningRecommendationPolicy,
    NextTestPlan,
    RecommendedDifficulty,
)
from ai_comp.domain.question_intelligence import RankedQuestionCandidate
from ai_comp.domain.test_analysis import TestAnalysis


class LearningRecommendationService:
    """Turns post-test weak-topic analytics into deterministic study recommendations."""

    def __init__(self, policy: LearningRecommendationPolicy | None = None) -> None:
        self.policy = policy or LearningRecommendationPolicy()

    def recommend(self, analysis: TestAnalysis) -> tuple[LearningRecommendation, ...]:
        recommendations = []
        for weak_topic in analysis.weak_topics[: self.policy.max_recommendations]:
            difficulty = (
                RecommendedDifficulty.EASY
                if weak_topic.accuracy < self.policy.easy_accuracy_threshold
                else RecommendedDifficulty.MEDIUM
            )
            recommendations.append(
                LearningRecommendation(
                    concept_id=weak_topic.concept_id,
                    priority_score=weak_topic.priority_score,
                    accuracy=weak_topic.accuracy,
                    recommended_difficulty=difficulty,
                    reason=weak_topic.reason,
                )
            )
        return tuple(recommendations)


class WeakTopicNextTestSelector:
    """Builds the next question order with weak-topic focus while preserving Phase 6.6 ranking."""

    def __init__(self, policy: LearningRecommendationPolicy | None = None) -> None:
        self.policy = policy or LearningRecommendationPolicy()

    def select(
        self,
        analysis: TestAnalysis,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        *,
        question_count: int,
    ) -> NextTestPlan:
        if question_count < 1:
            raise ValueError("question_count must be positive")

        recommendations = LearningRecommendationService(self.policy).recommend(analysis)
        if not recommendations:
            raise ValueError("no weak-topic recommendations available")

        question_by_id = {
            question.generated_question_id: question
            for question in questions
            if question.status is GeneratedQuestionStatus.ACCEPTED
        }
        candidate_by_id = {}
        for candidate in candidates:
            if candidate.question_id in candidate_by_id:
                raise ValueError("ranked candidates must have unique question IDs")
            if candidate.question_id not in question_by_id:
                raise ValueError("candidate must reference an accepted question")
            candidate_by_id[candidate.question_id] = candidate

        recent_ids = {outcome.question_id for outcome in analysis.outcomes}
        selected: list[RankedQuestionCandidate] = []
        selected_ids: set[str] = set()
        focus_concepts: list[str] = []
        focus_slots = min(question_count, max(1, int(question_count * self.policy.focus_ratio + 0.999999)))

        for recommendation in recommendations:
            while len(selected) < focus_slots:
                available = [
                    candidate
                    for candidate in candidate_by_id.values()
                    if candidate.question_id not in selected_ids
                    and recommendation.concept_id in question_by_id[candidate.question_id].concept_ids
                ]
                if not available:
                    break

                fresh = [candidate for candidate in available if candidate.question_id not in recent_ids]
                pool = fresh or available
                chosen = min(
                    pool,
                    key=lambda candidate: (
                        0
                        if candidate.score.difficulty.value == recommendation.recommended_difficulty.value
                        else 1,
                        -candidate.score.selection_score,
                        -candidate.score.novelty_score,
                        candidate.rank,
                        candidate.question_id,
                    ),
                )
                selected.append(chosen)
                selected_ids.add(chosen.question_id)
                if recommendation.concept_id not in focus_concepts:
                    focus_concepts.append(recommendation.concept_id)

                # One question per recommendation per round keeps multiple weak
                # topics represented instead of filling the test from one topic.
                break

        remaining = [
            candidate
            for candidate in candidate_by_id.values()
            if candidate.question_id not in selected_ids
        ]
        remaining.sort(
            key=lambda candidate: (
                candidate.question_id in recent_ids,
                -candidate.score.selection_score,
                -candidate.score.importance_score,
                candidate.rank,
                candidate.question_id,
            )
        )
        for candidate in remaining:
            if len(selected) >= question_count:
                break
            selected.append(candidate)
            selected_ids.add(candidate.question_id)

        if len(selected) < question_count:
            raise ValueError("not enough accepted ranked questions for the next test")

        ordered = tuple(
            candidate.__class__(
                question_id=candidate.question_id,
                score=candidate.score,
                rank=index,
            )
            for index, candidate in enumerate(selected[:question_count], start=1)
        )
        return NextTestPlan(
            question_ids=tuple(candidate.question_id for candidate in ordered),
            ranked_candidates=ordered,
            focus_concept_ids=tuple(focus_concepts),
            recommendations=recommendations,
        )
