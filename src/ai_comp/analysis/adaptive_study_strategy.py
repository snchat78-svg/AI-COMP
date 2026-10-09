from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_outcome_feedback import (
    OutcomeEvidenceKind,
    StudyOutcomeFeedbackReport,
    StudyTaskOutcome,
)
from ai_comp.domain.study_schedule import ScheduledStudyTask, StudySchedule
from ai_comp.domain.study_schedule_execution import StudyTaskExecutionStatus
from ai_comp.domain.adaptive_study_strategy import (
    AdaptiveStudyStrategyReport,
    StudyStrategyAction,
    StudyTaskStrategyAdjustment,
)


@dataclass(frozen=True)
class AdaptiveStudyStrategyPolicy:
    """Conservative strategy thresholds; all changes are recommendations, not writes."""

    minimum_baseline_attempts: int = 2
    minimum_follow_up_attempts: int = 2
    maximum_priority_increase: float = 0.15
    maximum_priority_decrease: float = 0.08
    minimum_priority_change: float = 0.02
    consolidation_accuracy_percentage: float = 85.0
    declining_revision_interval_days: int = 1
    stable_revision_interval_days: int = 3
    improving_revision_interval_days: int = 5
    consolidated_revision_interval_days: int = 7

    def __post_init__(self) -> None:
        for name in ("minimum_baseline_attempts", "minimum_follow_up_attempts"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("maximum_priority_increase", "maximum_priority_decrease"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if not 0.0 < self.minimum_priority_change <= min(
            self.maximum_priority_increase, self.maximum_priority_decrease
        ):
            raise ValueError("minimum priority change must fit within both adjustment caps")
        if not 0.0 <= self.consolidation_accuracy_percentage <= 100.0:
            raise ValueError("consolidation accuracy must be between 0 and 100")
        interval_values = (
            self.declining_revision_interval_days,
            self.stable_revision_interval_days,
            self.improving_revision_interval_days,
            self.consolidated_revision_interval_days,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 1
            for value in interval_values
        ):
            raise ValueError("revision intervals must be positive integers")
        if tuple(sorted(interval_values)) != interval_values:
            raise ValueError("revision intervals must be ordered from decline to consolidation")


class AdaptiveStudyStrategyService:
    """Turns Phase 6.22 observations into conservative next-strategy recommendations.

    It is deliberately read-only: this service does not change prior history,
    spaced-revision records, or the immutable Phase 6.20/6.21 schedule.
    """

    def __init__(
        self,
        *,
        policy: AdaptiveStudyStrategyPolicy | None = None,
    ) -> None:
        self.policy = policy or AdaptiveStudyStrategyPolicy()

    def update_strategy(
        self,
        schedule: StudySchedule,
        outcome_report: StudyOutcomeFeedbackReport,
        *,
        generated_at: datetime | None = None,
    ) -> AdaptiveStudyStrategyReport:
        if outcome_report.learner_id != schedule.learner_id:
            raise ValueError("outcome report learner does not match schedule")
        if outcome_report.schedule_id != schedule.schedule_id:
            raise ValueError("outcome report schedule fingerprint does not match")
        report_time = generated_at or datetime.now(timezone.utc)
        if report_time.tzinfo is None or report_time.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        if report_time < outcome_report.assessed_at:
            raise ValueError("generated_at cannot precede the completed assessment")

        tasks: dict[str, ScheduledStudyTask] = {
            task.task_id: task
            for day in schedule.days
            for task in day.tasks
        }
        adjustments = []
        for outcome in sorted(outcome_report.outcomes, key=lambda item: item.task_id):
            task = tasks.get(outcome.task_id)
            if task is None:
                raise ValueError("outcome report references a task outside the schedule")
            if task.kind is not outcome.task_kind:
                raise ValueError("outcome report task kind does not match schedule")
            adjustments.append(self._adjust(task, outcome))

        return AdaptiveStudyStrategyReport(
            learner_id=schedule.learner_id,
            schedule_id=schedule.schedule_id,
            assessment_session_id=outcome_report.assessment_session_id,
            assessed_at=outcome_report.assessed_at,
            adjustments=tuple(adjustments),
            generated_at=report_time,
        )

    def _adjust(
        self,
        task: ScheduledStudyTask,
        outcome: StudyTaskOutcome,
    ) -> StudyTaskStrategyAdjustment:
        reason_for_hold = self._hold_reason(outcome)
        enough_evidence = reason_for_hold is None
        if not enough_evidence:
            return StudyTaskStrategyAdjustment(
                task_id=task.task_id,
                task_kind=task.kind,
                execution_status=outcome.execution_status,
                evidence_kind=outcome.evidence_kind,
                source_trend=outcome.trend,
                action=StudyStrategyAction.COLLECT_MORE_EVIDENCE,
                current_priority_score=task.priority_score,
                recommended_priority_score=task.priority_score,
                suggested_revision_interval_days=None,
                baseline_attempted_count=outcome.baseline_attempted_count,
                follow_up_attempted_count=outcome.follow_up_attempted_count,
                baseline_accuracy_percentage=outcome.baseline_accuracy_percentage,
                follow_up_accuracy_percentage=outcome.follow_up_accuracy_percentage,
                delta_percentage_points=outcome.delta_percentage_points,
                reason=reason_for_hold or "More evidence is required before adapting this task.",
            )

        delta = outcome.delta_percentage_points
        assert delta is not None
        next_priority = task.priority_score
        if outcome.trend is LearningTrend.DECLINING:
            scale = abs(delta) / 100.0
            adjustment = min(
                self.policy.maximum_priority_increase,
                max(self.policy.minimum_priority_change,
                    scale * self.policy.maximum_priority_increase),
            )
            next_priority = min(1.0, task.priority_score + adjustment)
            action = StudyStrategyAction.REINFORCE_WEAK_AREA
            interval = self.policy.declining_revision_interval_days
            reason = (
                f"Linked accuracy declined by {abs(delta):.2f} percentage points; "
                "raise this task's focus modestly and review again soon. The trend "
                "is descriptive, not proof that the prior task caused the result."
            )
        elif outcome.trend is LearningTrend.IMPROVING:
            follow_up_accuracy = outcome.follow_up_accuracy_percentage
            assert follow_up_accuracy is not None
            if follow_up_accuracy >= self.policy.consolidation_accuracy_percentage:
                scale = max(0.0, delta) / 100.0
                reduction = min(
                    self.policy.maximum_priority_decrease,
                    max(self.policy.minimum_priority_change,
                        scale * self.policy.maximum_priority_decrease),
                )
                next_priority = max(0.0, task.priority_score - reduction)
                action = StudyStrategyAction.SPACE_REVISION
                interval = self.policy.consolidated_revision_interval_days
                reason = (
                    f"Linked accuracy improved and follow-up accuracy reached "
                    f"{self.policy.consolidation_accuracy_percentage:.1f}%; ease "
                    "priority slightly and widen the suggested review interval. "
                    "This is an association, not proof of causation."
                )
            else:
                action = StudyStrategyAction.CONTINUE_TARGETED_PRACTICE
                interval = self.policy.improving_revision_interval_days
                reason = (
                    f"Linked accuracy improved by {delta:.2f} percentage points, "
                    "but follow-up accuracy remains below the consolidation threshold; "
                    "continue focused practice before spacing reviews further."
                )
        else:
            action = StudyStrategyAction.MAINTAIN_AND_RETEST
            interval = self.policy.stable_revision_interval_days
            reason = (
                "Linked accuracy is broadly stable; keep the current priority and "
                "retest after a controlled interval instead of making a large change."
            )

        return StudyTaskStrategyAdjustment(
            task_id=task.task_id,
            task_kind=task.kind,
            execution_status=outcome.execution_status,
            evidence_kind=outcome.evidence_kind,
            source_trend=outcome.trend,
            action=action,
            current_priority_score=task.priority_score,
            recommended_priority_score=next_priority,
            suggested_revision_interval_days=interval,
            baseline_attempted_count=outcome.baseline_attempted_count,
            follow_up_attempted_count=outcome.follow_up_attempted_count,
            baseline_accuracy_percentage=outcome.baseline_accuracy_percentage,
            follow_up_accuracy_percentage=outcome.follow_up_accuracy_percentage,
            delta_percentage_points=delta,
            reason=reason,
        )

    def _hold_reason(self, outcome: StudyTaskOutcome) -> str | None:
        if outcome.execution_status in {
            StudyTaskExecutionStatus.SKIPPED,
            StudyTaskExecutionStatus.POSTPONED,
        }:
            return (
                f"The latest task status is {outcome.execution_status.value}; skipped "
                "or postponed work cannot trigger an adaptive strategy change."
            )
        if outcome.evidence_kind is OutcomeEvidenceKind.NO_RELATED_EVIDENCE:
            return "No direct-question or explicit concept evidence links this task to the assessment."
        if outcome.trend is LearningTrend.INSUFFICIENT_DATA:
            return "The baseline or follow-up sample is too small to support a strategy change."
        if (
            outcome.baseline_attempted_count < self.policy.minimum_baseline_attempts
            or outcome.follow_up_attempted_count < self.policy.minimum_follow_up_attempts
            or outcome.baseline_accuracy_percentage is None
            or outcome.follow_up_accuracy_percentage is None
            or outcome.delta_percentage_points is None
        ):
            return "The configured minimum evidence threshold has not been met; keep the current strategy."
        if outcome.trend is LearningTrend.DECLINING and outcome.delta_percentage_points >= 0:
            raise ValueError("declining outcome must have a negative accuracy delta")
        if outcome.trend is LearningTrend.IMPROVING and outcome.delta_percentage_points <= 0:
            raise ValueError("improving outcome must have a positive accuracy delta")
        return None


__all__ = ["AdaptiveStudyStrategyPolicy", "AdaptiveStudyStrategyService"]
