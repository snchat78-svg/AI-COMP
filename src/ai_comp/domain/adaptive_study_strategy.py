from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_outcome_feedback import OutcomeEvidenceKind
from ai_comp.domain.study_schedule import StudyTaskKind
from ai_comp.domain.study_schedule_execution import StudyTaskExecutionStatus


class StudyStrategyAction(str, Enum):
    REINFORCE_WEAK_AREA = "REINFORCE_WEAK_AREA"
    CONTINUE_TARGETED_PRACTICE = "CONTINUE_TARGETED_PRACTICE"
    MAINTAIN_AND_RETEST = "MAINTAIN_AND_RETEST"
    SPACE_REVISION = "SPACE_REVISION"
    COLLECT_MORE_EVIDENCE = "COLLECT_MORE_EVIDENCE"


@dataclass(frozen=True)
class StudyTaskStrategyAdjustment:
    """Explainable, proposed strategy for a task; it does not mutate a schedule."""

    task_id: str
    task_kind: StudyTaskKind
    execution_status: StudyTaskExecutionStatus
    evidence_kind: OutcomeEvidenceKind
    source_trend: LearningTrend
    action: StudyStrategyAction
    current_priority_score: float
    recommended_priority_score: float
    suggested_revision_interval_days: int | None
    baseline_attempted_count: int
    follow_up_attempted_count: int
    baseline_accuracy_percentage: float | None
    follow_up_accuracy_percentage: float | None
    delta_percentage_points: float | None
    reason: str

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id is required")
        if not self.reason.strip():
            raise ValueError("reason is required")
        for name, value in (
            ("current_priority_score", self.current_priority_score),
            ("recommended_priority_score", self.recommended_priority_score),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        for name in ("baseline_attempted_count", "follow_up_attempted_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name, value in (
            ("baseline_accuracy_percentage", self.baseline_accuracy_percentage),
            ("follow_up_accuracy_percentage", self.follow_up_accuracy_percentage),
        ):
            if value is not None and not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be between 0 and 100")
        if (
            self.baseline_accuracy_percentage is not None
            and self.baseline_attempted_count == 0
        ):
            raise ValueError("baseline accuracy requires baseline attempts")
        if (
            self.follow_up_accuracy_percentage is not None
            and self.follow_up_attempted_count == 0
        ):
            raise ValueError("follow-up accuracy requires follow-up attempts")
        if self.source_trend is LearningTrend.INSUFFICIENT_DATA:
            if self.delta_percentage_points is not None:
                raise ValueError("insufficient-data trend cannot contain a delta")
        elif self.delta_percentage_points is None:
            raise ValueError("supported trend requires a delta")

        if self.action is StudyStrategyAction.COLLECT_MORE_EVIDENCE:
            if self.suggested_revision_interval_days is not None:
                raise ValueError("insufficient evidence cannot set a revision interval")
            if self.current_priority_score != self.recommended_priority_score:
                raise ValueError("insufficient evidence cannot change priority")
        else:
            if self.evidence_kind is OutcomeEvidenceKind.NO_RELATED_EVIDENCE:
                raise ValueError("strategy adjustment requires linked evidence")
            if self.source_trend is LearningTrend.INSUFFICIENT_DATA:
                raise ValueError("strategy adjustment requires a supported trend")
            if self.execution_status in {
                StudyTaskExecutionStatus.SKIPPED,
                StudyTaskExecutionStatus.POSTPONED,
            }:
                raise ValueError("skipped or postponed work cannot drive an adjustment")
            if (
                self.suggested_revision_interval_days is None
                or self.suggested_revision_interval_days < 1
            ):
                raise ValueError("adjusted strategy requires a positive revision interval")

    @property
    def priority_delta(self) -> float:
        return self.recommended_priority_score - self.current_priority_score

    @property
    def was_adapted(self) -> bool:
        return (
            self.suggested_revision_interval_days is not None
            or abs(self.priority_delta) > 1e-9
        )


@dataclass(frozen=True)
class AdaptiveStudyStrategyReport:
    """Proposed evidence-based study-strategy changes for one assessment and schedule."""

    learner_id: str
    schedule_id: str
    assessment_session_id: str
    assessed_at: datetime
    adjustments: tuple[StudyTaskStrategyAdjustment, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        for name in ("learner_id", "schedule_id", "assessment_session_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if len(self.schedule_id) != 64:
            raise ValueError("schedule_id must be a 64-character fingerprint")
        try:
            int(self.schedule_id, 16)
        except ValueError as exc:
            raise ValueError("schedule_id must be hexadecimal") from exc
        for name in ("assessed_at", "generated_at"):
            value = getattr(self, name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.generated_at < self.assessed_at:
            raise ValueError("strategy report cannot precede its assessment")
        task_ids = tuple(item.task_id for item in self.adjustments)
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("strategy adjustments must be unique per task")

    @property
    def adapted_task_count(self) -> int:
        return sum(item.was_adapted for item in self.adjustments)

    @property
    def evidence_limited_count(self) -> int:
        return sum(
            item.action is StudyStrategyAction.COLLECT_MORE_EVIDENCE
            for item in self.adjustments
        )


__all__ = [
    "AdaptiveStudyStrategyReport",
    "StudyStrategyAction",
    "StudyTaskStrategyAdjustment",
]
