from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Callable

from ai_comp.domain.ingestion import IngestionJobStatus, OutboxEvent
from ai_comp.domain.ingestion_batch import (
    IngestionBatch,
    IngestionBatchStatus,
)
from ai_comp.domain.verification import VerificationStatus
from ai_comp.ingestion.durable import (
    InMemoryIngestionJobRepository,
    InMemoryIngestionStore,
    InMemoryOutboxRepository,
    IngestionJobService,
)
from ai_comp.ingestion.repository import (
    BatchIngestionRepositories,
    IngestionConcurrencyError,
    IngestionBatchRepository,
    IngestionBatchTransactionBoundary,
)
from ai_comp.ingestion.orchestrator import VerifiedIngestionRequest


class InMemoryIngestionBatchStore:
    def __init__(self) -> None:
        self.batches_by_id: dict[str, IngestionBatch] = {}
        self.batches_by_key: dict[str, str] = {}
        self.items_by_batch: dict[str, tuple[str, ...]] = {}


class InMemoryIngestionBatchRepository:
    def __init__(self, store: InMemoryIngestionBatchStore) -> None:
        self.store = store

    def get(self, batch_id: str) -> IngestionBatch | None:
        return self.store.batches_by_id.get(batch_id)

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> IngestionBatch | None:
        batch_id = self.store.batches_by_key.get(idempotency_key)
        return None if batch_id is None else self.get(batch_id)

    def create_if_absent(
        self,
        batch: IngestionBatch,
    ) -> tuple[IngestionBatch, bool]:
        existing = self.get_by_idempotency_key(batch.idempotency_key)
        if existing is not None:
            if existing.job_ids != batch.job_ids:
                raise IngestionConcurrencyError(
                    "batch idempotency key already exists with different job set"
                )
            return existing, False
        if self.get(batch.batch_id) is not None:
            raise IngestionConcurrencyError(
                "batch_id already exists with different data"
            )
        self.store.batches_by_id[batch.batch_id] = batch
        self.store.batches_by_key[batch.idempotency_key] = batch.batch_id
        self.store.items_by_batch[batch.batch_id] = batch.job_ids
        return batch, True

    def save(
        self,
        batch: IngestionBatch,
        *,
        expected_version: int,
    ) -> None:
        current = self.get(batch.batch_id)
        if current is None:
            raise IngestionConcurrencyError("ingestion batch does not exist")
        if current.version != expected_version:
            raise IngestionConcurrencyError(
                "ingestion batch version changed before update"
            )
        self.store.batches_by_id[batch.batch_id] = batch


class InMemoryIngestionBatchTransactionBoundary:
    def __init__(
        self,
        *,
        batch_store: InMemoryIngestionBatchStore,
        job_store: InMemoryIngestionStore,
    ) -> None:
        self.batch_store = batch_store
        self.job_store = job_store
        self.jobs = InMemoryIngestionJobRepository(job_store)
        self.batches = InMemoryIngestionBatchRepository(batch_store)
        self.outbox = InMemoryOutboxRepository(job_store)

    def execute(
        self,
        operation: Callable[[BatchIngestionRepositories], object],
    ):
        batch_snapshot = deepcopy(self.batch_store)
        outbox_by_id = deepcopy(self.job_store.outbox_by_id)
        outbox_by_dedupe = deepcopy(self.job_store.outbox_by_dedupe)
        repositories = BatchIngestionRepositories(
            jobs=self.jobs,
            batches=self.batches,
            outbox=self.outbox,
        )
        try:
            return operation(repositories)
        except Exception:
            self.batch_store.batches_by_id = batch_snapshot.batches_by_id
            self.batch_store.batches_by_key = batch_snapshot.batches_by_key
            self.batch_store.items_by_batch = batch_snapshot.items_by_batch
            self.job_store.outbox_by_id = outbox_by_id
            self.job_store.outbox_by_dedupe = outbox_by_dedupe
            raise


@dataclass(frozen=True)
class IngestionBatchRunResult:
    batch: IngestionBatch
    job_results: tuple[object, ...]
    replayed: bool


