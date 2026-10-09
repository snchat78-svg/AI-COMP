from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta, datetime
from enum import Enum


class StudyTaskKind(str, Enum):
    REVIEW_DUE_REVISION = "REVIEW_DUE_REVISION"
    REVIEW_PREVIOUS_MISTAKES = "REVIEW_PREVIOUS_MISTAKES"
    STUDY_WEAK_TOPIC = "STUDY_WEAK_TOPIC"
    PRACTICE_QUESTIONS = "PRACTICE_QUESTIONS"


@dataclass(frozen=True)
class StudySchedulePolicy:
    """Configurable time estimates and exam-proximity weighting for schedules."""

    review_minutes_per_question: int = 4
    practice_minutes_per_question: int = 3
    weak_topic_minutes: int = 25
    minimum_block_minutes: int = 5
    maximum_block_minutes: int = 45
    exam_urgency_window_days: int = 5
    exam_urgency_bonus: float = 0.15

    def __post_init__(self) -> None:
        for name in (
            "review_minutes_per_question",
            "practice_minutes_per_question",
            "weak_topic_minutes",
            "minimum_block_minutes",
            "maximum_block_minutes",
        ):
            value = getattr(self, name)
            if value < 1:
                raise ValueError(f"{name} must be positive")
        if self.minimum_block_minutes > self.maximum_block_minutes:
            raise ValueError("minimum block cannot exceed maximum block")
        if (
            self.review_minutes_per_question > self.maximum_block_minutes
            or self.practice_minutes_per_question > self.maximum_block_minutes
        ):
            raise ValueError("per-question estimates cannot exceed maximum block")
        if self.exam_urgency_window_days < 0:
            raise ValueError("exam urgency window must be non-negative")
        if not 0.0 <= self.exam_urgency_bonus <= 1.0:
            raise ValueError("exam urgency bonus must be between 0 and 1")


@dataclass(frozen=True)
class ScheduledStudyTask:
    task_id: str
    kind: StudyTaskKind
    scheduled_date: date
    title: str
    estimated_minutes: int
    priority_score: float
    reason: str
    concept_ids: tuple[str, ...] = ()
    question_ids: tuple[str, ...] = ()
    deadline_date: date | None = None

    def __post_init__(self) -> None:
        for name in ("task_id", "title", "reason"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.estimated_minutes < 1:
            raise ValueError("estimated_minutes must be positive")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")
        if not self.concept_ids and not self.question_ids:
            raise ValueError("a scheduled task must identify concepts or questions")
        for name, values in (
            ("concept_ids", self.concept_ids),
            ("question_ids", self.question_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must be unique")
            if any(not value.strip() for value in values):
                raise ValueError(f"{name} must not contain empty IDs")


@dataclass(frozen=True)
class UnscheduledStudyWork:
    work_id: str
    kind: StudyTaskKind
    title: str
    remaining_minutes: int
    priority_score: float
    reason: str
    unscheduled_reason: str
    concept_ids: tuple[str, ...] = ()
    question_ids: tuple[str, ...] = ()
    deadline_date: date | None = None

    def __post_init__(self) -> None:
        for name in ("work_id", "title", "reason", "unscheduled_reason"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.remaining_minutes < 1:
            raise ValueError("remaining_minutes must be positive")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")
        if not self.concept_ids and not self.question_ids:
            raise ValueError("unscheduled work must identify concepts or questions")
        if len(self.concept_ids) != len(set(self.concept_ids)):
            raise ValueError("concept_ids must be unique")
        if len(self.question_ids) != len(set(self.question_ids)):
            raise ValueError("question_ids must be unique")


@dataclass(frozen=True)
class StudyDayPlan:
    study_date: date
    available_minutes: int
    tasks: tuple[ScheduledStudyTask, ...]

    def __post_init__(self) -> None:
        if self.available_minutes < 0:
            raise ValueError("available_minutes must be non-negative")
        if any(task.scheduled_date != self.study_date for task in self.tasks):
            raise ValueError("day plan contains a task scheduled for another date")
        if self.scheduled_minutes > self.available_minutes:
            raise ValueError("scheduled work exceeds daily availability")
        task_ids = tuple(task.task_id for task in self.tasks)
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("task IDs must be unique within a day")
        question_ids = tuple(
            question_id for task in self.tasks for question_id in task.question_ids
        )
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("a question cannot be scheduled twice in one day")

    @property
    def scheduled_minutes(self) -> int:
        return sum(task.estimated_minutes for task in self.tasks)


@dataclass(frozen=True)
class StudySchedule:
    """A bounded, learner-scoped schedule; unallocated work is explicit."""

    learner_id: str
    start_date: date
    end_date: date
    exam_date: date | None
    days: tuple[StudyDayPlan, ...]
    unscheduled_work: tuple[UnscheduledStudyWork, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot precede start_date")
        if self.exam_date is not None and self.exam_date < self.start_date:
            raise ValueError("exam_date cannot precede start_date")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")

        expected_dates = tuple(
            self.start_date + timedelta(days=index)
            for index in range((self.end_date - self.start_date).days + 1)
        )
        if tuple(day.study_date for day in self.days) != expected_dates:
            raise ValueError("day plans must cover every date in the schedule window")
        if self.exam_date is not None and any(
            day.tasks for day in self.days if day.study_date == self.exam_date
        ):
            raise ValueError("study tasks cannot be scheduled on the exam date")

        task_ids = tuple(task.task_id for day in self.days for task in day.tasks)
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("scheduled task IDs must be unique")
        scheduled_questions = tuple(
            question_id
            for day in self.days
            for task in day.tasks
            for question_id in task.question_ids
        )
        if len(scheduled_questions) != len(set(scheduled_questions)):
            raise ValueError("a question cannot be scheduled more than once")
        unscheduled_ids = tuple(item.work_id for item in self.unscheduled_work)
        if len(unscheduled_ids) != len(set(unscheduled_ids)):
            raise ValueError("unscheduled work IDs must be unique")
        unallocated_questions = {
            question_id
            for item in self.unscheduled_work
            for question_id in item.question_ids
        }
        if set(scheduled_questions) & unallocated_questions:
            raise ValueError("a question cannot be both scheduled and unallocated")

    @property
    def total_available_minutes(self) -> int:
        return sum(day.available_minutes for day in self.days)

    @property
    def scheduled_minutes(self) -> int:
        return sum(day.scheduled_minutes for day in self.days)

    @property
    def remaining_work_minutes(self) -> int:
        return sum(item.remaining_minutes for item in self.unscheduled_work)


__all__ = [
    "ScheduledStudyTask",
    "StudyDayPlan",
    "StudySchedule",
    "StudySchedulePolicy",
    "StudyTaskKind",
    "UnscheduledStudyWork",
]
