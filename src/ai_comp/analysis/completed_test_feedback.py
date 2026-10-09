from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.analysis.question_learning import QuestionLearningHistoryService
from ai_comp.analysis.test_analysis import TestAnalysisService
from ai_comp.domain.learning_history import (
    LearningAttemptRecord,
    LearnerLearningHistory,
)
from ai_comp.domain.material_generation import GeneratedMCQ, GeneratedQuestionStatus
from ai_comp.domain.question_learning import LearnerQuestionHistory
from ai_comp.domain.test_analysis import TestAnalysis
from ai_comp.domain.test_engine import TestResult, TestSession, TestSessionStatus
from ai_comp.test_engine import TestEngine


_FINISHED_STATUSES = frozenset(
    {TestSessionStatus.SUBMITTED, TestSessionStatus.EXPIRED}
)


@dataclass(frozen=True)
class CompletedTestFeedback:
    """One immutable view of scoring, immediate analysis and updated learner history."""

    learner_id: str
    session: TestSession
    result: TestResult
    analysis: TestAnalysis
    attempt: LearningAttemptRecord
    learning_history: LearnerLearningHistory
    question_history: LearnerQuestionHistory

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        if self.session.status not in _FINISHED_STATUSES:
            raise ValueError("feedback requires a finished test session")
        if self.result.session_id != self.session.session_id:
            raise ValueError("feedback result does not match session")
        if self.attempt.learner_id != self.learner_id:
            raise ValueError("feedback attempt belongs to a different learner")
        if self.attempt.session_id != self.session.session_id:
            raise ValueError("feedback attempt does not match session")
        if self.learning_history.learner_id != self.learner_id:
            raise ValueError("learning history belongs to a different learner")
        if self.question_history.learner_id != self.learner_id:
            raise ValueError("question history belongs to a different learner")


class CompletedTestFeedbackService:
    """Connects completed TestEngine sessions to both existing learning-history services.

    Learning history is written first because its persisted completion timestamp anchors
    safe retries if question-level persistence fails. The repositories remain the owners
    of persistence and idempotency; this service does not create a second state store.
    """

    def __init__(
        self,
        *,
        test_engine: TestEngine,
        learning_history_service: LearningHistoryService,
        question_history_service: QuestionLearningHistoryService,
        analysis_service: TestAnalysisService | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.test_engine = test_engine
        self.learning_history_service = learning_history_service
        self.question_history_service = question_history_service
        self.analysis_service = analysis_service or TestAnalysisService()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def process_completed_test(
        self,
        learner_id: str,
        session_id: str,
        questions: Sequence[GeneratedMCQ],
    ) -> CompletedTestFeedback:
        """Analyze and persist one finished session, then return fresh learner history.

        Callers must authorize that learner_id owns session_id before calling this
        method. The current TestSession contract does not itself store learner ownership.
        Retrying the same learner/session pair is supported by the underlying stable
        attempt identities and by reusing the already-persisted completion timestamp.
        """
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if not session_id.strip():
            raise ValueError("session_id is required")

        session = self.test_engine.get_session(session_id)
        if session.status not in _FINISHED_STATUSES:
            raise ValueError("only finished (submitted or expired) test sessions can be processed")
        result = session.result
        if result is None:
            raise ValueError("finished test session is missing its result")
        if result.session_id != session.session_id or result.test_id != session.test_id:
            raise ValueError("stored result does not match test session")
        if result.status is not session.status:
            raise ValueError("stored result status does not match test session")

        materialized_questions = tuple(questions)
        question_ids = tuple(
            question.generated_question_id for question in materialized_questions
        )
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("duplicate generated question ID")
        if (
            len(question_ids) != len(session.question_ids)
            or set(question_ids) != set(session.question_ids)
        ):
            raise ValueError("questions do not exactly match the test session")
        if any(
            question.status is not GeneratedQuestionStatus.ACCEPTED
            for question in materialized_questions
        ):
            raise ValueError("only accepted generated questions can be analyzed")

        analysis = self.analysis_service.analyze(
            session,
            result,
            materialized_questions,
        )

        # A retry must use the original timestamp, otherwise idempotent repositories
        # correctly interpret an otherwise-identical attempt as conflicting data.
        existing_attempt = self.learning_history_service.repository.get_attempt(
            learner_id,
            session.session_id,
        )
        if existing_attempt is not None:
            completed_at = existing_attempt.completed_at
        else:
            completed_at = self.clock()
            if (
                completed_at.tzinfo is None
                or completed_at.utcoffset() is None
            ):
                raise ValueError("clock must return a timezone-aware datetime")
            completed_at = completed_at.astimezone(timezone.utc)

        attempt = self.learning_history_service.record_analysis(
            learner_id,
            analysis,
            completed_at=completed_at,
        )
        self.question_history_service.record_analysis(
            learner_id,
            analysis,
            completed_at=completed_at,
        )

        learning_history = self.learning_history_service.history(
            learner_id,
            generated_at=completed_at,
        )
        question_history = self.question_history_service.history(
            learner_id,
            generated_at=completed_at,
        )
        return CompletedTestFeedback(
            learner_id=learner_id,
            session=session,
            result=result,
            analysis=analysis,
            attempt=attempt,
            learning_history=learning_history,
            question_history=question_history,
        )


__all__ = ["CompletedTestFeedback", "CompletedTestFeedbackService"]
