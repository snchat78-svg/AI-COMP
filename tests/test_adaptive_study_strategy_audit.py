from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from ai_comp.analysis.adaptive_study_strategy_audit import AdaptiveStudyStrategyAuditService
from ai_comp.domain.adaptive_study_strategy import (
    AdaptiveStudyStrategyReport,
    StudyStrategyAction,
    StudyTaskStrategyAdjustment,
)
from ai_comp.domain.adaptive_study_strategy_audit import (
    AdaptiveStudyStrategyAudit,
    AdaptiveStudyStrategyAuditConflictError,
)
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_outcome_feedback import OutcomeEvidenceKind
from ai_comp.domain.study_schedule import (
    ScheduledStudyTask, StudyDayPlan, StudySchedule, StudyTaskKind,
)
from ai_comp.domain.study_schedule_execution import StudyTaskExecutionStatus


NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


class InMemoryAuditRepository:
    def __init__(self):
        self.rows = {}

    def get_audit(self, audit_id):
        return self.rows.get(audit_id)

    def save_audit(self, audit):
        old = self.rows.get(audit.audit_id)
        if old is not None and old != audit:
            raise AdaptiveStudyStrategyAuditConflictError("audit ID already exists with different evidence")
        self.rows[audit.audit_id] = audit
        return self.rows[audit.audit_id]

    def list_for_learner(self, learner_id, *, limit=50):
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        return tuple(sorted(
            (row for row in self.rows.values() if row.learner_id == learner_id),
            key=lambda row: (row.recorded_at, row.audit_id),
            reverse=True,
        )[:limit])


def make_schedule(*, generated_at=NOW - timedelta(days=2), priority=0.60):
    task = ScheduledStudyTask(
        task_id="task-science",
        kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        scheduled_date=NOW.date() - timedelta(days=1),
        title="Study science",
        estimated_minutes=20,
        priority_score=priority,
        reason="Existing learner evidence.",
        concept_ids=("science",),
    )
    return StudySchedule(
        learner_id="learner-1",
        start_date=task.scheduled_date,
        end_date=task.scheduled_date,
        exam_date=None,
        days=(StudyDayPlan(task.scheduled_date, 30, (task,)),),
        unscheduled_work=(),
        generated_at=generated_at,
    )


def make_report(schedule, *, generated_at=NOW - timedelta(hours=1), recommended=0.75):
    adjustment = StudyTaskStrategyAdjustment(
        task_id="task-science",
        task_kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        execution_status=StudyTaskExecutionStatus.COMPLETED,
        evidence_kind=OutcomeEvidenceKind.CONCEPT_OVERLAP,
        source_trend=LearningTrend.DECLINING,
        action=StudyStrategyAction.REINFORCE_WEAK_AREA,
        current_priority_score=0.60,
        recommended_priority_score=recommended,
        suggested_revision_interval_days=1,
        baseline_attempted_count=10,
        follow_up_attempted_count=10,
        baseline_accuracy_percentage=70.0,
        follow_up_accuracy_percentage=60.0,
        delta_percentage_points=-10.0,
        reason="Recent linked accuracy declined.",
    )
    return AdaptiveStudyStrategyReport(
        learner_id=schedule.learner_id,
        schedule_id=schedule.schedule_id,
        assessment_session_id="assessment-1",
        assessed_at=NOW - timedelta(hours=2),
        adjustments=(adjustment,),
        generated_at=generated_at,
    )


def make_resulting_schedule(*, priority=0.75):
    when = NOW
    task = ScheduledStudyTask(
        task_id="next-science",
        kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        scheduled_date=NOW.date(),
        title="Reinforce science",
        estimated_minutes=20,
        priority_score=priority,
        reason="Adaptive schedule applied.",
        concept_ids=("science",),
    )
    return StudySchedule(
        learner_id="learner-1",
        start_date=when.date(),
        end_date=when.date(),
        exam_date=None,
        days=(StudyDayPlan(when.date(), 30, (task,)),),
        unscheduled_work=(),
        generated_at=when,
    )


def test_audit_service_stores_and_reloads_immutable_snapshots_idempotently():
    repository = InMemoryAuditRepository()
    service = AdaptiveStudyStrategyAuditService(repository)
    source = make_schedule()
    report = make_report(source)
    result = make_resulting_schedule()

    saved = service.record_applied_strategy(
        "audit-001",
        source_schedule=source,
        strategy_report=report,
        resulting_schedule=result,
    )
    retried = service.record_applied_strategy(
        "audit-001",
        source_schedule=source,
        strategy_report=report,
        resulting_schedule=result,
    )

    assert saved == retried
    assert service.get_audit("audit-001") == saved
    assert saved.source_schedule_id == source.schedule_id
    assert saved.resulting_schedule_id == result.schedule_id
    assert saved.strategy_report.adjustments[0].current_priority_score == 0.60
    assert saved.strategy_report.adjustments[0].recommended_priority_score == 0.75
    assert saved.resulting_schedule.days[0].tasks[0].priority_score == 0.75
    assert service.list_for_learner("learner-1") == (saved,)


def test_same_audit_id_with_different_result_is_a_conflict():
    repository = InMemoryAuditRepository()
    service = AdaptiveStudyStrategyAuditService(repository)
    source = make_schedule()
    report = make_report(source)
    service.record_applied_strategy(
        "audit-001",
        source_schedule=source,
        strategy_report=report,
        resulting_schedule=make_resulting_schedule(),
    )

    with pytest.raises(AdaptiveStudyStrategyAuditConflictError, match="different evidence"):
        service.record_applied_strategy(
            "audit-001",
            source_schedule=source,
            strategy_report=report,
            resulting_schedule=make_resulting_schedule(priority=0.50),
        )


def test_audit_requires_matching_source_report_and_result_learner():
    source = make_schedule()
    report = make_report(source)
    with pytest.raises(ValueError, match="fingerprint"):
        AdaptiveStudyStrategyAudit(
            audit_id="audit-wrong",
            source_schedule=source,
            strategy_report=make_report(make_schedule(priority=0.3)),
            resulting_schedule=make_resulting_schedule(),
            recorded_at=NOW,
        )

    wrong_learner_task = ScheduledStudyTask(
        task_id="other-task",
        kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        scheduled_date=NOW.date(),
        title="Other learner",
        estimated_minutes=10,
        priority_score=0.4,
        reason="Other learner plan.",
        concept_ids=("science",),
    )
    wrong_learner = StudySchedule(
        learner_id="learner-2",
        start_date=NOW.date(),
        end_date=NOW.date(),
        exam_date=None,
        days=(StudyDayPlan(NOW.date(), 30, (wrong_learner_task,)),),
        unscheduled_work=(),
        generated_at=NOW,
    )
    with pytest.raises(ValueError, match="learner does not match"):
        AdaptiveStudyStrategyAudit(
            audit_id="audit-wrong-learner",
            source_schedule=source,
            strategy_report=report,
            resulting_schedule=wrong_learner,
            recorded_at=NOW,
        )


def test_recorded_clock_cannot_precede_applied_schedule():
    source = make_schedule()
    with pytest.raises(ValueError, match="recorded_at cannot precede"):
        AdaptiveStudyStrategyAudit(
            audit_id="audit-old-clock",
            source_schedule=source,
            strategy_report=make_report(source),
            resulting_schedule=make_resulting_schedule(),
            recorded_at=NOW - timedelta(seconds=1),
        )
