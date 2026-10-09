from __future__ import annotations

from datetime import datetime

from ai_comp.domain.adaptive_study_strategy import AdaptiveStudyStrategyReport
from ai_comp.domain.adaptive_study_strategy_audit import (
    AdaptiveStudyStrategyAudit,
    AdaptiveStudyStrategyAuditRepository,
)
from ai_comp.domain.study_schedule import StudySchedule


class AdaptiveStudyStrategyAuditService:
    """Persists immutable strategy-and-replan snapshots through one audit repository."""

    def __init__(self, repository: AdaptiveStudyStrategyAuditRepository) -> None:
        self.repository = repository

    def record_applied_strategy(
        self,
        audit_id: str,
        *,
        source_schedule: StudySchedule,
        strategy_report: AdaptiveStudyStrategyReport,
        resulting_schedule: StudySchedule,
        recorded_at: datetime | None = None,
    ) -> AdaptiveStudyStrategyAudit:
        # A deterministic default lets a retry reuse the same idempotency key/payload.
        audit = AdaptiveStudyStrategyAudit(
            audit_id=audit_id,
            source_schedule=source_schedule,
            strategy_report=strategy_report,
            resulting_schedule=resulting_schedule,
            recorded_at=recorded_at or resulting_schedule.generated_at,
        )
        return self.repository.save_audit(audit)

    def get_audit(self, audit_id: str) -> AdaptiveStudyStrategyAudit | None:
        return self.repository.get_audit(audit_id)

    def list_for_learner(
        self,
        learner_id: str,
        *,
        limit: int = 50,
    ) -> tuple[AdaptiveStudyStrategyAudit, ...]:
        return self.repository.list_for_learner(learner_id, limit=limit)


__all__ = ["AdaptiveStudyStrategyAuditService"]
