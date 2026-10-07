from __future__ import annotations

from collections.abc import Sequence
from ai_comp.domain.learning_history import LearnerLearningHistory, LearningTrend, LongTermPerformanceBand
from ai_comp.domain.material_generation import GeneratedMCQ, GeneratedQuestionStatus
from ai_comp.domain.question_intelligence import RankedQuestionCandidate
from ai_comp.domain.test_analysis import TestAnalysis
from ai_comp.domain.learning_recommendation import (
    LearningRecommendation,
    LearningRecommendationPolicy,
    NextTestPlan,
    RecommendedDifficulty,
)


class LongTermLearningRecommendationService:
    """Converts persistent multi-test topic history into actionable recommendations."""

    def __init__(self, policy: LearningRecommendationPolicy | None = None) -> None:
        self.policy = policy or LearningRecommendationPolicy()

    def recommend(
        self,
        history: LearnerLearningHistory,
    ) -> tuple[LearningRecommendation, ...]:
        rows = [
            topic for topic in history.topic_performance
            if topic.performance is LongTermPerformanceBand.WEAK
        ]
        rows.sort(key=lambda item: (-item.priority_score, item.concept_id))
        return tuple(
            LearningRecommendation(
                concept_id=topic.concept_id,
                priority_score=topic.priority_score,
                accuracy=topic.accuracy,
                recommended_difficulty=(
                    RecommendedDifficulty.EASY
                    if topic.recent_accuracy < self.policy.easy_accuracy_threshold
                    else RecommendedDifficulty.MEDIUM
                ),
                reason=self._reason(topic.trend, topic.weak_streak),
            )
            for topic in rows[: self.policy.max_recommendations]
        )

    @staticmethod
    def _reason(trend: LearningTrend, weak_streak: int) -> str:
        if trend is LearningTrend.DECLINING:
            return "accuracy trend declining"
        if weak_streak >= 2:
            return "topic remained weak across multiple tests"
        return "long-term accuracy is weak"


class PersonalizedNextTestSelector:
    """Uses durable history first, with recent weak topics as a fallback."""

    def __init__(self, policy: LearningRecommendationPolicy | None = None) -> None:
        self.policy = policy or LearningRecommendationPolicy()

    def select(
        self,
        history: LearnerLearningHistory,
        analysis: TestAnalysis,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        *,
        question_count: int,
    ) -> NextTestPlan:
        recommendations = LongTermLearningRecommendationService(self.policy).recommend(history)
        if not recommendations:
            from ai_comp.analysis.learning import LearningRecommendationService
            recommendations = LearningRecommendationService(self.policy).recommend(analysis)
        if not recommendations:
            raise ValueError("no learning recommendations available")

        accepted = {
            question.generated_question_id: question
            for question in questions
            if question.status is GeneratedQuestionStatus.ACCEPTED
        }
        by_id = {candidate.question_id: candidate for candidate in candidates}
        if len(by_id) != len(candidates):
            raise ValueError("ranked candidates must have unique question IDs")
        if any(question_id not in accepted for question_id in by_id):
            raise ValueError("candidate must reference an accepted question")

        recent_ids = {outcome.question_id for outcome in analysis.outcomes}
        selected: list[RankedQuestionCandidate] = []
        selected_ids: set[str] = set()
        focus_concepts: list[str] = []
        focus_slots = min(
            question_count,
            max(1, int(question_count * self.policy.focus_ratio + 0.999999)),
        )

        while len(selected) < focus_slots:
            progress = False
            for recommendation in recommendations:
                if len(selected) >= focus_slots:
                    break
                available = [
                    candidate
                    for candidate in by_id.values()
                    if candidate.question_id not in selected_ids
                    and recommendation.concept_id in accepted[candidate.question_id].concept_ids
                ]
                if not available:
                    continue
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
                progress = True
            if not progress:
                break

        remaining = [candidate for candidate in by_id.values() if candidate.question_id not in selected_ids]
        remaining.sort(
            key=lambda candidate: (
                candidate.question_id in recent_ids,
                -candidate.score.selection_score,
                -candidate.score.importance_score,
                candidate.rank,
                candidate.question_id,
            )
        )
        selected.extend(remaining[: max(0, question_count - len(selected))])

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
            recommendations=tuple(recommendations),
        )
