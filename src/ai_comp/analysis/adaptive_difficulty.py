from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from ai_comp.analysis.spaced_revision import SpacedRevisionService
from ai_comp.domain.adaptive_difficulty import (
    AdaptiveAction,
    AdaptiveDifficultyDecision,
    AdaptiveDifficultyPolicy,
    AdaptiveDifficultyProfile,
    MasteryStatus,
)
from ai_comp.domain.learning_history import LearnerLearningHistory, LearningTrend
from ai_comp.domain.question_learning import LearnerQuestionHistory
from ai_comp.domain.question_intelligence import DifficultyLevel


class AdaptiveDifficultyService:
    """Derives conservative difficulty and retention decisions from learner history."""

    def __init__(
        self,
        policy: AdaptiveDifficultyPolicy | None = None,
    ) -> None:
        self.policy = policy or AdaptiveDifficultyPolicy()

    def analyze(
        self,
        learner_id: str,
        learning_history: LearnerLearningHistory,
        question_history: LearnerQuestionHistory,
        *,
        as_of: datetime | None = None,
    ) -> AdaptiveDifficultyProfile:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if learning_history.learner_id != learner_id:
            raise ValueError("learning history learner does not match")
        if question_history.learner_id != learner_id:
            raise ValueError("question history learner does not match")

        reference_time = as_of or datetime.now(timezone.utc)
        schedules = SpacedRevisionService().schedules(
            question_history,
            as_of=reference_time,
        )

        performance_by_question = {
            performance.question_id: performance
            for performance in question_history.question_performance
        }
        due_by_concept: dict[str, int] = defaultdict(int)
        for schedule in schedules:
            if schedule.status.value != "DUE":
                continue
            performance = performance_by_question.get(schedule.question_id)
            if performance is None:
                continue
            for concept_id in performance.concept_ids:
                due_by_concept[concept_id] += 1

        alert_concepts = {
            alert.concept_id
            for alert in question_history.repeated_concept_alerts
        }

        decisions = tuple(
            self._decision(topic, due_by_concept, alert_concepts)
            for topic in learning_history.topic_performance
        )

        return AdaptiveDifficultyProfile(
            learner_id=learner_id,
            decisions=decisions,
            recommended_difficulty=self._overall_difficulty(decisions),
            retention_due_question_ids=tuple(
                schedule.question_id
                for schedule in schedules
                if schedule.status.value == "DUE"
            ),
            generated_at=reference_time,
        )

    def _decision(
        self,
        topic,
        due_by_concept: dict[str, int],
        alert_concepts: set[str],
    ) -> AdaptiveDifficultyDecision:
        due_count = due_by_concept.get(topic.concept_id, 0)
        repeated_weakness = topic.concept_id in alert_concepts

        if topic.test_count < self.policy.min_tests_for_progression:
            mastery = (
                MasteryStatus.LEARNING
                if topic.accuracy < self.policy.remediation_accuracy_threshold
                else MasteryStatus.INSUFFICIENT_DATA
            )
            action = (
                AdaptiveAction.REMEDIATE
                if mastery is MasteryStatus.LEARNING
                else AdaptiveAction.STABILIZE
            )
            difficulty = (
                DifficultyLevel.EASY
                if action is AdaptiveAction.REMEDIATE
                else DifficultyLevel.MEDIUM
            )
            reason = (
                "insufficient history with low accuracy"
                if action is AdaptiveAction.REMEDIATE
                else "insufficient history; keep medium difficulty"
            )
        elif (
            topic.accuracy < self.policy.remediation_accuracy_threshold
            or topic.recent_accuracy < self.policy.remediation_accuracy_threshold
            or topic.weak_streak > 0
            or repeated_weakness
        ):
            mastery = MasteryStatus.LEARNING
            action = AdaptiveAction.REMEDIATE
            difficulty = DifficultyLevel.EASY
            reason = "persistent weakness requires remediation"
        elif due_count:
            mastery = MasteryStatus.RETENTION_DUE
            action = AdaptiveAction.RETAIN
            difficulty = DifficultyLevel.MEDIUM
            reason = "strong topic has retention review due"
        elif (
            topic.test_count >= self.policy.mastery_min_tests
            and topic.accuracy >= self.policy.mastery_accuracy_threshold
            and topic.recent_accuracy >= self.policy.mastery_recent_accuracy_threshold
            and topic.trend is not LearningTrend.DECLINING
        ):
            mastery = MasteryStatus.MASTERED
            action = AdaptiveAction.ADVANCE
            difficulty = DifficultyLevel.HARD
            reason = "repeated high performance supports difficulty advancement"
        else:
            mastery = MasteryStatus.DEVELOPING
            action = AdaptiveAction.STABILIZE
            difficulty = DifficultyLevel.MEDIUM
            reason = "progress is not yet strong enough for hard advancement"

        retention_signal = min(1.0, due_count / 3.0)
        priority = max(topic.priority_score, retention_signal)
        if action is AdaptiveAction.ADVANCE:
            priority = min(priority, 0.50)

        return AdaptiveDifficultyDecision(
            concept_id=topic.concept_id,
            test_count=topic.test_count,
            accuracy=topic.accuracy,
            recent_accuracy=topic.recent_accuracy,
            trend=topic.trend,
            weak_streak=topic.weak_streak,
            mastery=mastery,
            action=action,
            recommended_difficulty=difficulty,
            retention_due_count=due_count,
            priority_score=priority,
            reason=reason,
        )

    @staticmethod
    def _overall_difficulty(
        decisions: tuple[AdaptiveDifficultyDecision, ...],
    ) -> DifficultyLevel:
        if not decisions:
            return DifficultyLevel.MEDIUM
        if any(
            decision.action is AdaptiveAction.REMEDIATE
            for decision in decisions
        ):
            return DifficultyLevel.EASY
        if any(
            decision.mastery is MasteryStatus.RETENTION_DUE
            for decision in decisions
        ):
            return DifficultyLevel.MEDIUM
        if all(
            decision.mastery is MasteryStatus.MASTERED
            for decision in decisions
        ):
            return DifficultyLevel.HARD
        return DifficultyLevel.MEDIUM


__all__ = ["AdaptiveDifficultyService"]
