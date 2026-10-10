from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.analysis.question_learning import QuestionLearningHistoryService
from ai_comp.analysis.test_analysis import TestAnalysisService
from ai_comp.database.postgres_learning_history import PostgresLearningHistoryRepository
from ai_comp.database.postgres_question_learning import PostgresQuestionLearningHistoryRepository
from ai_comp.domain.material_generation import GeneratedMCQ
from ai_comp.domain.test_engine import TestSession, TestSessionStatus


class CompletedTestSessionLearningRecorder:
    """Idempotently connects finished TestEngine results to durable learner history."""

    def __init__(self, connection_factory) -> None:
        self._connection_factory = connection_factory

    def record(
        self,
        learner_id: str,
        session: TestSession,
        questions: Sequence[GeneratedMCQ],
    ) -> None:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if session.result is None or session.status not in (
            TestSessionStatus.SUBMITTED,
            TestSessionStatus.EXPIRED,
        ):
            raise ValueError("only finished sessions can be recorded")
        if session.submitted_at is None:
            raise ValueError("finished session requires a completion timestamp")
        completed_at = datetime.fromtimestamp(session.submitted_at, tz=timezone.utc)
        analysis = TestAnalysisService().analyze(session, session.result, questions)
        connection = self._connection_factory()
        try:
            with connection.transaction():
                LearningHistoryService(
                    PostgresLearningHistoryRepository(connection)
                ).record_analysis(learner_id, analysis, completed_at=completed_at)
                QuestionLearningHistoryService(
                    PostgresQuestionLearningHistoryRepository(connection)
                ).record_analysis(learner_id, analysis, completed_at=completed_at)
        finally:
            close = getattr(connection, "close", None)
            if callable(close):
                close()


__all__ = ["CompletedTestSessionLearningRecorder"]
