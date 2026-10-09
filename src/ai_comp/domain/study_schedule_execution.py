from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Protocol


class StudyTaskExecutionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"
    POSTPONED = "POSTPONED"


@dataclass(frozen=True)
class StudyTaskExecution:
    """Immutable execution event; event_id is the idempotency key."""

    event_id: str
    schedule_id: str
    learner_id: str
    task_id: str
    status: StudyTaskExecutionStatus
    occurred_at: datetime
    actual_minutes: int = 0
    remaining_minutes: int | None = None
    postponed_until: date | None = None
    completed_question_ids: tuple[str, ...] = ()
    note: str | None = None

    def __post_init__(self) -> None:
        for name in ("event_id", "schedule_id", "learner_id", "task_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if len(self.schedule_id) != 64:
            raise ValueError("schedule_id must be a 64-character schedule fingerprint")
        try:
            int(self.schedule_id, 16)
        except ValueError as exc:
            raise ValueError("schedule_id must be hexadecimal") from exc
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        if isinstance(self.actual_minutes, bool) or not isinstance(self.actual_minutes, int) or self.actual_minutes < 0:
            raise ValueError("actual_minutes must be a non-negative integer")
        if self.status is StudyTaskExecutionStatus.PARTIAL:
            if (
                isinstance(self.remaining_minutes, bool)
                or not isinstance(self.remaining_minutes, int)
                or self.remaining_minutes < 1
            ):
                raise ValueError("partial execution requires positive remaining_minutes")
        elif self.remaining_minutes is not None:
            raise ValueError("remaining_minutes is only valid for partial execution")
        if self.status is StudyTaskExecutionStatus.POSTPONED:
            if self.postponed_until is None:
                raise ValueError("postponed execution requires postponed_until")
        elif self.postponed_until is not None:
            raise ValueError("postponed_until is only valid for postponed execution")
        if self.status is not StudyTaskExecutionStatus.PARTIAL and self.completed_question_ids:
            raise ValueError("completed_question_ids are only valid for partial execution")
        if len(self.completed_question_ids) != len(set(self.completed_question_ids)):
            raise ValueError("completed_question_ids must be unique")
        if any(not value.strip() for value in self.completed_question_ids):
            raise ValueError("completed_question_ids must not contain empty IDs")
        if self.note is not None and not self.note.strip():
            raise ValueError("note must not be blank when supplied")


class StudyTaskExecutionConflictError(RuntimeError):
    """Raised when an idempotency key is reused with different event data."""


class StudyTaskExecutionRepository(Protocol):
    def get_event(self, event_id: str) -> StudyTaskExecution | None: ...
    def save_event(self, event: StudyTaskExecution) -> None: ...
    def list_for_schedule(
        self,
        schedule_id: str,
        learner_id: str,
    ) -> tuple[StudyTaskExecution, ...]: ...


__all__ = [
    "StudyTaskExecution",
    "StudyTaskExecutionConflictError",
    "StudyTaskExecutionRepository",
    "StudyTaskExecutionStatus",
]
