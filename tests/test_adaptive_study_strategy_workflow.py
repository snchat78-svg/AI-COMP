from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai_comp.analysis.adaptive_study_strategy_audit import AdaptiveStudyStrategyAuditService
from ai_comp.analysis.adaptive_study_strategy_workflow import AdaptiveStudyStrategyWorkflow
from ai_comp.analysis.study_schedule_execution import StudyScheduleExecutionService
from ai_comp.domain.adaptive_study_strategy import (
    AdaptiveStudyStrategyReport,
    StudyStrategyAction,
    StudyTaskStrategyAdjustment,
)
from ai_comp.domain.adaptive_study_strategy_audit import AdaptiveStudyStrategyAuditConflictError
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_outcome_feedback import OutcomeEvidenceKind
from ai_comp.domain.study_schedule import ScheduledStudyTask, StudyDayPlan, StudySchedule, StudyTaskKind
from ai_comp.domain.study_schedule_execution import StudyTaskExecution, StudyTaskExecutionStatus


NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


class InMemoryExecutionRepository:
    def __init__(self):
        self.events = {}

    def get_event(self, event_id):
        return self.events.get(event_id)

    def save_event(self, event):
        self.events[event.event_id] = event

    def list_for_schedule(self, schedule_id, learner_id):
        return tuple(sorted(
            (event for event in self.events.values()
             if event.schedule_id == schedule_id and event.learner_id == learner_id),
            key=lambda event: (event.occurred_at, event.event_id),
        ))


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
        return audit

    def list_for_learner(self, learner_id, *, limit=50):
        return tuple(sorted(
            (row for row in self.rows.values() if row.learner_id == learner_id),
            key=lambda row: (row.recorded_at, row.audit_id),
            reverse=True,
        )[:limit])


def make_schedule():
    source = ScheduledStudyTask(
        task_id="task-science-source",
        kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        scheduled_date=TODAY - timedelta(days=1),
        title="Study science",
        estimated_minutes=20,
        priority_score=0.60,
        reason="Learner topic evidence.",
        concept_ids=("science",),
    )
    next_task = ScheduledStudyTask(
        task_id="task-science-next",
        kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        scheduled_date=TODAY + timedelta(days=1),
        title="Continue science",
        estimated_minutes=20,
        priority_score=0.40,
        reason="Unfinished next task.",
        concept_ids=("science",),
    )
    return StudySchedule(
        learner_id="learner-1",
        start_date=TODAY - timedelta(days=1),
        end_date=TODAY + timedelta(days=1),
        exam_date=None,
        days=(
            StudyDayPlan(TODAY - timedelta(days=1), 30, (source,)),
            StudyDayPlan(TODAY, 30, ()),
            StudyDayPlan(TODAY + timedelta(days=1), 30, (next_task,)),
        ),
        unscheduled_work=(),
        generated_at=NOW - timedelta(days=2),
    )


def make_strategy_report(schedule, *, generated_at=NOW - timedelta(hours=1), priority=0.80, interval=3):
    adjustment = StudyTaskStrategyAdjustment(
        task_id="task-science-source",
        task_kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        execution_status=StudyTaskExecutionStatus.COMPLETED,
        evidence_kind=OutcomeEvidenceKind.CONCEPT_OVERLAP,
        source_trend=LearningTrend.DECLINING,
        action=StudyStrategyAction.REINFORCE_WEAK_AREA,
        current_priority_score=0.60,
        recommended_priority_score=priority,
        suggested_revision_interval_days=interval,
        baseline_attempted_count=10,
        follow_up_attempted_count=10,
        baseline_accuracy_percentage=70.0,
        follow_up_accuracy_percentage=60.0,
        delta_percentage_points=-10.0,
        reason="Linked science performance declined.",
    )
    return AdaptiveStudyStrategyReport(
        learner_id=schedule.learner_id,
        schedule_id=schedule.schedule_id,
        assessment_session_id="assessment-26",
        assessed_at=NOW - timedelta(hours=2),
        adjustments=(adjustment,),
        generated_at=generated_at,
    )


def build_workflow():
    schedule = make_schedule()
    execution_repository = InMemoryExecutionRepository()
    execution_repository.save_event(StudyTaskExecution(
        event_id="completed-source-task",
        schedule_id=schedule.schedule_id,
        learner_id=schedule.learner_id,
        task_id="task-science-source",
        status=StudyTaskExecutionStatus.COMPLETED,
        occurred_at=NOW - timedelta(hours=3),
        actual_minutes=20,
    ))
    audit_repository = InMemoryAuditRepository()
    workflow = AdaptiveStudyStrategyWorkflow(
        StudyScheduleExecutionService(execution_repository),
        AdaptiveStudyStrategyAuditService(audit_repository),
    )
    return schedule, audit_repository, workflow


def test_workflow_replans_and_records_the_exact_resulting_schedule():
    schedule, repository, workflow = build_workflow()
    strategy = make_strategy_report(schedule)

    result = workflow.apply_and_record(
        "flow-audit-1",
        source_schedule=schedule,
        strategy_report=strategy,
        daily_minutes=30,
        start_date=TODAY,
        as_of=NOW,
    )

    task = next(task for day in result.schedule.days for task in day.tasks)
    assert task.title == "Continue science"
    assert task.priority_score == pytest.approx(0.80)
    assert task.scheduled_date == TODAY + timedelta(days=3)
    assert result.audit.source_schedule_id == schedule.schedule_id
    assert result.audit.resulting_schedule_id == result.schedule.schedule_id
    assert repository.get_audit("flow-audit-1") == result.audit


def test_same_audit_id_and_as_of_replay_idempotently():
    schedule, repository, workflow = build_workflow()
    strategy = make_strategy_report(schedule)

    first = workflow.apply_and_record(
        "flow-audit-retry",
        source_schedule=schedule,
        strategy_report=strategy,
        daily_minutes=30,
        start_date=TODAY,
        as_of=NOW,
    )
    second = workflow.apply_and_record(
        "flow-audit-retry",
        source_schedule=schedule,
        strategy_report=strategy,
        daily_minutes=30,
        start_date=TODAY,
        as_of=NOW,
    )

    assert second == first
    assert repository.list_for_learner("learner-1") == (first.audit,)


def test_workflow_rejects_non_deterministic_or_pre_report_clock():
    schedule, _, workflow = build_workflow()
    strategy = make_strategy_report(schedule)

    with pytest.raises(ValueError, match="timezone-aware"):
        workflow.apply_and_record(
            "bad-clock", source_schedule=schedule, strategy_report=strategy,
            daily_minutes=30, as_of=datetime(2026, 10, 9),
        )
    with pytest.raises(ValueError, match="cannot precede"):
        workflow.apply_and_record(
            "old-clock", source_schedule=schedule, strategy_report=strategy,
            daily_minutes=30, as_of=NOW - timedelta(hours=2),
        )


def test_workflow_does_not_persist_when_replan_validation_fails():
    schedule, repository, workflow = build_workflow()
    strategy = make_strategy_report(schedule)

    with pytest.raises(ValueError, match="daily_minutes"):
        workflow.apply_and_record(
            "failed-replan", source_schedule=schedule, strategy_report=strategy,
            daily_minutes=-1, as_of=NOW,
        )

    assert repository.list_for_learner("learner-1") == ()
