from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from ai_comp.analysis.study_schedule_execution import StudyScheduleExecutionService
from ai_comp.domain.study_schedule import (
    ScheduledStudyTask, StudyDayPlan, StudySchedule, StudyTaskKind,
    UnscheduledStudyWork,
)
from ai_comp.domain.study_schedule_execution import (
    StudyTaskExecution, StudyTaskExecutionConflictError, StudyTaskExecutionStatus,
)


NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


class InMemoryExecutionRepository:
    def __init__(self) -> None:
        self.events: dict[str, StudyTaskExecution] = {}

    def get_event(self, event_id: str) -> StudyTaskExecution | None:
        return self.events.get(event_id)

    def save_event(self, event: StudyTaskExecution) -> None:
        old = self.events.get(event.event_id)
        if old is not None and old != event:
            raise StudyTaskExecutionConflictError(
                "event_id already exists with different execution data"
            )
        self.events[event.event_id] = event

    def list_for_schedule(
        self, schedule_id: str, learner_id: str
    ) -> tuple[StudyTaskExecution, ...]:
        return tuple(sorted(
            (item for item in self.events.values()
             if item.schedule_id == schedule_id and item.learner_id == learner_id),
            key=lambda item: (item.occurred_at, item.event_id),
        ))


def make_schedule() -> StudySchedule:
    yesterday = TODAY - timedelta(days=1)
    tomorrow = TODAY + timedelta(days=1)
    day_tasks = (
        ScheduledStudyTask(
            task_id="task-review", kind=StudyTaskKind.REVIEW_PREVIOUS_MISTAKES,
            scheduled_date=yesterday, title="Review old mistakes",
            estimated_minutes=8, priority_score=0.95, reason="Previous wrong answers.",
            concept_ids=("science",), question_ids=("q1", "q2"),
            deadline_date=TODAY + timedelta(days=2),
        ),
        ScheduledStudyTask(
            task_id="task-topic", kind=StudyTaskKind.STUDY_WEAK_TOPIC,
            scheduled_date=TODAY, title="Study science",
            estimated_minutes=25, priority_score=0.90, reason="Weak-topic evidence.",
            concept_ids=("science",),
        ),
        ScheduledStudyTask(
            task_id="task-practice", kind=StudyTaskKind.PRACTICE_QUESTIONS,
            scheduled_date=tomorrow, title="Practice question",
            estimated_minutes=3, priority_score=0.80, reason="Accepted question.",
            concept_ids=("geography",), question_ids=("q3",),
            deadline_date=TODAY + timedelta(days=2),
        ),
    )
    return StudySchedule(
        learner_id="learner-1",
        start_date=yesterday,
        end_date=tomorrow,
        exam_date=TODAY + timedelta(days=3),
        days=(
            StudyDayPlan(yesterday, 30, (day_tasks[0],)),
            StudyDayPlan(TODAY, 30, (day_tasks[1],)),
            StudyDayPlan(tomorrow, 30, (day_tasks[2],)),
        ),
        unscheduled_work=(
            UnscheduledStudyWork(
                work_id="work-extra", kind=StudyTaskKind.PRACTICE_QUESTIONS,
                title="Extra practice", remaining_minutes=3, priority_score=0.5,
                reason="Selected from the existing plan.",
                unscheduled_reason="Previous capacity was insufficient.",
                concept_ids=("history",), question_ids=("q4",),
                deadline_date=TODAY + timedelta(days=2),
            ),
        ),
        generated_at=NOW - timedelta(days=1),
    )


def event(
    schedule: StudySchedule,
    *,
    event_id: str,
    task_id: str,
    status: StudyTaskExecutionStatus,
    minutes: int = 0,
    remaining: int | None = None,
    postponed_until: date | None = None,
    completed: tuple[str, ...] = (),
    occurred_at: datetime = NOW,
) -> StudyTaskExecution:
    return StudyTaskExecution(
        event_id=event_id,
        schedule_id=schedule.schedule_id,
        learner_id=schedule.learner_id,
        task_id=task_id,
        status=status,
        occurred_at=occurred_at,
        actual_minutes=minutes,
        remaining_minutes=remaining,
        postponed_until=postponed_until,
        completed_question_ids=completed,
    )


def test_schedule_has_stable_content_fingerprint_and_events_are_idempotent():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    service = StudyScheduleExecutionService(repository)
    recorded = event(
        schedule, event_id="event-complete", task_id="task-topic",
        status=StudyTaskExecutionStatus.COMPLETED, minutes=22,
    )

    assert schedule.schedule_id == make_schedule().schedule_id
    assert service.record_execution(schedule, recorded) == recorded
    assert service.record_execution(schedule, recorded) == recorded
    assert len(repository.events) == 1

    with pytest.raises(StudyTaskExecutionConflictError, match="different execution data"):
        service.record_execution(schedule, replace(recorded, actual_minutes=23))


def test_partial_progress_is_monotonic_and_terminal_tasks_cannot_be_reopened():
    schedule = make_schedule()
    service = StudyScheduleExecutionService(InMemoryExecutionRepository())
    first = event(
        schedule, event_id="partial-1", task_id="task-review",
        status=StudyTaskExecutionStatus.PARTIAL, minutes=4,
        remaining=4, completed=("q1",),
    )
    second_bad = event(
        schedule, event_id="partial-2", task_id="task-review",
        status=StudyTaskExecutionStatus.PARTIAL, minutes=2,
        remaining=2, completed=(),
    )
    service.record_execution(schedule, first)
    with pytest.raises(ValueError, match="cannot forget completed questions"):
        service.record_execution(schedule, second_bad)

    completed = event(
        schedule, event_id="completed-topic", task_id="task-topic",
        status=StudyTaskExecutionStatus.COMPLETED, minutes=20,
    )
    service.record_execution(schedule, completed)
    with pytest.raises(ValueError, match="terminal execution status"):
        service.record_execution(
            schedule,
            event(
                schedule, event_id="second-completion", task_id="task-topic",
                status=StudyTaskExecutionStatus.COMPLETED, minutes=1,
            ),
        )


