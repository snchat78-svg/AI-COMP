from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from hashlib import sha256
from typing import Mapping
from urllib.parse import urlparse


class IngestionJobStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    FETCHED = "FETCHED"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    MATCHED = "MATCHED"
    MASTERED = "MASTERED"
    HISTORICAL_RECORDED = "HISTORICAL_RECORDED"
    COMPLETED = "COMPLETED"
    RETRYABLE = "RETRYABLE"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS: dict[IngestionJobStatus, frozenset[IngestionJobStatus]] = {
    IngestionJobStatus.DISCOVERED: frozenset({
        IngestionJobStatus.FETCHED,
        IngestionJobStatus.RETRYABLE,
        IngestionJobStatus.FAILED,
    }),
    IngestionJobStatus.FETCHED: frozenset({
        IngestionJobStatus.PROCESSING,
        IngestionJobStatus.RETRYABLE,
        IngestionJobStatus.FAILED,
    }),
    IngestionJobStatus.PROCESSING: frozenset({
        IngestionJobStatus.EXTRACTED,
        IngestionJobStatus.MATCHED,
        IngestionJobStatus.MASTERED,
        IngestionJobStatus.HISTORICAL_RECORDED,
        IngestionJobStatus.COMPLETED,
        IngestionJobStatus.RETRYABLE,
        IngestionJobStatus.FAILED,
    }),
    IngestionJobStatus.EXTRACTED: frozenset({
        IngestionJobStatus.PROCESSING,
        IngestionJobStatus.MATCHED,
        IngestionJobStatus.MASTERED,
        IngestionJobStatus.HISTORICAL_RECORDED,
        IngestionJobStatus.COMPLETED,
        IngestionJobStatus.RETRYABLE,
        IngestionJobStatus.FAILED,
    }),
    IngestionJobStatus.MATCHED: frozenset({
        IngestionJobStatus.PROCESSING,
        IngestionJobStatus.MASTERED,
        IngestionJobStatus.HISTORICAL_RECORDED,
        IngestionJobStatus.COMPLETED,
        IngestionJobStatus.RETRYABLE,
        IngestionJobStatus.FAILED,
    }),
    IngestionJobStatus.MASTERED: frozenset({
        IngestionJobStatus.PROCESSING,
        IngestionJobStatus.HISTORICAL_RECORDED,
        IngestionJobStatus.COMPLETED,
        IngestionJobStatus.RETRYABLE,
        IngestionJobStatus.FAILED,
    }),
    IngestionJobStatus.HISTORICAL_RECORDED: frozenset({
        IngestionJobStatus.COMPLETED,
        IngestionJobStatus.RETRYABLE,
        IngestionJobStatus.FAILED,
    }),
    IngestionJobStatus.RETRYABLE: frozenset({
        IngestionJobStatus.PROCESSING,
        IngestionJobStatus.FAILED,
    }),
    IngestionJobStatus.COMPLETED: frozenset(),
    IngestionJobStatus.FAILED: frozenset(),
}