class IngestionBatchService:
    """Runs a deterministic set of ingestion jobs as one resumable batch."""

    _VERIFICATION_RANK = {
        VerificationStatus.VERIFIED: 2,
        VerificationStatus.SECONDARY_LIKELY: 1,
        VerificationStatus.UNVERIFIED: 0,
    }

    def __init__(
        self,
        *,
        job_service: IngestionJobService,
        boundary: IngestionBatchTransactionBoundary,
    ) -> None:
        self.job_service = job_service
        self.boundary = boundary

    @staticmethod
    def idempotency_key(
        requests: tuple[VerifiedIngestionRequest, ...],
    ) -> str:
        keys = sorted(
            IngestionJobService.idempotency_key(request)
            for request in requests
        )
        if not keys:
            raise ValueError("batch must contain at least one request")
        return sha256("\x1e".join(keys).encode("utf-8")).hexdigest()

    @staticmethod
    def batch_id_for(idempotency_key: str) -> str:
        return f"batch:{idempotency_key[:32]}"

    @classmethod
    def _canonical_requests(
        cls,
        requests: tuple[VerifiedIngestionRequest, ...],
    ) -> tuple[VerifiedIngestionRequest, ...]:
        by_key: dict[str, VerifiedIngestionRequest] = {}
        for request in requests:
            key = IngestionJobService.idempotency_key(request)
            current = by_key.get(key)
            if current is None:
                by_key[key] = request
                continue
            current_rank = cls._VERIFICATION_RANK[current.verification.status]
            candidate_rank = cls._VERIFICATION_RANK[request.verification.status]
            current_order = (current_rank, current.source_url)
            candidate_order = (candidate_rank, request.source_url)
            if candidate_order > current_order:
                by_key[key] = request
        return tuple(
            by_key[key]
            for key in sorted(by_key)
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def ensure_batch(
        self,
        requests: tuple[VerifiedIngestionRequest, ...],
    ) -> tuple[IngestionBatch, bool]:
        canonical = self._canonical_requests(requests)
        if not canonical:
            raise ValueError("batch must contain at least one unique request")

        jobs = []
        for request in canonical:
            job, _ = self.job_service.ensure_job(request)
            jobs.append(job)

        key = self.idempotency_key(canonical)
        batch = IngestionBatch.create(
            batch_id=self.batch_id_for(key),
            idempotency_key=key,
            job_ids=tuple(job.job_id for job in jobs),
            now=self._now(),
        )

        def create(repositories):
            existing, created = repositories.batches.create_if_absent(batch)
            if created:
                repositories.outbox.save(
                    OutboxEvent.for_batch_update(
                        batch=existing,
                        previous_status=None,
                        event_type="INGESTION_BATCH_CREATED",
                        now=self._now(),
                    )
                )
            return existing, created

        return self.boundary.execute(create)

    def run(
        self,
        requests: tuple[VerifiedIngestionRequest, ...],
    ) -> IngestionBatchRunResult:
        canonical = self._canonical_requests(requests)
        batch, created = self.ensure_batch(canonical)

        if batch.status is IngestionBatchStatus.COMPLETED:
            return IngestionBatchRunResult(
                batch=batch,
                job_results=(),
                replayed=not created,
            )
        if batch.status is IngestionBatchStatus.FAILED:
            return IngestionBatchRunResult(
                batch=batch,
                job_results=(),
                replayed=True,
            )

        if batch.status is IngestionBatchStatus.DISCOVERED:
            batch = self._transition(
                batch,
                IngestionBatchStatus.RUNNING,
            )
        elif batch.status is IngestionBatchStatus.PARTIAL_FAILURE:
            batch = self._transition(
                batch,
                IngestionBatchStatus.RUNNING,
            )

        request_by_job = {}
        for request in canonical:
            job, _ = self.job_service.ensure_job(request)
            request_by_job[job.job_id] = request

        results = []
        for job_id in batch.job_ids:
            job = self._get_job(job_id)
            if job is None:
                raise IngestionConcurrencyError(
                    f"batch references missing ingestion job: {job_id}"
                )
            if job.status in {
                IngestionJobStatus.COMPLETED,
                IngestionJobStatus.FAILED,
            }:
                continue
            request = request_by_job.get(job_id)
            if request is None:
                raise ValueError(
                    f"batch job {job_id} has no matching request"
                )
            results.append(self.job_service.run(request))
            batch = self._refresh(batch)

        batch = self._refresh(batch)
        target = self._target_status(batch)
        if target is not batch.status:
            batch = self._transition(batch, target)

        return IngestionBatchRunResult(
            batch=batch,
            job_results=tuple(results),
            replayed=not created,
        )

    def _get_job(self, job_id: str):
        return self.boundary.execute(
            lambda repositories: repositories.jobs.get(job_id)
        )

    def _refresh(self, batch: IngestionBatch) -> IngestionBatch:
        counts = self.boundary.execute(
            lambda repositories: self._count_jobs(repositories, batch.job_ids)
        )
        updated = batch.with_progress(
            completed_jobs=counts[0],
            retryable_jobs=counts[1],
            failed_jobs=counts[2],
            now=self._now(),
        )
        return self._save_batch_update(batch, updated)

    @staticmethod
    def _count_jobs(repositories, job_ids: tuple[str, ...]):
        completed = retryable = failed = 0
        for job_id in job_ids:
            job = repositories.jobs.get(job_id)
            if job is None:
                raise IngestionConcurrencyError(
                    f"batch job not found: {job_id}"
                )
            if job.status is IngestionJobStatus.COMPLETED:
                completed += 1
            elif job.status is IngestionJobStatus.RETRYABLE:
                retryable += 1
            elif job.status is IngestionJobStatus.FAILED:
                failed += 1
        return completed, retryable, failed

    @staticmethod
    def _target_status(batch: IngestionBatch) -> IngestionBatchStatus:
        if batch.pending_jobs > 0:
            return IngestionBatchStatus.RUNNING
        if batch.completed_jobs == batch.total_jobs:
            return IngestionBatchStatus.COMPLETED
        if batch.failed_jobs == batch.total_jobs:
            return IngestionBatchStatus.FAILED
        return IngestionBatchStatus.PARTIAL_FAILURE

    def _transition(
        self,
        batch: IngestionBatch,
        status: IngestionBatchStatus,
    ) -> IngestionBatch:
        updated = batch.transition(
            status,
            now=self._now(),
        )
        return self._save_batch_update(batch, updated)

    def _save_batch_update(
        self,
        previous: IngestionBatch,
        updated: IngestionBatch,
    ) -> IngestionBatch:
        event_type = (
            "INGESTION_BATCH_STATUS_CHANGED"
            if previous.status is not updated.status
            else "INGESTION_BATCH_PROGRESS"
        )
        event = OutboxEvent.for_batch_update(
            batch=updated,
            previous_status=previous.status,
            event_type=event_type,
            now=updated.updated_at or self._now(),
        )

        def save(repositories):
            repositories.batches.save(
                updated,
                expected_version=previous.version,
            )
            repositories.outbox.save(event)
            return updated

        return self.boundary.execute(save)
