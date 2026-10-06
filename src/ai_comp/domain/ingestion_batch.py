from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum


class IngestionBatchStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS: dict[IngestionBatchStatus, frozenset[IngestionBatchStatus]] = {
    IngestionBatchStatus.DISCOVERED: frozenset({
        IngestionBatchStatus.RUNNING,
    }),
    IngestionBatchStatus.RUNNING: frozenset({
        IngestionBatchStatus.COMPLETED,
        IngestionBatchStatus.PARTIAL_FAILURE,
        IngestionBatchStatus.FAILED,
    }),
    IngestionBatchStatus.PARTIAL_FAILURE: frozenset({
        IngestionBatchStatus.RUNNING,
        IngestionBatchStatus.COMPLETED,
        IngestionBatchStatus.FAILED,
    }),
    IngestionBatchStatus.COMPLETED: frozenset(),
    IngestionBatchStatus.FAILED: frozenset(),
}


@dataclass(frozen=True)
class IngestionBatch:
    batch_id: str
    idempotency_key: str
    job_ids: tuple[str, ...]
    total_jobs: int
    completed_jobs: int
    retryable_jobs: int
    failed_jobs: int
    status: IngestionBatchStatus
    version: int
    last_error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.batch_id.strip():
            raise ValueError("batch_id must not be empty")
        if len(self.idempotency_key) != 64:
            raise ValueError("idempotency_key must be a SHA-256 hex digest")
        if not self.job_ids:
            raise ValueError("batch must contain at least one job")
        if len(self.job_ids) != len(set(self.job_ids)):
            raise ValueError("batch job_ids must be unique")
        if self.total_jobs != len(self.job_ids):
            raise ValueError("total_jobs must equal len(job_ids)")
        for value in (
            self.completed_jobs,
            self.retryable_jobs,
            self.failed_jobs,
        ):
            if value < 0:
                raise ValueError("batch progress counts must be non-negative")
        if (
            self.completed_jobs
            + self.retryable_jobs
            + self.failed_jobs
            > self.total_jobs
        ):
            raise ValueError("batch progress exceeds total_jobs")
        if self.version < 0:
            raise ValueError("batch version must be non-negative")

    @property
    def pending_jobs(self) -> int:
        return (
            self.total_jobs
            - self.completed_jobs
            - self.retryable_jobs
            - self.failed_jobs
        )

    @classmethod
    def create(
        cls,
        *,
        batch_id: str,
        idempotency_key: str,
        job_ids: tuple[str, ...],
        now: datetime,
    ) -> "IngestionBatch":
        ordered = tuple(sorted(job_ids))
        return cls(
            batch_id=batch_id,
            idempotency_key=idempotency_key,
            job_ids=ordered,
            total_jobs=len(ordered),
            completed_jobs=0,
            retryable_jobs=0,
            failed_jobs=0,
            status=IngestionBatchStatus.DISCOVERED,
            version=0,
            created_at=now,
            updated_at=now,
        )

    def transition(
        self,
        status: IngestionBatchStatus,
        *,
        now: datetime,
        last_error: str | None = None,
    ) -> "IngestionBatch":
        if status is self.status:
            raise ValueError("batch status must actually change")
        if status not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(
                f"invalid ingestion batch transition: "
                f"{self.status.value} -> {status.value}"
            )
        return replace(
            self,
            status=status,
            version=self.version + 1,
            last_error=last_error,
            updated_at=now,
            completed_at=(
                now
                if status is IngestionBatchStatus.COMPLETED
                else self.completed_at
            ),
        )

    def with_progress(
        self,
        *,
        completed_jobs: int,
        retryable_jobs: int,
        failed_jobs: int,
        now: datetime,
        last_error: str | None = None,
    ) -> "IngestionBatch":
        updated = replace(
            self,
            completed_jobs=completed_jobs,
            retryable_jobs=retryable_jobs,
            failed_jobs=failed_jobs,
            version=self.version + 1,
            updated_at=now,
            last_error=last_error,
        )
        updated.__post_init__()
        return updated
