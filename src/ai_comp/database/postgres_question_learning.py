from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.question_learning import (
    LearnerQuestionAttemptRecord,
    LearnerQuestionHistoryRepository,
    QuestionLearningHistoryConflictError,
    QuestionOutcomeKind,
)


class PostgresQuestionLearningHistoryRepository(LearnerQuestionHistoryRepository):
    """Durable PostgreSQL storage for learner question-level outcomes."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save_outcomes(
        self,
        outcomes: tuple[LearnerQuestionAttemptRecord, ...],
    ) -> None:
        if not outcomes:
            return
        learner_id = outcomes[0].learner_id
        attempt_id = outcomes[0].attempt_id
        if any(item.learner_id != learner_id for item in outcomes):
            raise ValueError("outcomes must belong to one learner")
        if any(item.attempt_id != attempt_id for item in outcomes):
            raise ValueError("outcomes must belong to one attempt")
        try:
            with self._connection.transaction():
                for item in outcomes:
                    if item.outcome_id != item.outcome_id.strip():
                        raise ValueError("outcome_id must not contain surrounding whitespace")
                    inserted = self._connection.execute(
                        """
                        INSERT INTO learner_question_attempts (
                            outcome_id, attempt_id, learner_id, test_id, session_id,
                            question_id, concept_ids, difficulty, selected_option_key,
                            correct_option_key, outcome, completed_at
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (outcome_id) DO NOTHING
                        RETURNING outcome_id
                        """,
                        (
                            item.outcome_id,
                            item.attempt_id,
                            item.learner_id,
                            item.test_id,
                            item.session_id,
                            item.question_id,
                            list(item.concept_ids),
                            item.difficulty,
                            item.selected_option_key,
                            item.correct_option_key,
                            item.outcome.value,
                            item.completed_at,
                        ),
                    ).fetchone()
                    if inserted is None:
                        existing = self._get_by_id(item.outcome_id)
                        if existing != item:
                            raise QuestionLearningHistoryConflictError(
                                "question outcome already exists with different data"
                            )
        except QuestionLearningHistoryConflictError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to persist learner question history") from exc

    def list_outcomes(
        self,
        learner_id: str,
    ) -> tuple[LearnerQuestionAttemptRecord, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT
                    outcome_id, attempt_id, learner_id, test_id, session_id,
                    question_id, concept_ids, difficulty, selected_option_key,
                    correct_option_key, outcome, completed_at
                FROM learner_question_attempts
                WHERE learner_id = %s
                ORDER BY completed_at, session_id, question_id
                """,
                (learner_id,),
            ).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list learner question history") from exc
        return tuple(self._row(row) for row in rows)

    def _get_by_id(
        self,
        outcome_id: str,
    ) -> LearnerQuestionAttemptRecord | None:
        row = self._connection.execute(
            """
            SELECT
                outcome_id, attempt_id, learner_id, test_id, session_id,
                question_id, concept_ids, difficulty, selected_option_key,
                correct_option_key, outcome, completed_at
            FROM learner_question_attempts
            WHERE outcome_id = %s
            """,
            (outcome_id,),
        ).fetchone()
        return None if row is None else self._row(row)

    @staticmethod
    def _row(row: Sequence[object]) -> LearnerQuestionAttemptRecord:
        return LearnerQuestionAttemptRecord(
            outcome_id=str(row[0]),
            attempt_id=str(row[1]),
            learner_id=str(row[2]),
            test_id=str(row[3]),
            session_id=str(row[4]),
            question_id=str(row[5]),
            concept_ids=tuple(str(value) for value in (row[6] or [])),
            difficulty=str(row[7]),
            selected_option_key=None if row[8] is None else str(row[8]),
            correct_option_key=str(row[9]),
            outcome=QuestionOutcomeKind(str(row[10])),
            completed_at=row[11],
        )
