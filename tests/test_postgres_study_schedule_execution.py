from __future__ import annotations

import os
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner
from ai_comp.database.postgres_study_schedule_execution import PostgresStudyTaskExecutionRepository
from ai_comp.domain.study_schedule_execution import (
    StudyTaskExecution, StudyTaskExecutionConflictError, StudyTaskExecutionStatus,
)


pytestmark = pytest.mark.integration


def database_url() -> str:
    value = os.getenv("AI_COMP_DATABASE_URL", "").strip()
    if not value:
        pytest.skip("AI_COMP_DATABASE_URL is not configured")
    return value


def test_postgres_execution_events_round_trip_and_are_idempotent():
    with connect_postgres(database_url()) as connection:
        migrations = Path(__file__).resolve().parents[1] / "database" / "migrations"
        MigrationRunner(migrations).apply(connection)
        repo = PostgresStudyTaskExecutionRepository(connection)
        event_id = f"study-event-{uuid4()}"
        schedule_id = "a" * 64
        event = StudyTaskExecution(
            event_id=event_id,
            schedule_id=schedule_id,
            learner_id="phase-6-21-db-learner",
            task_id="scheduled-task-1",
            status=StudyTaskExecutionStatus.PARTIAL,
            occurred_at=datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc),
            actual_minutes=5,
            remaining_minutes=7,
            completed_question_ids=("question-one",),
            note="saved in integration test",
        )

        repo.save_event(event)
        repo.save_event(event)
        assert repo.get_event(event_id) == event
        assert repo.list_for_schedule(schedule_id, event.learner_id) == (event,)

        conflict = StudyTaskExecution(
            event_id=event_id,
            schedule_id=schedule_id,
            learner_id=event.learner_id,
            task_id=event.task_id,
            status=StudyTaskExecutionStatus.PARTIAL,
            occurred_at=event.occurred_at,
            actual_minutes=6,
            remaining_minutes=7,
            completed_question_ids=("question-one",),
            note="conflicting payload",
        )
        with pytest.raises(StudyTaskExecutionConflictError, match="different execution data"):
            repo.save_event(conflict)
