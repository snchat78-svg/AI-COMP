from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai_comp.analysis.study_schedule_execution import StudyScheduleExecutionService
from ai_comp.domain.adaptive_study_strategy import (
    AdaptiveStudyStrategyReport,
    StudyStrategyAction,
    StudyTaskStrategyAdjustment,
)
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_outcome_feedback import OutcomeEvidenceKind
from ai_comp.domain.study_schedule import (
    ScheduledStudyTask,
    StudyDayPlan,
    StudySchedule,
    StudyTaskKind,
)
from ai_comp.domain.study_schedule_execution import (
    StudyTaskExecution,
    StudyTaskExecutionStatus,
)


NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


class InMemoryExecutionRepository:
    def __init__(self) -> None:
        self.events: dict[str, StudyTaskExecution] = {}

    def get_event(self, event_id: str) -> StudyTaskExecution | None:
        return self.events.get(event_id)

    def save_event(self, event: StudyTaskExecution) -> None:
        existing = self.events.get(event.event_id)
        if existing is not None and existing != event:
            raise ValueError("conflicting event")
        self.events[event.event_id] = event

    def list_for_schedule(self, schedule_id: str, learner_id: str):
        return tuple(sorted(
            (event for event in self.events.values()
             if event.schedule_id == schedule_id and event.learner_id == learner_id),
            key=lambda event: (event.occurred_at, event.event_id),
        ))


def make_schedule(*, next_priority: float = 0.40) -> StudySchedule:
    source = ScheduledStudyTask(
        task_id="task-science-source",
        kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        scheduled_date=TODAY - timedelta(days=1),
        title="Study science basics",
        estimated_minutes=20,
        priority_score=0.60,
        reason="Evidence-backed learner topic.",
        concept_ids=("science",),
    )
    next_task = ScheduledStudyTask(
        task_id="task-science-next",
        kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        scheduled_date=TODAY + timedelta(days=1),
        title="Continue science practice",
        estimated_minutes=20,
        priority_score=next_priority,
        reason="Planned continuation.",
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


def make_strategy_report(
    schedule: StudySchedule,
    *,
    action: StudyStrategyAction = StudyStrategyAction.REINFORCE_WEAK_AREA,
    priority: float = 0.80,
    interval: int | None = 3,
    generated_at: datetime = NOW + timedelta(minutes=1),
) -> AdaptiveStudyStrategyReport:
    limited = action is StudyStrategyAction.COLLECT_MORE_EVIDENCE
    adjustment = StudyTaskStrategyAdjustment(
        task_id="task-science-source",
        task_kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        execution_status=StudyTaskExecutionStatus.COMPLETED,
        evidence_kind=(
            OutcomeEvidenceKind.NO_RELATED_EVIDENCE
            if limited else OutcomeEvidenceKind.CONCEPT_OVERLAP
        ),
        source_trend=(
            LearningTrend.INSUFFICIENT_DATA
            if limited else LearningTrend.DECLINING
        ),
        action=action,
        current_priority_score=0.60,
        recommended_priority_score=0.60 if limited else priority,
        suggested_revision_interval_days=None if limited else interval,
        baseline_attempted_count=1 if limited else 10,
        follow_up_attempted_count=1 if limited else 10,
        baseline_accuracy_percentage=None if limited else 70.0,
        follow_up_accuracy_percentage=None if limited else 60.0,
        delta_percentage_points=None if limited else -10.0,
        reason="Evidence-linked test strategy.",
    )
    return AdaptiveStudyStrategyReport(
        learner_id=schedule.learner_id,
        schedule_id=schedule.schedule_id,
        assessment_session_id="assessment-1",
        assessed_at=NOW,
        adjustments=(adjustment,),
        generated_at=generated_at,
    )


def complete_source_task(schedule: StudySchedule, repository: InMemoryExecutionRepository):
    repository.save_event(StudyTaskExecution(
        event_id="source-completed",
        schedule_id=schedule.schedule_id,
        learner_id=schedule.learner_id,
        task_id="task-science-source",
        status=StudyTaskExecutionStatus.COMPLETED,
        occurred_at=NOW - timedelta(hours=1),
        actual_minutes=20,
    ))


def next_schedule_tasks(schedule: StudySchedule):
    return tuple(task for day in schedule.days for task in day.tasks)


def test_strategy_priority_and_revision_interval_flow_into_next_schedule():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    complete_source_task(schedule, repository)
    report = make_strategy_report(schedule)

    revised = StudyScheduleExecutionService(repository).replan(
        schedule,
        daily_minutes=30,
        start_date=TODAY,
        as_of=NOW + timedelta(minutes=2),
        strategy_report=report,
    )

    tasks = next_schedule_tasks(revised)
    assert len(tasks) == 1
    assert tasks[0].title == "Continue science practice"
    assert tasks[0].priority_score == pytest.approx(0.80)
    assert tasks[0].scheduled_date == TODAY + timedelta(days=3)
    assert "Adaptive strategy applied" in tasks[0].reason
    assert revised.start_date == TODAY
    assert revised.end_date == TODAY + timedelta(days=3)


def test_insufficient_evidence_does_not_change_priority_or_delay_schedule():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    complete_source_task(schedule, repository)
    report = make_strategy_report(
        schedule,
        action=StudyStrategyAction.COLLECT_MORE_EVIDENCE,
        interval=None,
    )

    revised = StudyScheduleExecutionService(repository).replan(
        schedule,
        daily_minutes=30,
        start_date=TODAY,
        as_of=NOW + timedelta(minutes=2),
        strategy_report=report,
    )

    tasks = next_schedule_tasks(revised)
    assert len(tasks) == 1
    assert tasks[0].priority_score == pytest.approx(0.40)
    assert tasks[0].scheduled_date == TODAY + timedelta(days=1)
    assert "Adaptive strategy applied" not in tasks[0].reason


def test_strategy_report_must_match_learner_and_original_schedule():
    schedule = make_schedule()
    report = make_strategy_report(schedule)
    other = make_schedule(next_priority=0.35)

    with pytest.raises(ValueError, match="fingerprint does not match"):
        StudyScheduleExecutionService(InMemoryExecutionRepository()).replan(
            other,
            daily_minutes=30,
            as_of=NOW + timedelta(minutes=2),
            strategy_report=report,
        )


def test_replanning_clock_cannot_precede_strategy_report_generation():
    schedule = make_schedule()
    report = make_strategy_report(schedule)

    with pytest.raises(ValueError, match="cannot precede strategy report generation"):
        StudyScheduleExecutionService(InMemoryExecutionRepository()).replan(
            schedule,
            daily_minutes=30,
            as_of=NOW,
            strategy_report=report,
        )


def test_replan_without_strategy_report_keeps_legacy_contract():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    complete_source_task(schedule, repository)

    revised = StudyScheduleExecutionService(repository).replan(
        schedule,
        daily_minutes=30,
        start_date=TODAY,
        as_of=NOW + timedelta(minutes=2),
    )

    tasks = next_schedule_tasks(revised)
    assert len(tasks) == 1
    assert tasks[0].priority_score == pytest.approx(0.40)
    assert tasks[0].scheduled_date == TODAY + timedelta(days=1)
