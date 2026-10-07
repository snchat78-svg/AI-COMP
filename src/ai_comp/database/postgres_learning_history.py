from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.learning_history import (
    LearningAttemptRecord,
    LearningHistoryConflictError,
    LearningHistoryRepository,
    LearningTrend,
    LongTermPerformanceBand,
    TopicAttemptRecord,
)


class PostgresLearningHistoryRepository(LearningHistoryRepository):
    """Durable PostgreSQL storage for learner test attempts and topic snapshots."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save_attempt(
        self,
        attempt: LearningAttemptRecord,
        topics: tuple[TopicAttemptRecord, ...],
    ) -> None:
        if any(topic.attempt_id != attempt.attempt_id for topic in topics):
            raise ValueError("topic snapshot must reference the attempt")
        if any(topic.learner_id != attempt.learner_id for topic in topics):
            raise ValueError("topic snapshot learner must match attempt")

        try:
            with self._connection.transaction():
                inserted = self._connection.execute(
                    """
                    INSERT INTO learner_test_attempts (
                        attempt_id, learner_id, test_id, session_id,
                        total_questions, attempted_questions, correct_answers,
                        incorrect_answers, unattempted_questions, raw_score,
                        percentage, accuracy, completed_at
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (attempt_id) DO NOTHING
                    RETURNING attempt_id
                    """,
                    (
                        attempt.attempt_id,
                        attempt.learner_id,
                        attempt.test_id,
                        attempt.session_id,
                        attempt.total_questions,
                        attempt.attempted_questions,
                        attempt.correct_answers,
                        attempt.incorrect_answers,
                        attempt.unattempted_questions,
                        attempt.raw_score,
                        attempt.percentage,
                        attempt.accuracy,
                        attempt.completed_at,
                    ),
                ).fetchone()

                if inserted is None:
                    existing = self.get_attempt(attempt.learner_id, attempt.session_id)
                    if existing != attempt:
                        raise LearningHistoryConflictError(
                            "learner test attempt already exists with different data"
                        )
                    return

                seen: set[str] = set()
                for topic in topics:
                    if topic.concept_id in seen:
                        raise ValueError("duplicate concept in topic snapshot")
                    seen.add(topic.concept_id)
                    self._connection.execute(
                        """
                        INSERT INTO learner_topic_attempts (
                            attempt_id, learner_id, test_id, session_id,
                            concept_id, question_count, attempted_count,
                            correct_count, incorrect_count, unattempted_count,
                            accuracy, performance
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            topic.attempt_id,
                            topic.learner_id,
                            topic.test_id,
                            topic.session_id,
                            topic.concept_id,
                            topic.question_count,
                            topic.attempted_count,
                            topic.correct_count,
                            topic.incorrect_count,
                            topic.unattempted_count,
                            topic.accuracy,
                            topic.performance.value,
                        ),
                    )
        except LearningHistoryConflictError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to persist learner learning history") from exc

    def get_attempt(
        self,
        learner_id: str,
        session_id: str,
    ) -> LearningAttemptRecord | None:
        try:
            row = self._connection.execute(
                """
                SELECT
                    attempt_id, learner_id, test_id, session_id,
                    total_questions, attempted_questions, correct_answers,
                    incorrect_answers, unattempted_questions, raw_score,
                    percentage, accuracy, completed_at
                FROM learner_test_attempts
                WHERE learner_id = %s AND session_id = %s
                """,
                (learner_id, session_id),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to read learner attempt") from exc
        return None if row is None else self._attempt(row)

    def list_attempts(self, learner_id: str) -> tuple[LearningAttemptRecord, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT
                    attempt_id, learner_id, test_id, session_id,
                    total_questions, attempted_questions, correct_answers,
                    incorrect_answers, unattempted_questions, raw_score,
                    percentage, accuracy, completed_at
                FROM learner_test_attempts
                WHERE learner_id = %s
                ORDER BY completed_at, session_id
                """,
                (learner_id,),
            ).fetchall()
            return tuple(self._attempt(row) for row in rows)
        except Exception as exc:
            raise RepositoryError("failed to list learner attempts") from exc

    def list_topic_attempts(
        self,
        learner_id: str,
    ) -> tuple[TopicAttemptRecord, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT
                    attempt_id, learner_id, test_id, session_id,
                    concept_id, question_count, attempted_count,
                    correct_count, incorrect_count, unattempted_count,
                    accuracy, performance
                FROM learner_topic_attempts
                WHERE learner_id = %s
                ORDER BY attempt_id, concept_id
                """,
                (learner_id,),
            ).fetchall()
            return tuple(self._topic(row) for row in rows)
        except Exception as exc:
            raise RepositoryError("failed to list learner topic history") from exc

    @staticmethod
    def _attempt(row: Sequence[object]) -> LearningAttemptRecord:
        return LearningAttemptRecord(
            attempt_id=str(row[0]),
            learner_id=str(row[1]),
            test_id=str(row[2]),
            session_id=str(row[3]),
            total_questions=int(row[4]),
            attempted_questions=int(row[5]),
            correct_answers=int(row[6]),
            incorrect_answers=int(row[7]),
            unattempted_questions=int(row[8]),
            raw_score=float(row[9]),
            percentage=float(row[10]),
            accuracy=float(row[11]),
            completed_at=row[12],
        )

    @staticmethod
    def _topic(row: Sequence[object]) -> TopicAttemptRecord:
        return TopicAttemptRecord(
            attempt_id=str(row[0]),
            learner_id=str(row[1]),
            test_id=str(row[2]),
            session_id=str(row[3]),
            concept_id=str(row[4]),
            question_count=int(row[5]),
            attempted_count=int(row[6]),
            correct_count=int(row[7]),
            incorrect_count=int(row[8]),
            unattempted_count=int(row[9]),
            accuracy=float(row[10]),
            performance=LongTermPerformanceBand(str(row[11])),
        )
