from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner
from ai_comp.database.postgres_learning_history import PostgresLearningHistoryRepository
from ai_comp.domain.learning_history import LongTermPerformanceBand


pytestmark = pytest.mark.integration


def database_url() -> str:
    value = os.getenv("AI_COMP_DATABASE_URL", "").strip()
    if not value:
        pytest.skip("AI_COMP_DATABASE_URL is not configured")
    return value


def make_analysis():
    from ai_comp.domain.test_analysis import (
        PerformanceBand,
        QuestionOutcome,
        TestAnalysis,
        TopicPerformance,
        WeakTopic,
    )
    return TestAnalysis(
        test_id="pg-test",
        session_id="pg-session",
        total_questions=2,
        attempted_questions=2,
        correct_answers=0,
        incorrect_answers=2,
        unattempted_questions=0,
        raw_score=-0.5,
        percentage=-25.0,
        accuracy=0.0,
        outcomes=(
            QuestionOutcome(
                question_id="q1",
                concept_ids=("science",),
                selected_option_key="A",
                correct_option_key="B",
                attempted=True,
                correct=False,
                difficulty="EASY",
            ),
            QuestionOutcome(
                question_id="q2",
                concept_ids=("history",),
                selected_option_key="A",
                correct_option_key="B",
                attempted=True,
                correct=False,
                difficulty="EASY",
            ),
        ),
        topic_performance=(
            TopicPerformance(
                concept_id="science",
                question_count=1,
                attempted_count=1,
                correct_count=0,
                incorrect_count=1,
                unattempted_count=0,
                accuracy=0.0,
                performance=PerformanceBand.WEAK,
            ),
            TopicPerformance(
                concept_id="history",
                question_count=1,
                attempted_count=1,
                correct_count=0,
                incorrect_count=1,
                unattempted_count=0,
                accuracy=0.0,
                performance=PerformanceBand.WEAK,
            ),
        ),
        weak_topics=(
            WeakTopic(
                concept_id="science",
                priority_score=1.0,
                accuracy=0.0,
                attempted_count=1,
                question_count=1,
                reason="कम accuracy",
            ),
            WeakTopic(
                concept_id="history",
                priority_score=1.0,
                accuracy=0.0,
                attempted_count=1,
                question_count=1,
                reason="कम accuracy",
            ),
        ),
    )


def test_postgres_learning_history_round_trip_and_idempotency():
    dsn = database_url()
    with connect_postgres(dsn) as connection:
        migrations_dir = __import__("pathlib").Path(__file__).resolve().parents[1] / "database" / "migrations"
        MigrationRunner(migrations_dir).apply(connection)
        repo = PostgresLearningHistoryRepository(connection)
        service = LearningHistoryService(repo)
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        analysis = make_analysis()
        service.record_analysis("postgres-learner", analysis, completed_at=now)
        service.record_analysis("postgres-learner", analysis, completed_at=now)

        attempts = repo.list_attempts("postgres-learner")
        assert len(attempts) == 1
        topics = repo.list_topic_attempts("postgres-learner")
        assert {item.concept_id for item in topics} == {"science", "history"}

        history = service.history("postgres-learner", generated_at=now)
        science = next(
            item for item in history.topic_performance
            if item.concept_id == "science"
        )
        assert science.test_count == 1
        assert science.performance is LongTermPerformanceBand.WEAK
        assert repo.get_attempt("postgres-learner", "unknown-session") is None
