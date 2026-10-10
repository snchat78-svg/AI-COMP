from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.preparation_request import (
    PreparationRequestStatus,
    PreparationTestRequest,
    PreparationTestRequestRecord,
)
from ai_comp.domain.test_engine import ScoringPolicy, TestSpecification


class PostgresPreparationTestRequestRepository:
    """Persists one active preparation request per learner and retains older rows."""

    COLUMNS = """
        request_id, learner_id, test_id, title, question_count, duration_seconds,
        correct_marks, incorrect_marks, unattempted_marks, mode, concept_ids,
        exclude_question_ids, shuffle_questions, shuffle_seed, exam_id, subject_id,
        as_of, status, created_at, updated_at
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save_active(
        self,
        request_id: str,
        request: PreparationTestRequest,
        *,
        now: datetime | None = None,
    ) -> PreparationTestRequestRecord:
        if not request_id.strip() or request_id != request_id.strip():
            raise ValueError("request_id must be a non-empty trimmed string")
        timestamp = now or datetime.now(timezone.utc)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        spec = request.specification
        try:
            with self._connection.transaction():
                # Serialize replacements, so parallel POSTs cannot leave two active
                # rows for the same learner under the partial unique index.
                self._connection.execute(
                    "LOCK TABLE preparation_test_requests IN SHARE ROW EXCLUSIVE MODE"
                )
                self._connection.execute(
                    """
                    UPDATE preparation_test_requests
                    SET status = 'SUPERSEDED', updated_at = %s
                    WHERE learner_id = %s AND status = 'ACTIVE'
                    """,
                    (timestamp, request.learner_id),
                )
                row = self._connection.execute(
                    f"""
                    INSERT INTO preparation_test_requests (
                        request_id, learner_id, test_id, title, question_count,
                        duration_seconds, correct_marks, incorrect_marks,
                        unattempted_marks, mode, concept_ids, exclude_question_ids,
                        shuffle_questions, shuffle_seed, exam_id, subject_id, as_of,
                        status, created_at, updated_at
                    )
                    VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        'ACTIVE',%s,%s
                    )
                    RETURNING {self.COLUMNS}
                    """,
                    (
                        request_id, request.learner_id, spec.test_id, spec.title,
                        spec.question_count, spec.duration_seconds,
                        spec.scoring.correct_marks, spec.scoring.incorrect_marks,
                        spec.scoring.unattempted_marks, request.mode.value,
                        list(request.concept_ids), list(request.exclude_question_ids),
                        spec.shuffle_questions, spec.shuffle_seed, request.exam_id,
                        request.subject_id, request.as_of, timestamp, timestamp,
                    ),
                ).fetchone()
            if row is None:
                raise RepositoryError("failed to return saved preparation request")
            return self._from_row(row)
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to save preparation request") from exc

    def get_active_for_learner(
        self,
        learner_id: str,
    ) -> PreparationTestRequestRecord | None:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        try:
            row = self._connection.execute(
                f"""
                SELECT {self.COLUMNS}
                FROM preparation_test_requests
                WHERE learner_id = %s AND status = 'ACTIVE'
                ORDER BY created_at DESC, request_id DESC
                LIMIT 1
                """,
                (learner_id,),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to load active preparation request") from exc
        return None if row is None else self._from_row(row)

    def get_for_learner(
        self,
        learner_id: str,
        request_id: str,
    ) -> PreparationTestRequestRecord | None:
        if not learner_id.strip() or not request_id.strip():
            raise ValueError("learner_id and request_id are required")
        try:
            row = self._connection.execute(
                f"""
                SELECT {self.COLUMNS}
                FROM preparation_test_requests
                WHERE learner_id = %s AND request_id = %s
                """,
                (learner_id, request_id),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to load preparation request") from exc
        return None if row is None else self._from_row(row)


    def list_for_learner(
        self,
        learner_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
        status: PreparationRequestStatus | None = None,
    ) -> tuple[PreparationTestRequestRecord, ...]:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 101:
            raise ValueError("limit must be between 1 and 101")
        if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 100000:
            raise ValueError("offset must be between 0 and 100000")
        if status is not None and not isinstance(status, PreparationRequestStatus):
            raise ValueError("status must be a PreparationRequestStatus")
        query = f"""
            SELECT {self.COLUMNS}
            FROM preparation_test_requests
            WHERE learner_id = %s
        """
        parameters: list[object] = [learner_id]
        if status is not None:
            query += " AND status = %s"
            parameters.append(status.value)
        query += " ORDER BY created_at DESC, request_id DESC LIMIT %s OFFSET %s"
        parameters.extend((limit, offset))
        try:
            rows = self._connection.execute(query, tuple(parameters)).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list preparation request history") from exc
        return tuple(self._from_row(row) for row in rows)

    def activate_for_learner(
        self,
        learner_id: str,
        request_id: str,
        *,
        now: datetime | None = None,
    ) -> PreparationTestRequestRecord | None:
        if not learner_id.strip() or not request_id.strip():
            raise ValueError("learner_id and request_id are required")
        timestamp = now or datetime.now(timezone.utc)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        try:
            with self._connection.transaction():
                # Serialize all lifecycle transitions with save_active(), so
                # reactivating an older request cannot race another replacement.
                self._connection.execute(
                    "LOCK TABLE preparation_test_requests IN SHARE ROW EXCLUSIVE MODE"
                )
                row = self._connection.execute(
                    f"""
                    SELECT {self.COLUMNS}
                    FROM preparation_test_requests
                    WHERE learner_id = %s AND request_id = %s
                    FOR UPDATE
                    """,
                    (learner_id, request_id),
                ).fetchone()
                if row is None:
                    return None
                current = self._from_row(row)
                if current.status in (
                    PreparationRequestStatus.ACTIVE,
                    PreparationRequestStatus.CANCELLED,
                ):
                    # Activating the active row is idempotent; cancellation is
                    # terminal and requires creating a fresh request instead.
                    return current
                self._connection.execute(
                    """
                    UPDATE preparation_test_requests
                    SET status = 'SUPERSEDED', updated_at = %s
                    WHERE learner_id = %s AND status = 'ACTIVE'
                    """,
                    (timestamp, learner_id),
                )
                activated = self._connection.execute(
                    f"""
                    UPDATE preparation_test_requests
                    SET status = 'ACTIVE', updated_at = %s
                    WHERE learner_id = %s AND request_id = %s
                      AND status = 'SUPERSEDED'
                    RETURNING {self.COLUMNS}
                    """,
                    (timestamp, learner_id, request_id),
                ).fetchone()
                if activated is None:
                    raise RepositoryError("preparation request changed during activation")
            return self._from_row(activated)
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to activate preparation request") from exc

    def cancel_for_learner(
        self,
        learner_id: str,
        request_id: str,
        *,
        now: datetime | None = None,
    ) -> PreparationTestRequestRecord | None:
        if not learner_id.strip() or not request_id.strip():
            raise ValueError("learner_id and request_id are required")
        timestamp = now or datetime.now(timezone.utc)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        try:
            with self._connection.transaction():
                self._connection.execute(
                    "LOCK TABLE preparation_test_requests IN SHARE ROW EXCLUSIVE MODE"
                )
                row = self._connection.execute(
                    f"""
                    SELECT {self.COLUMNS}
                    FROM preparation_test_requests
                    WHERE learner_id = %s AND request_id = %s
                    FOR UPDATE
                    """,
                    (learner_id, request_id),
                ).fetchone()
                if row is None:
                    return None
                current = self._from_row(row)
                if current.status is PreparationRequestStatus.CANCELLED:
                    # Repeated cancellation is safe and preserves the original
                    # transition timestamp.
                    return current
                cancelled = self._connection.execute(
                    f"""
                    UPDATE preparation_test_requests
                    SET status = 'CANCELLED', updated_at = %s
                    WHERE learner_id = %s AND request_id = %s
                      AND status IN ('ACTIVE', 'SUPERSEDED')
                    RETURNING {self.COLUMNS}
                    """,
                    (timestamp, learner_id, request_id),
                ).fetchone()
                if cancelled is None:
                    raise RepositoryError("preparation request changed during cancellation")
            return self._from_row(cancelled)
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to cancel preparation request") from exc

    @staticmethod
    def _from_row(row: Sequence[object]) -> PreparationTestRequestRecord:
        spec = TestSpecification(
            test_id=str(row[2]),
            title=str(row[3]),
            question_count=int(row[4]),
            duration_seconds=int(row[5]),
            scoring=ScoringPolicy(
                correct_marks=float(row[6]),
                incorrect_marks=float(row[7]),
                unattempted_marks=float(row[8]),
            ),
            shuffle_questions=bool(row[12]),
            shuffle_seed=None if row[13] is None else int(row[13]),
        )
        request = PreparationTestRequest(
            learner_id=str(row[1]),
            specification=spec,
            mode=PersonalizedPreparationMode(str(row[9])),
            concept_ids=tuple(str(v) for v in (row[10] or ())),
            exclude_question_ids=tuple(str(v) for v in (row[11] or ())),
            exam_id=None if row[14] is None else str(row[14]),
            subject_id=None if row[15] is None else str(row[15]),
            as_of=row[16],
        )
        return PreparationTestRequestRecord(
            request_id=str(row[0]),
            request=request,
            status=PreparationRequestStatus(str(row[17])),
            created_at=row[18],
            updated_at=row[19],
        )


__all__ = ["PostgresPreparationTestRequestRepository"]
