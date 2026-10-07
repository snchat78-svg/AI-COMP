from __future__ import annotations

from collections.abc import Sequence

from ai_comp.domain.learning_history import LearnerLearningHistory
from ai_comp.domain.learning_recommendation import (
    LearningRecommendation,
    LearningRecommendationPolicy,
    RecommendedDifficulty,
)
from ai_comp.domain.material_generation import GeneratedMCQ, GeneratedQuestionStatus
from ai_comp.domain.personalized_preparation import (
    PersonalizedPreparationMode,
    PersonalizedPreparationPlan,
    PersonalizedPreparationPolicy,
)
from ai_comp.domain.question_intelligence import DifficultyLevel, RankedQuestionCandidate
from ai_comp.domain.question_learning import LearnerQuestionHistory
from ai_comp.domain.test_analysis import TestAnalysis
from ai_comp.domain.test_engine import ScoringPolicy, TestSpecification


class PersonalizedPreparationService:
    """Coordinates long-term weakness, prior mistakes and Phase 6.6 ranking."""

    def __init__(
        self,
        policy: PersonalizedPreparationPolicy | None = None,
        recommendation_policy: LearningRecommendationPolicy | None = None,
    ) -> None:
        self.policy = policy or PersonalizedPreparationPolicy()
        self.recommendation_policy = (
            recommendation_policy or LearningRecommendationPolicy()
        )

    def build_plan(
        self,
        learner_id: str,
        *,
        test_id: str,
        title: str,
        question_count: int,
        duration_seconds: int,
        history: LearnerLearningHistory,
        question_history: LearnerQuestionHistory,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        current_analysis: TestAnalysis | None = None,
        mode: PersonalizedPreparationMode = PersonalizedPreparationMode.ADAPTIVE,
        scoring: ScoringPolicy | None = None,
        shuffle_questions: bool = False,
        shuffle_seed: int | None = None,
        exclude_question_ids: Sequence[str] = (),
    ) -> PersonalizedPreparationPlan:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if history.learner_id != learner_id:
            raise ValueError("learning history learner does not match")
        if question_history.learner_id != learner_id:
            raise ValueError("question history learner does not match")
        if question_count < 1:
            raise ValueError("question_count must be positive")

        accepted = {
            question.generated_question_id: question
            for question in questions
            if question.status is GeneratedQuestionStatus.ACCEPTED
        }
        candidate_by_id: dict[str, RankedQuestionCandidate] = {}
        for candidate in candidates:
            if candidate.question_id in candidate_by_id:
                raise ValueError("ranked candidates must have unique question IDs")
            if candidate.question_id not in accepted:
                raise ValueError("candidate must reference an accepted question")
            candidate_by_id[candidate.question_id] = candidate

        excluded = set(exclude_question_ids)
        if current_analysis is not None:
            excluded.update(
                outcome.question_id for outcome in current_analysis.outcomes
            )

        recommendations = self._recommendations(history, current_analysis)
        revision_pool = {
            item.question_id: item
            for item in question_history.revision_candidates
            if item.question_id in candidate_by_id
            and item.question_id not in excluded
        }

        if mode is PersonalizedPreparationMode.REVISION:
            if not revision_pool:
                raise ValueError("no prior mistakes available for revision")
            revision_slots = question_count
        elif mode is PersonalizedPreparationMode.WEAK_TOPICS:
            revision_slots = 0
        else:
            revision_slots = (
                min(
                    question_count,
                    self._ceil_ratio(
                        question_count, self.policy.revision_ratio
                    ),
                )
                if revision_pool
                else 0
            )

        selected: list[RankedQuestionCandidate] = []
        selected_ids: set[str] = set()
        revision_selected: list[str] = []

        revision_candidates = sorted(
            (
                candidate
                for question_id, candidate in candidate_by_id.items()
                if question_id in revision_pool
            ),
            key=lambda candidate: (
                -revision_pool[candidate.question_id].priority_score,
                -revision_pool[candidate.question_id].mistake_streak,
                -revision_pool[candidate.question_id].mistake_count,
                candidate.rank,
                candidate.question_id,
            ),
        )
        for candidate in revision_candidates[:revision_slots]:
            selected.append(candidate)
            selected_ids.add(candidate.question_id)
            revision_selected.append(candidate.question_id)

        remaining_count = question_count - len(selected)
        focus_concepts: list[str] = []

        if remaining_count:
            remaining_candidates = tuple(
                candidate
                for candidate in candidate_by_id.values()
                if candidate.question_id not in selected_ids
                and candidate.question_id not in excluded
            )

            if mode is PersonalizedPreparationMode.REVISION:
                selected.extend(
                    self._rank_general(remaining_candidates)[:remaining_count]
                )
            else:
                weak_slots = (
                    remaining_count
                    if mode is PersonalizedPreparationMode.WEAK_TOPICS
                    else min(
                        remaining_count,
                        self._ceil_ratio(
                            remaining_count,
                            self.policy.weak_topic_ratio,
                        ),
                    )
                )
                focused, focus_concepts = self._select_weak_topics(
                    recommendations,
                    remaining_candidates,
                    accepted,
                    weak_slots,
                )
                selected.extend(focused)

                if len(selected) < question_count:
                    selected_ids_local = {
                        candidate.question_id for candidate in selected
                    }
                    general_pool = tuple(
                        candidate
                        for candidate in remaining_candidates
                        if candidate.question_id not in selected_ids_local
                    )
                    selected.extend(
                        self._rank_general(general_pool)[
                            : question_count - len(selected)
                        ]
                    )

        if len(selected) < question_count:
            raise ValueError(
                "not enough accepted ranked questions for personalized test"
            )

        selected = selected[:question_count]
        ordered = tuple(
            candidate.__class__(
                question_id=candidate.question_id,
                score=candidate.score,
                rank=index,
            )
            for index, candidate in enumerate(selected, start=1)
        )

        if not focus_concepts:
            focus_concepts = self._derive_focus_concepts(
                recommendations,
                ordered,
                accepted,
            )

        difficulty = self._recommended_difficulty(recommendations)
        effective_mode = self._effective_mode(
            mode, revision_selected, focus_concepts
        )
        reason = self._reason(
            effective_mode, revision_selected, focus_concepts
        )

        specification = TestSpecification(
            test_id=test_id,
            title=title,
            question_count=question_count,
            duration_seconds=duration_seconds,
            scoring=scoring or ScoringPolicy(),
            shuffle_questions=shuffle_questions,
            shuffle_seed=shuffle_seed,
        )

        return PersonalizedPreparationPlan(
            learner_id=learner_id,
            test_specification=specification,
            mode=effective_mode,
            recommended_difficulty=difficulty,
            question_ids=tuple(
                candidate.question_id for candidate in ordered
            ),
            ranked_candidates=ordered,
            focus_concept_ids=tuple(focus_concepts),
            revision_question_ids=tuple(revision_selected),
            recommendations=tuple(recommendations),
            reason=reason,
        )

    def _recommendations(
        self,
        history: LearnerLearningHistory,
        current_analysis: TestAnalysis | None,
    ) -> tuple[LearningRecommendation, ...]:
        from ai_comp.analysis.learning import LearningRecommendationService
        from ai_comp.analysis.personalization import (
            LongTermLearningRecommendationService,
        )

        recommendations = LongTermLearningRecommendationService(
            self.recommendation_policy
        ).recommend(history)
        if recommendations or current_analysis is None:
            return recommendations
        return LearningRecommendationService(
            self.recommendation_policy
        ).recommend(current_analysis)

    @staticmethod
    def _select_weak_topics(
        recommendations: Sequence[LearningRecommendation],
        candidates: Sequence[RankedQuestionCandidate],
        accepted: dict[str, GeneratedMCQ],
        question_count: int,
    ) -> tuple[list[RankedQuestionCandidate], list[str]]:
        if question_count <= 0 or not recommendations:
            return [], []

        selected: list[RankedQuestionCandidate] = []
        selected_ids: set[str] = set()
        focus_concepts: list[str] = []

        while len(selected) < question_count:
            progress = False
            for recommendation in recommendations:
                if len(selected) >= question_count:
                    break
                available = [
                    candidate
                    for candidate in candidates
                    if candidate.question_id not in selected_ids
                    and recommendation.concept_id
                    in accepted[candidate.question_id].concept_ids
                ]
                if not available:
                    continue

                chosen = min(
                    available,
                    key=lambda candidate: (
                        0
                        if candidate.score.difficulty.value
                        == recommendation.recommended_difficulty.value
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

        return selected, focus_concepts

    @staticmethod
    def _rank_general(
        candidates: Sequence[RankedQuestionCandidate],
    ) -> list[RankedQuestionCandidate]:
        return sorted(
            candidates,
            key=lambda candidate: (
                -candidate.score.selection_score,
                -candidate.score.importance_score,
                -candidate.score.novelty_score,
                candidate.rank,
                candidate.question_id,
            ),
        )

    @staticmethod
    def _recommended_difficulty(
        recommendations: Sequence[LearningRecommendation],
    ) -> DifficultyLevel | None:
        if not recommendations:
            return None
        return (
            DifficultyLevel.EASY
            if recommendations[0].recommended_difficulty
            is RecommendedDifficulty.EASY
            else DifficultyLevel.MEDIUM
        )

    @staticmethod
    def _derive_focus_concepts(
        recommendations: Sequence[LearningRecommendation],
        ordered: Sequence[RankedQuestionCandidate],
        accepted: dict[str, GeneratedMCQ],
    ) -> list[str]:
        selected_ids = {
            candidate.question_id for candidate in ordered
        }
        return [
            recommendation.concept_id
            for recommendation in recommendations
            if any(
                question_id in selected_ids
                and recommendation.concept_id
                in accepted[question_id].concept_ids
                for question_id in selected_ids
            )
        ]

    @staticmethod
    def _effective_mode(
        requested: PersonalizedPreparationMode,
        revision_ids: Sequence[str],
        focus_concepts: Sequence[str],
    ) -> PersonalizedPreparationMode:
        if requested is not PersonalizedPreparationMode.ADAPTIVE:
            return requested
        if revision_ids and focus_concepts:
            return PersonalizedPreparationMode.MIXED
        if revision_ids:
            return PersonalizedPreparationMode.REVISION
        if focus_concepts:
            return PersonalizedPreparationMode.WEAK_TOPICS
        return PersonalizedPreparationMode.MIXED

    @staticmethod
    def _reason(
        mode: PersonalizedPreparationMode,
        revision_ids: Sequence[str],
        focus_concepts: Sequence[str],
    ) -> str:
        parts: list[str] = []
        if revision_ids:
            parts.append("previous mistakes prioritized")
        if focus_concepts:
            parts.append("weak concepts prioritized")
        if not parts:
            parts.append("Phase 6.6 ranked questions prioritized")
        return "; ".join(parts) + f" ({mode.value.lower()})"

    @staticmethod
    def _ceil_ratio(value: int, ratio: float) -> int:
        return int(value * ratio + 0.999999)