@dataclass(frozen=True)
class IngestionJob:
    job_id: str
    idempotency_key: str
    document_id: str
    document_sha256: str
    paper_id: str
    exam_id: str
    year: int
    shift: str | None
    source_url: str
    status: IngestionJobStatus
    attempt_count: int
    version: int
    checkpoint: Mapping[str, object] = field(default_factory=dict)
    last_error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError("job_id must not be empty")
        if len(self.idempotency_key) != 64:
            raise ValueError("idempotency_key must be a SHA-256 hex digest")
        if len(self.document_sha256) != 64:
            raise ValueError("document_sha256 must be a SHA-256 hex digest")
        if not self.paper_id.strip() or not self.exam_id.strip():
            raise ValueError("paper_id and exam_id must not be empty")
        if self.year < 1900:
            raise ValueError("year must be >= 1900")
        if self.attempt_count < 0:
            raise ValueError("attempt_count must be non-negative")
        if self.version < 0:
            raise ValueError("version must be non-negative")
        parsed = urlparse(self.source_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source_url must be an HTTP(S) URL")

    @classmethod
    def create(
        cls,
        *,
        job_id: str,
        idempotency_key: str,
        document_id: str,
        document_sha256: str,
        paper_id: str,
        exam_id: str,
        year: int,
        shift: str | None,
        source_url: str,
        now: datetime,
    ) -> "IngestionJob":
        return cls(
            job_id=job_id,
            idempotency_key=idempotency_key,
            document_id=document_id,
            document_sha256=document_sha256,
            paper_id=paper_id,
            exam_id=exam_id,
            year=year,
            shift=shift,
            source_url=source_url,
            status=IngestionJobStatus.DISCOVERED,
            attempt_count=0,
            version=0,
            created_at=now,
            updated_at=now,
        )

    def transition(
        self,
        status: IngestionJobStatus,
        *,
        checkpoint: Mapping[str, object] | None = None,
        last_error: str | None = None,
        now: datetime,
    ) -> "IngestionJob":
        if status is self.status:
            raise ValueError("job status must actually change")
        if status not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(
                f"invalid ingestion job transition: "
                f"{self.status.value} -> {status.value}"
            )

        merged_checkpoint = dict(self.checkpoint)
        if checkpoint:
            merged_checkpoint.update(checkpoint)

        attempt_count = self.attempt_count
        if status is IngestionJobStatus.PROCESSING:
            attempt_count += 1

        completed_at = self.completed_at
        if status is IngestionJobStatus.COMPLETED:
            completed_at = now

        return IngestionJob(
            job_id=self.job_id,
            idempotency_key=self.idempotency_key,
            document_id=self.document_id,
            document_sha256=self.document_sha256,
            paper_id=self.paper_id,
            exam_id=self.exam_id,
            year=self.year,
            shift=self.shift,
            source_url=self.source_url,
            status=status,
            attempt_count=attempt_count,
            version=self.version + 1,
            checkpoint=merged_checkpoint,
            last_error=last_error,
            created_at=self.created_at,
            updated_at=now,
            completed_at=completed_at,
        )


@dataclass(frozen=True)
class OutboxEvent:
    event_id: str
    dedupe_key: str
    aggregate_type: str
    aggregate_id: str
    aggregate_version: int
    event_type: str
    payload: Mapping[str, object]
    created_at: datetime
    published_at: datetime | None = None
    attempt_count: int = 0
    last_error: str | None = None

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty")
        if not self.dedupe_key.strip():
            raise ValueError("dedupe_key must not be empty")
        if self.aggregate_version < 0:
            raise ValueError("aggregate_version must be non-negative")
        if self.attempt_count < 0:
            raise ValueError("attempt_count must be non-negative")

    @classmethod
    def for_job_transition(
        cls,
        *,
        job: IngestionJob,
        previous_status: IngestionJobStatus | None,
        event_type: str = "INGESTION_JOB_STATUS_CHANGED",
        now: datetime,
    ) -> "OutboxEvent":
        dedupe_key = f"{job.job_id}:{job.version}:{event_type}"
        digest = sha256(dedupe_key.encode("utf-8")).hexdigest()
        return cls(
            event_id=f"outbox:{digest[:32]}",
            dedupe_key=dedupe_key,
            aggregate_type="ingestion_job",
            aggregate_id=job.job_id,
            aggregate_version=job.version,
            event_type=event_type,
            payload={
                "job_id": job.job_id,
                "idempotency_key": job.idempotency_key,
                "previous_status": (
                    None if previous_status is None else previous_status.value
                ),
                "status": job.status.value,
                "version": job.version,
                "attempt_count": job.attempt_count,
                "checkpoint": dict(job.checkpoint),
                "last_error": job.last_error,
            },
            created_at=now,
        )


    @classmethod
    def for_batch_update(
        cls,
        *,
        batch,
        previous_status,
        event_type: str,
        now: datetime,
    ) -> "OutboxEvent":
        dedupe_key = f"{batch.batch_id}:{batch.version}:{event_type}"
        digest = sha256(dedupe_key.encode("utf-8")).hexdigest()
        return cls(
            event_id=f"outbox:{digest[:32]}",
            dedupe_key=dedupe_key,
            aggregate_type="ingestion_batch",
            aggregate_id=batch.batch_id,
            aggregate_version=batch.version,
            event_type=event_type,
            payload={
                "batch_id": batch.batch_id,
                "idempotency_key": batch.idempotency_key,
                "previous_status": (
                    None if previous_status is None else previous_status.value
                ),
                "status": batch.status.value,
                "version": batch.version,
                "total_jobs": batch.total_jobs,
                "completed_jobs": batch.completed_jobs,
                "retryable_jobs": batch.retryable_jobs,
                "failed_jobs": batch.failed_jobs,
            },
            created_at=now,
        )
