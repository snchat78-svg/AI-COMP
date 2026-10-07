from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.analysis.question_learning import QuestionLearningHistoryService
from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner
from ai_comp.database.postgres_learning_history import PostgresLearningHistoryRepository
from ai_comp.database.postgres_question_learning import PostgresQuestionLearningHistoryRepository
from ai_comp.domain.test_analysis import (
    PerformanceBand,
    QuestionOutcome,
    TestAnalysis,
    TopicPerformance,
    WeakTopic,
)


pytestmark = pytest.mark.integration


def database_url() -> str:
    value = os.getenv("AI_COMP_DATABASE_URL", "").strip()
    if not value:
        pytest.skip("AI_COMP_DATABASE_URL is not configured")
    return value


def analysis():
    topic = TopicPerformance(
        concept_id="question-learning-science",
        question_count=1,
        attempted_count=1,
        correct_count=0,
        incorrect_count=1,
        unattempted_count=0,
        accuracy=0.0,
        performance=PerformanceBand.WEAK,
    )
    return TestAnalysis(
        test_id="ql-test",
        session_id="ql-session",
        total_questions=1,
        attempted_questions=1,
        correct_answers=0,
        incorrect_answers=1,
        unattempted_questions=0,
        raw_score=-0.25,
        percentage=-25.0,
        accuracy=0.0,
        outcomes=(
            QuestionOutcome(
                question_id="ql-q1",
                concept_ids=("question-learning-science",),
                selected_option_key="A",
                correct_option_key="B",
                attempted=True,
                correct=False,
                difficulty="EASY",
            ),
        ),
        topic_performance=(topic,),
        weak_topics=(
            WeakTopic(
                concept_id="question-learning-science",
                priority_score=1.0,
                accuracy=0.0,
                attempted_count=1,
                question_count=1,
                reason="weak",
            ),
        ),
    )


def test_postgres_question_history_round_trip_and_idempotency():
    dsn = database_url()
    with connect_postgres(dsn) as connection:
        migrations_dir = Path(__file__).resolve().parents[1] / "database" / "migrations"
        MigrationRunner(migrations_dir).apply(connection)

        learner_repo = PostgresLearningHistoryRepository(connection)
        attempt_service = LearningHistoryService(learner_repo)
        now = datetime(2026, 2, 1, tzinfo=timezone.utc)
        attempt_service.record_analysis("ql-learner", analysis(), completed_at=now)

        repo = PostgresQuestionLearningHistoryRepository(connection)
        service = QuestionLearningHistoryService(repo)
        service.record_analysis("ql-learner", analysis(), completed_at=now)
        service.record_analysis("ql-learner", analysis(), completed_at=now)

        rows = repo.list_outcomes("ql-learner")
        assert len(rows) == 1
        assert rows[0].question_id == "ql-q1"
        assert rows[0].outcome.value == "INCORRECT"
        history = service.history("ql-learner", generated_at=now)
        assert history.revision_candidates[0].question_id == "ql-q1"
