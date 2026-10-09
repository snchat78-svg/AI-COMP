from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from ai_comp.domain.adaptive_study_strategy import AdaptiveStudyStrategyReport
from ai_comp.domain.study_schedule import StudySchedule


class AdaptiveStudyStrategyAuditConflictError(RuntimeError):
    """Raised when an audit idempotency key is reused for different evidence."""


@dataclass(frozen=True)
class AdaptiveStudyStrategyAudit:
    """Immutable audit snapshot of a strategy recommendation and its applied schedule."""

    audit_id: str
    source_schedule: StudySchedule
    strategy_report: AdaptiveStudyStrategyReport
    resulting_schedule: StudySchedule
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not self.audit_id.strip():
            raise ValueError("audit_id is required")
        if self.strategy_report.learner_id != self.source_schedule.learner_id:
            raise ValueError("strategy report learner does not match source schedule")
        if self.strategy_report.schedule_id != self.source_schedule.schedule_id:
            raise ValueError("strategy report fingerprint does not match source schedule")
        if self.resulting_schedule.learner_id != self.source_schedule.learner_id:
            raise ValueError("resulting schedule learner does not match source schedule")
        if self.resulting_schedule.generated_at < self.strategy_report.generated_at:
            raise ValueError("resulting schedule cannot precede strategy report generation")
        source_tasks = {
            task.task_id: task
            for day in self.source_schedule.days
            for task in day.tasks
        }
        for adjustment in self.strategy_report.adjustments:
            source_task = source_tasks.get(adjustment.task_id)
            if source_task is None:
                raise ValueError("strategy adjustment references a task outside source schedule")
            if source_task.kind is not adjustment.task_kind:
                raise ValueError("strategy adjustment task kind does not match source schedule")
            if source_task.priority_score != adjustment.current_priority_score:
                raise ValueError("strategy adjustment previous priority does not match source schedule")
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("recorded_at must be timezone-aware")
        if self.recorded_at < self.resulting_schedule.generated_at:
            raise ValueError("recorded_at cannot precede the resulting schedule")

    @property
    def learner_id(self) -> str:
        return self.source_schedule.learner_id

    @property
    def source_schedule_id(self) -> str:
        return self.source_schedule.schedule_id

    @property
    def resulting_schedule_id(self) -> str:
        return self.resulting_schedule.schedule_id

    @property
    def assessment_session_id(self) -> str:
        return self.strategy_report.assessment_session_id


class AdaptiveStudyStrategyAuditRepository(Protocol):
    def get_audit(self, audit_id: str) -> AdaptiveStudyStrategyAudit | None: ...

    def save_audit(self, audit: AdaptiveStudyStrategyAudit) -> AdaptiveStudyStrategyAudit: ...

    def list_for_learner(
        self,
        learner_id: str,
        *,
        limit: int = 50,
    ) -> tuple[AdaptiveStudyStrategyAudit, ...]: ...


__all__ = [
    "AdaptiveStudyStrategyAudit",
    "AdaptiveStudyStrategyAuditConflictError",
    "AdaptiveStudyStrategyAuditRepository",
]
