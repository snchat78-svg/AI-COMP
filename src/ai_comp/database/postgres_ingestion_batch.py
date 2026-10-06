from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai_comp.database.postgres_ingestion import (
    PostgresIngestionJobRepository,
    PostgresOutboxRepository,
)
from ai_comp.database.repository import RepositoryError
from ai_comp.domain.ingestion_batch import (
    IngestionBatch,
    IngestionBatchStatus,
)
from ai_comp.ingestion.repository import IngestionConcurrencyError


class PostgresIngestionBatchRepository:
    """Transaction-aware PostgreSQL storage for ingestion batches."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def get(self, batch_id: str) -> IngestionBatch | None:
        row = self._connection.execute(
            self._select_sql("batch_id = %s"),
            (batch_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_batch(row)

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> IngestionBatch | None:
        row = self._connection.execute(
            self._select_sql("idempotency_key = %s"),
            (idempotency_key,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_batch(row)

    def create_if_absent(
        self,
        batch: IngestionBatch,
    ) -> tuple[IngestionBatch, bool]:
        try:
            row = self._connection.execute(
                """
                INSERT INTO ingestion_batches (
                    batch_id,
                    idempotency_key,
                    total_jobs,
                    completed_jobs,
                    retryable_jobs,
                    failed_jobs,
                    status,
                    version,
                    last_error,
                    created_at,
                    updated_at,
                    completed_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING batch_id
                """,
                self._insert_values(batch),
            ).fetchone()

            if row is not None:
                for item_order, job_id in enumerate(batch.job_ids, start=1):
                    self._connection.execute(
                        """
                        INSERT INTO ingestion_batch_items (
                            batch_id,
                            job_id,
                            item_order
                        )
                        VALUES (%s, %s, %s)
                        """,
                        (batch.batch_id, job_id, item_order),
                    )
                return batch, True

            existing = self.get_by_idempotency_key(batch.idempotency_key)
            if existing is None:
                raise RepositoryError(
                    "could not resolve existing ingestion batch"
                )
            if existing.job_ids != batch.job_ids:
                raise IngestionConcurrencyError(
                    "batch idempotency key already exists with different job set"
                )
            return existing, False
        except (RepositoryError, IngestionConcurrencyError):
            raise
        except Exception as exc:
            raise RepositoryError(
                "failed to create ingestion batch"
            ) from exc

    def save(
        self,
        batch: IngestionBatch,
        *,
        expected_version: int,
    ) -> None:
        try:
            row = self._connection.execute(
                """
                UPDATE ingestion_batches
                SET
                    total_jobs = %s,
                    completed_jobs = %s,
                    retryable_jobs = %s,
                    failed_jobs = %s,
                    status = %s,
                    version = %s,
                    last_error = %s,
                    updated_at = %s,
                    completed_at = %s
                WHERE batch_id = %s
                  AND version = %s
                RETURNING batch_id
                """,
                (
                    batch.total_jobs,
                    batch.completed_jobs,
                    batch.retryable_jobs,
                    batch.failed_jobs,
                    batch.status.value,
                    batch.version,
                    batch.last_error,
                    batch.updated_at,
                    batch.completed_at,
                    batch.batch_id,
                    expected_version,
                ),
            ).fetchone()
            if row is None:
                raise IngestionConcurrencyError(
                    "ingestion batch version changed before update"
                )
        except IngestionConcurrencyError:
            raise
        except Exception as exc:
            raise RepositoryError(
                "failed to update ingestion batch"
            ) from exc

    def _select_sql(self, where: str) -> str:
        return f"""
            SELECT
                b.batch_id,
                b.idempotency_key,
                b.total_jobs,
                b.completed_jobs,
                b.retryable_jobs,
                b.failed_jobs,
                b.status,
                b.version,
                b.last_error,
                b.created_at,
                b.updated_at,
                b.completed_at,
                COALESCE(
                    ARRAY(
                        SELECT i.job_id
                        FROM ingestion_batch_items AS i
                        WHERE i.batch_id = b.batch_id
                        ORDER BY i.item_order
                    ),
                    ARRAY[]::TEXT[]
                ) AS job_ids
            FROM ingestion_batches AS b
            WHERE {where}
        """

    @staticmethod
    def _insert_values(batch: IngestionBatch) -> Sequence[object]:
        return (
            batch.batch_id,
            batch.idempotency_key,
            batch.total_jobs,
            batch.completed_jobs,
            batch.retryable_jobs,
            batch.failed_jobs,
            batch.status.value,
            batch.version,
            batch.last_error,
            batch.created_at,
            batch.updated_at,
            batch.completed_at,
        )

    @staticmethod
    def _row_to_batch(row: Sequence[object]) -> IngestionBatch:
        (
            batch_id,
            idempotency_key,
            total_jobs,
            completed_jobs,
            retryable_jobs,
            failed_jobs,
            status,
            version,
            last_error,
            created_at,
            updated_at,
            completed_at,
            job_ids,
        ) = row
        return IngestionBatch(
            batch_id=str(batch_id),
            idempotency_key=str(idempotency_key),
            job_ids=tuple(str(job_id) for job_id in (job_ids or ())),
            total_jobs=int(total_jobs),
            completed_jobs=int(completed_jobs),
            retryable_jobs=int(retryable_jobs),
            failed_jobs=int(failed_jobs),
            status=IngestionBatchStatus(str(status)),
            version=int(version),
            last_error=None if last_error is None else str(last_error),
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
        )


class PostgresIngestionBatchUnitOfWork:
    """Atomic batch state + shared outbox boundary."""

    def __init__(self, connection: Any) -> None:
        self.connection = connection
        self.jobs = PostgresIngestionJobRepository(connection)
        self.batches = PostgresIngestionBatchRepository(connection)
        self.outbox = PostgresOutboxRepository(connection)

    def execute(self, operation):
        from ai_comp.ingestion.repository import BatchIngestionRepositories

        with self.connection.transaction():
            repositories = BatchIngestionRepositories(
                jobs=self.jobs,
                batches=self.batches,
                outbox=self.outbox,
            )
            return operation(repositories)
