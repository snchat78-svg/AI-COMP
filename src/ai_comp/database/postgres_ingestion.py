from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from ai_comp.domain.ingestion import (
    IngestionJob,
    IngestionJobStatus,
    OutboxEvent,
)
from ai_comp.ingestion.repository import (
    IngestionConcurrencyError,
    IngestionRepositoryError,
)


class PostgresIngestionJobRepository:
    """Transaction-aware PostgreSQL repository; caller owns the transaction."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def get(self, job_id: str) -> IngestionJob | None:
        row = self._connection.execute(
            self._select_sql("job_id = %s"),
            (job_id,),
        ).fetchone()
        return None if row is None else self._row_to_job(row)

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> IngestionJob | None:
        row = self._connection.execute(
            self._select_sql("idempotency_key = %s"),
            (idempotency_key,),
        ).fetchone()
        return None if row is None else self._row_to_job(row)

    def create_if_absent(
        self,
        job: IngestionJob,
    ) -> tuple[IngestionJob, bool]:
        try:
            row = self._connection.execute(
                """
                INSERT INTO ingestion_jobs (
                    job_id,
                    idempotency_key,
                    document_id,
                    document_sha256,
                    paper_id,
                    exam_id,
                    year,
                    shift,
                    source_url,
                    status,
                    attempt_count,
                    version,
                    checkpoint,
                    last_error,
                    created_at,
                    updated_at,
                    completed_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s::jsonb, %s, %s, %s, %s
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING job_id
                """,
                self._insert_values(job),
            ).fetchone()

            if row is not None:
                return job, True

            existing = self.get_by_idempotency_key(job.idempotency_key)
            if existing is None:
                raise IngestionRepositoryError(
                    "could not resolve idempotent ingestion job"
                )
            return existing, False
        except IngestionRepositoryError:
            raise
        except Exception as exc:
            raise IngestionRepositoryError(
                "failed to create ingestion job"
            ) from exc

    def save(
        self,
        job: IngestionJob,
        *,
        expected_version: int,
    ) -> None:
        try:
            row = self._connection.execute(
                """
                UPDATE ingestion_jobs
                SET
                    status = %s,
                    attempt_count = %s,
                    version = %s,
                    checkpoint = %s::jsonb,
                    last_error = %s,
                    updated_at = %s,
                    completed_at = %s
                WHERE job_id = %s
                  AND version = %s
                RETURNING job_id
                """,
                (
                    job.status.value,
                    job.attempt_count,
                    job.version,
                    json.dumps(dict(job.checkpoint), ensure_ascii=False),
                    job.last_error,
                    job.updated_at,
                    job.completed_at,
                    job.job_id,
                    expected_version,
                ),
            ).fetchone()
            if row is None:
                raise IngestionConcurrencyError(
                    "ingestion job version changed before update"
                )
        except IngestionConcurrencyError:
            raise
        except Exception as exc:
            raise IngestionRepositoryError(
                "failed to update ingestion job"
            ) from exc

    @staticmethod
    def _select_sql(where: str) -> str:
        return f"""
            SELECT
                job_id,
                idempotency_key,
                document_id,
                document_sha256,
                paper_id,
                exam_id,
                year,
                shift,
                source_url,
                status,
                attempt_count,
                version,
                checkpoint,
                last_error,
                created_at,
                updated_at,
                completed_at
            FROM ingestion_jobs
            WHERE {where}
        """

    @staticmethod
    def _insert_values(job: IngestionJob) -> Sequence[object]:
        return (
            job.job_id,
            job.idempotency_key,
            job.document_id,
            job.document_sha256,
            job.paper_id,
            job.exam_id,
            job.year,
            job.shift,
            job.source_url,
            job.status.value,
            job.attempt_count,
            job.version,
            json.dumps(dict(job.checkpoint), ensure_ascii=False),
            job.last_error,
            job.created_at,
            job.updated_at,
            job.completed_at,
        )

    @staticmethod
    def _row_to_job(row: Sequence[object]) -> IngestionJob:
        (
            job_id,
            idempotency_key,
            document_id,
            document_sha256,
            paper_id,
            exam_id,
            year,
            shift,
            source_url,
            status,
            attempt_count,
            version,
            checkpoint,
            last_error,
            created_at,
            updated_at,
            completed_at,
        ) = row
        if isinstance(checkpoint, str):
            checkpoint = json.loads(checkpoint)
        return IngestionJob(
            job_id=str(job_id),
            idempotency_key=str(idempotency_key),
            document_id=str(document_id),
            document_sha256=str(document_sha256),
            paper_id=str(paper_id),
            exam_id=str(exam_id),
            year=int(year),
            shift=None if shift is None else str(shift),
            source_url=str(source_url),
            status=IngestionJobStatus(str(status)),
            attempt_count=int(attempt_count),
            version=int(version),
            checkpoint=dict(checkpoint or {}),
            last_error=None if last_error is None else str(last_error),
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
        )


class PostgresOutboxRepository:
    """Transaction-aware PostgreSQL outbox repository."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, event: OutboxEvent) -> None:
        try:
            row = self._connection.execute(
                """
                INSERT INTO ingestion_outbox (
                    event_id,
                    dedupe_key,
                    aggregate_type,
                    aggregate_id,
                    aggregate_version,
                    event_type,
                    payload,
                    created_at,
                    published_at,
                    attempt_count,
                    last_error
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s::jsonb,
                    %s, %s, %s, %s
                )
                ON CONFLICT (dedupe_key) DO NOTHING
                RETURNING event_id
                """,
                (
                    event.event_id,
                    event.dedupe_key,
                    event.aggregate_type,
                    event.aggregate_id,
                    event.aggregate_version,
                    event.event_type,
                    json.dumps(dict(event.payload), ensure_ascii=False),
                    event.created_at,
                    event.published_at,
                    event.attempt_count,
                    event.last_error,
                ),
            ).fetchone()
            if row is not None:
                return

            existing = self._connection.execute(
                """
                SELECT
                    event_id,
                    dedupe_key,
                    aggregate_type,
                    aggregate_id,
                    aggregate_version,
                    event_type,
                    payload,
                    created_at,
                    published_at,
                    attempt_count,
                    last_error
                FROM ingestion_outbox
                WHERE dedupe_key = %s
                """,
                (event.dedupe_key,),
            ).fetchone()
            if existing is None:
                raise IngestionRepositoryError(
                    "could not resolve existing outbox event"
                )
            stored = self._row_to_event(existing)
            if stored != event:
                raise IngestionRepositoryError(
                    "outbox dedupe key already exists with different event"
                )
        except IngestionRepositoryError:
            raise
        except Exception as exc:
            raise IngestionRepositoryError(
                "failed to persist ingestion outbox event"
            ) from exc

    def list_unpublished(
        self,
        *,
        limit: int = 100,
    ) -> tuple[OutboxEvent, ...]:
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        rows = self._connection.execute(
            """
            SELECT
                event_id,
                dedupe_key,
                aggregate_type,
                aggregate_id,
                aggregate_version,
                event_type,
                payload,
                created_at,
                published_at,
                attempt_count,
                last_error
            FROM ingestion_outbox
            WHERE published_at IS NULL
            ORDER BY created_at, event_id
            LIMIT %s
            """,
            (limit,),
        ).fetchall()
        return tuple(self._row_to_event(row) for row in rows)

    def mark_published(self, event_id: str) -> None:
        row = self._connection.execute(
            """
            UPDATE ingestion_outbox
            SET published_at = NOW()
            WHERE event_id = %s
              AND published_at IS NULL
            RETURNING event_id
            """,
            (event_id,),
        ).fetchone()
        if row is None:
            existing = self._connection.execute(
                "SELECT event_id FROM ingestion_outbox WHERE event_id = %s",
                (event_id,),
            ).fetchone()
            if existing is None:
                raise IngestionRepositoryError(
                    f"outbox event not found: {event_id}"
                )

    def record_publish_failure(
        self,
        event_id: str,
        error: str,
    ) -> None:
        row = self._connection.execute(
            """
            UPDATE ingestion_outbox
            SET
                attempt_count = attempt_count + 1,
                last_error = %s
            WHERE event_id = %s
            RETURNING event_id
            """,
            (error, event_id),
        ).fetchone()
        if row is None:
            raise IngestionRepositoryError(
                f"outbox event not found: {event_id}"
            )

    @staticmethod
    def _row_to_event(row: Sequence[object]) -> OutboxEvent:
        (
            event_id,
            dedupe_key,
            aggregate_type,
            aggregate_id,
            aggregate_version,
            event_type,
            payload,
            created_at,
            published_at,
            attempt_count,
            last_error,
        ) = row
        if isinstance(payload, str):
            payload = json.loads(payload)
        return OutboxEvent(
            event_id=str(event_id),
            dedupe_key=str(dedupe_key),
            aggregate_type=str(aggregate_type),
            aggregate_id=str(aggregate_id),
            aggregate_version=int(aggregate_version),
            event_type=str(event_type),
            payload=dict(payload or {}),
            created_at=created_at,
            published_at=published_at,
            attempt_count=int(attempt_count),
            last_error=None if last_error is None else str(last_error),
        )
