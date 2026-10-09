from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from collections.abc import Mapping

from ai_comp.analysis.adaptive_study_strategy_audit import AdaptiveStudyStrategyAuditService
from ai_comp.analysis.study_schedule_execution import StudyScheduleExecutionService
from ai_comp.domain.adaptive_study_strategy import AdaptiveStudyStrategyReport
from ai_comp.domain.adaptive_study_strategy_audit import AdaptiveStudyStrategyAudit
from ai_comp.domain.study_schedule import StudySchedule


@dataclass(frozen=True)
class AdaptiveStudyStrategyApplicationResult:
    """The replanned schedule paired with the durable audit of that exact result."""

    schedule: StudySchedule
    audit: AdaptiveStudyStrategyAudit

    def __post_init__(self) -> None:
        if self.schedule != self.audit.resulting_schedule:
            raise ValueError("application result schedule must match its audit snapshot")


class AdaptiveStudyStrategyWorkflow:
    """Coordinates replan and audit persistence through the existing canonical services.

    Replanning is a pure derivation over schedule plus append-only execution history.
    The exact resulting schedule and report are then committed through the audit
    repository as one immutable snapshot. Callers supply a stable audit_id and as_of
    clock so retries can replay the same request safely.
    """

    def __init__(
        self,
        schedule_execution_service: StudyScheduleExecutionService,
        audit_service: AdaptiveStudyStrategyAuditService,
    ) -> None:
        self.schedule_execution_service = schedule_execution_service
        self.audit_service = audit_service

    def apply_and_record(
        self,
        audit_id: str,
        *,
        source_schedule: StudySchedule,
        strategy_report: AdaptiveStudyStrategyReport,
        daily_minutes: int,
        as_of: datetime,
        weekday_minutes: Mapping[int, int] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        first_day_minutes: int | None = None,
        exam_date: date | None = None,
    ) -> AdaptiveStudyStrategyApplicationResult:
        if not audit_id.strip():
            raise ValueError("audit_id is required")
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        if as_of < strategy_report.generated_at:
            raise ValueError("as_of cannot precede strategy report generation")

        resulting_schedule = self.schedule_execution_service.replan(
            source_schedule,
            daily_minutes=daily_minutes,
            weekday_minutes=weekday_minutes,
            start_date=start_date,
            end_date=end_date,
            first_day_minutes=first_day_minutes,
            as_of=as_of,
            exam_date=exam_date,
            strategy_report=strategy_report,
        )
        audit = self.audit_service.record_applied_strategy(
            audit_id,
            source_schedule=source_schedule,
            strategy_report=strategy_report,
            resulting_schedule=resulting_schedule,
            recorded_at=resulting_schedule.generated_at,
        )
        return AdaptiveStudyStrategyApplicationResult(
            schedule=resulting_schedule,
            audit=audit,
        )


__all__ = [
    "AdaptiveStudyStrategyApplicationResult",
    "AdaptiveStudyStrategyWorkflow",
]
