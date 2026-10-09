from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.study_schedule_execution import (
    StudyTaskExecution,
    StudyTaskExecutionConflictError,
    StudyTaskExecutionRepository,
    StudyTaskExecutionStatus,
)


class PostgresStudyTaskExecutionRepository(StudyTaskExecutionRepository):
    """Append-only PostgreSQL store for idempotent study-task execution events."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def get_event(self, event_id: str) -> StudyTaskExecution | None:
        try:
            row = self._connection.execute(
                """
                SELECT event_id, schedule_id, learner_id, task_id, status,
                       occurred_at, actual_minutes, remaining_minutes,
                       postponed_until, completed_question_ids, note
                FROM study_schedule_task_events
                WHERE event_id = %s
                """,
                (event_id,),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to read study schedule execution event") from exc
        return None if row is None else self._row(row)

    def save_event(self, event: StudyTaskExecution) -> None:
        try:
            with self._connection.transaction():
                inserted = self._connection.execute(
                    """
                    INSERT INTO study_schedule_task_events (
                        event_id, schedule_id, learner_id, task_id, status,
                        occurred_at, actual_minutes, remaining_minutes,
                        postponed_until, completed_question_ids, note
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (event_id) DO NOTHING
                    RETURNING event_id
                    """,
                    (
                        event.event_id,
                        event.schedule_id,
                        event.learner_id,
                        event.task_id,
                        event.status.value,
                        event.occurred_at,
                        event.actual_minutes,
                        event.remaining_minutes,
                        event.postponed_until,
                        list(event.completed_question_ids),
                        event.note,
                    ),
                ).fetchone()
                if inserted is None:
                    existing = self.get_event(event.event_id)
                    if existing != event:
                        raise StudyTaskExecutionConflictError(
                            "event_id already exists with different execution data"
                        )
        except StudyTaskExecutionConflictError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to persist study schedule execution event") from exc

    def list_for_schedule(
        self,
        schedule_id: str,
        learner_id: str,
    ) -> tuple[StudyTaskExecution, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT event_id, schedule_id, learner_id, task_id, status,
                       occurred_at, actual_minutes, remaining_minutes,
                       postponed_until, completed_question_ids, note
                FROM study_schedule_task_events
                WHERE schedule_id = %s AND learner_id = %s
                ORDER BY occurred_at, event_id
                """,
                (schedule_id, learner_id),
            ).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list study schedule execution events") from exc
        return tuple(self._row(row) for row in rows)

    @staticmethod
    def _row(row: Sequence[object]) -> StudyTaskExecution:
        return StudyTaskExecution(
            event_id=str(row[0]),
            schedule_id=str(row[1]).strip(),
            learner_id=str(row[2]),
            task_id=str(row[3]),
            status=StudyTaskExecutionStatus(str(row[4])),
            occurred_at=row[5],
            actual_minutes=int(row[6]),
            remaining_minutes=None if row[7] is None else int(row[7]),
            postponed_until=row[8],
            completed_question_ids=tuple(str(value) for value in (row[9] or [])),
            note=None if row[10] is None else str(row[10]),
        )


__all__ = ["PostgresStudyTaskExecutionRepository"]