def test_replan_removes_completed_work_carries_partial_progress_and_honors_postpone():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    service = StudyScheduleExecutionService(repository)
    service.record_execution(schedule, event(
        schedule, event_id="review-partial", task_id="task-review",
        status=StudyTaskExecutionStatus.PARTIAL, minutes=4,
        remaining=4, completed=("q1",),
    ))
    service.record_execution(schedule, event(
        schedule, event_id="topic-complete", task_id="task-topic",
        status=StudyTaskExecutionStatus.COMPLETED, minutes=22,
    ))
    postponed_date = TODAY + timedelta(days=2)
    service.record_execution(schedule, event(
        schedule, event_id="practice-postpone", task_id="task-practice",
        status=StudyTaskExecutionStatus.POSTPONED, postponed_until=postponed_date,
    ))

    next_schedule = service.replan(
        schedule,
        daily_minutes=20,
        first_day_minutes=7,
        start_date=TODAY,
        as_of=NOW,
    )
    tasks = tuple(task for day in next_schedule.days for task in day.tasks)
    scheduled_question_ids = {
        question_id for task in tasks for question_id in task.question_ids
    }
    dates_by_question = {
        question_id: task.scheduled_date
        for task in tasks for question_id in task.question_ids
    }

    assert next_schedule.start_date == TODAY
    assert next_schedule.end_date == postponed_date
    assert "q1" not in scheduled_question_ids
    assert "q2" in scheduled_question_ids
    assert "q3" in scheduled_question_ids
    assert "q4" in scheduled_question_ids
    assert dates_by_question["q3"] == postponed_date
    assert all("task-topic" not in task.task_id for task in tasks)
    assert all(day.scheduled_minutes <= day.available_minutes for day in next_schedule.days)
    assert sum(day.scheduled_minutes for day in next_schedule.days) <= next_schedule.total_available_minutes


def test_skipped_work_is_not_requeued_and_exam_day_has_no_tasks():
    schedule = make_schedule()
    service = StudyScheduleExecutionService(InMemoryExecutionRepository())
    service.record_execution(schedule, event(
        schedule, event_id="topic-skipped", task_id="task-topic",
        status=StudyTaskExecutionStatus.SKIPPED,
    ))
    next_schedule = service.replan(
        schedule,
        daily_minutes=30,
        start_date=TODAY,
        end_date=TODAY + timedelta(days=3),
        as_of=NOW,
    )
    tasks = tuple(task for day in next_schedule.days for task in day.tasks)

    assert not any(task.title == "Study science" for task in tasks)
    assert next_schedule.days[-1].study_date == next_schedule.exam_date
    assert next_schedule.days[-1].available_minutes == 0
    assert next_schedule.days[-1].tasks == ()


def test_execution_rejects_wrong_learner_schedule_and_question_scope():
    schedule = make_schedule()
    service = StudyScheduleExecutionService(InMemoryExecutionRepository())
    good = event(
        schedule, event_id="scope-check", task_id="task-review",
        status=StudyTaskExecutionStatus.PARTIAL, remaining=4,
        completed=("q1",),
    )

    with pytest.raises(ValueError, match="learner does not match"):
        service.record_execution(schedule, replace(good, learner_id="other-learner"))
    with pytest.raises(ValueError, match="fingerprint does not match"):
        service.record_execution(schedule, replace(good, schedule_id="0" * 64))
    with pytest.raises(ValueError, match="must belong to the scheduled task"):
        service.record_execution(schedule, replace(good, completed_question_ids=("not-in-task",)))


def test_event_contract_validates_partial_postpone_and_timestamps():
    schedule = make_schedule()
    with pytest.raises(ValueError, match="positive remaining_minutes"):
        event(
            schedule, event_id="invalid-partial", task_id="task-review",
            status=StudyTaskExecutionStatus.PARTIAL,
        )
    with pytest.raises(ValueError, match="requires postponed_until"):
        event(
            schedule, event_id="invalid-postpone", task_id="task-review",
            status=StudyTaskExecutionStatus.POSTPONED,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        event(
            schedule, event_id="invalid-time", task_id="task-review",
            status=StudyTaskExecutionStatus.COMPLETED,
            occurred_at=datetime(2026, 10, 9),
        )


def test_replan_rejects_invalid_capacity_window_and_past_postpone():
    schedule = make_schedule()
    service = StudyScheduleExecutionService(InMemoryExecutionRepository())
    with pytest.raises(ValueError, match="daily_minutes"):
        service.replan(schedule, daily_minutes=-1, as_of=NOW)
    with pytest.raises(ValueError, match="cannot precede replanning start"):
        service.replan(
            schedule, daily_minutes=30, start_date=TODAY,
            exam_date=TODAY - timedelta(days=1), as_of=NOW,
        )
    with pytest.raises(ValueError, match="cannot exceed 366"):
        service.replan(
            schedule, daily_minutes=30, start_date=TODAY,
            end_date=TODAY + timedelta(days=366), as_of=NOW,
        )
