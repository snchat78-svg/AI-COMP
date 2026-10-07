from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Callable, Mapping

from ai_comp.domain.ingestion import (
    IngestionJob,
    IngestionJobStatus,
    OutboxEvent,
)
from ai_comp.ingestion.repository import (
    IngestionConcurrencyError,
    IngestionRepositories,
    IngestionTransactionBoundary,
)


@dataclass
class InMemoryIngestionStore:
    jobs_by_id: dict[str, IngestionJob]
    jobs_by_key: dict[str, str]
    outbox_by_id: dict[str, OutboxEvent]
    outbox_by_dedupe: dict[str, str]

    def __init__(self) -> None:
        self.jobs_by_id = {}
        self.jobs_by_key = {}
        self.outbox_by_id = {}
        self.outbox_by_dedupe = {}


class InMemoryIngestionJobRepository:
    def __init__(self, store: InMemoryIngestionStore) -> None:
        self.store = store

    def get(self, job_id: str) -> IngestionJob | None:
        return self.store.jobs_by_id.get(job_id)

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> IngestionJob | None:
        job_id = self.store.jobs_by_key.get(idempotency_key)
        return None if job_id is None else self.get(job_id)

    def create_if_absent(
        self,
        job: IngestionJob,
    ) -> tuple[IngestionJob, bool]:
        existing = self.get_by_idempotency_key(job.idempotency_key)
        if existing is not None:
            return existing, False
        if self.get(job.job_id) is not None:
            raise IngestionConcurrencyError(
                "job_id already exists with different data"
            )
        self.store.jobs_by_id[job.job_id] = job
        self.store.jobs_by_key[job.idempotency_key] = job.job_id
        return job, True

    def save(
        self,
        job: IngestionJob,
        *,
        expected_version: int,
    ) -> None:
        current = self.get(job.job_id)
        if current is None:
            raise IngestionConcurrencyError("ingestion job does not exist")
        if current.version != expected_version:
            raise IngestionConcurrencyError(
                "ingestion job version changed before update"
            )
        self.store.jobs_by_id[job.job_id] = job


class InMemoryOutboxRepository:
    def __init__(self, store: InMemoryIngestionStore) -> None:
        self.store = store

    def save(self, event: OutboxEvent) -> None:
        existing_id = self.store.outbox_by_dedupe.get(event.dedupe_key)
        if existing_id is not None:
            existing = self.store.outbox_by_id[existing_id]
            if existing != event:
                raise ValueError(
                    "outbox dedupe key already exists with different event"
                )
            return
        self.store.outbox_by_id[event.event_id] = event
        self.store.outbox_by_dedupe[event.dedupe_key] = event.event_id

    def list_unpublished(
        self,
        *,
        limit: int = 100,
    ) -> tuple[OutboxEvent, ...]:
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        return tuple(
            event
            for event in sorted(
                self.store.outbox_by_id.values(),
                key=lambda item: (item.created_at, item.event_id),
            )
            if event.published_at is None
        )[:limit]

    def mark_published(self, event_id: str) -> None:
        event = self.store.outbox_by_id.get(event_id)
        if event is None:
            raise KeyError(event_id)
        self.store.outbox_by_id[event_id] = OutboxEvent(
            **{
                **event.__dict__,
                "published_at": datetime.now(timezone.utc),
            }
        )

    def record_publish_failure(
        self,
        event_id: str,
        error: str,
    ) -> None:
        event = self.store.outbox_by_id.get(event_id)
        if event is None:
            raise KeyError(event_id)
        self.store.outbox_by_id[event_id] = OutboxEvent(
            **{
                **event.__dict__,
                "attempt_count": event.attempt_count + 1,
                "last_error": error,
            }
        )


class InMemoryIngestionTransactionBoundary:
    """Transactional test/local boundary with rollback semantics."""

    def __init__(self, store: InMemoryIngestionStore) -> None:
        self.store = store
        self.jobs = InMemoryIngestionJobRepository(store)
        self.outbox = InMemoryOutboxRepository(store)

    def execute(
        self,
        operation: Callable[[IngestionRepositories], object],
    ):
        snapshot = deepcopy(self.store)
        repositories = IngestionRepositories(
            jobs=self.jobs,
            outbox=self.outbox,
        )
        try:
            return operation(repositories)
        except Exception:
            self.store.jobs_by_id = snapshot.jobs_by_id
            self.store.jobs_by_key = snapshot.jobs_by_key
            self.store.outbox_by_id = snapshot.outbox_by_id
            self.store.outbox_by_dedupe = snapshot.outbox_by_dedupe
            self.jobs.store = self.store
            self.outbox.store = self.store
            raise


@dataclass(frozen=True)
class IngestionJobRunResult:
    job: IngestionJob
    ingestion_result: object | None
    replayed: bool
    error: str | None = None


class IngestionJobService:
    """Creates and executes idempotent, checkpoint-aware ingestion jobs."""

    _RESUMABLE_STATUSES = {
        IngestionJobStatus.PROCESSING,
        IngestionJobStatus.EXTRACTED,
        IngestionJobStatus.MATCHED,
        IngestionJobStatus.MASTERED,
    }

    def __init__(
        self,
        *,
        boundary: IngestionTransactionBoundary,
        processor,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.boundary = boundary
        self.processor = processor
        self.max_attempts = max_attempts

    @staticmethod
    def idempotency_key(request) -> str:
        raw = "\x1f".join(
            (
                request.document.document.sha256,
                request.exam_id,
                request.paper_id,
                str(request.year),
                request.shift or "",
            )
        )
        return sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def job_id_for(idempotency_key: str) -> str:
        return f"ingestion:{idempotency_key[:32]}"

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def ensure_job(self, request) -> tuple[IngestionJob, bool]:
        idempotency_key = self.idempotency_key(request)
        job = IngestionJob.create(
            job_id=self.job_id_for(idempotency_key),
            idempotency_key=idempotency_key,
            document_id=request.document.document.document_id,
            document_sha256=request.document.document.sha256,
            paper_id=request.paper_id,
            exam_id=request.exam_id,
            year=request.year,
            shift=request.shift,
            source_url=request.source_url,
            now=self._now(),
        )

        def create(repositories):
            existing, created = repositories.jobs.create_if_absent(job)
            if created:
                repositories.outbox.save(
                    OutboxEvent.for_job_transition(
                        job=existing,
                        previous_status=None,
                        event_type="INGESTION_JOB_CREATED",
                        now=self._now(),
                    )
                )
            return existing, created

        return self.boundary.execute(create)

    def run(self, request) -> IngestionJobRunResult:
        job, created = self.ensure_job(request)

        if job.status is IngestionJobStatus.COMPLETED:
            return IngestionJobRunResult(
                job=job,
                ingestion_result=None,
                replayed=not created,
            )

        if job.status is IngestionJobStatus.FAILED:
            return IngestionJobRunResult(
                job=job,
                ingestion_result=None,
                replayed=True,
                error=job.last_error or "ingestion job is terminally failed",
            )

        if job.status is IngestionJobStatus.HISTORICAL_RECORDED:
            completed = self._transition(
                job,
                IngestionJobStatus.COMPLETED,
                checkpoint={"resume_after": None},
                last_error=None,
            )
            return IngestionJobRunResult(
                job=completed,
                ingestion_result=None,
                replayed=True,
            )

        resume_after = self._resume_after(job)

        if job.status is IngestionJobStatus.DISCOVERED:
            job = self._transition(job, IngestionJobStatus.FETCHED)

        if job.status is not IngestionJobStatus.PROCESSING:
            job = self._transition(
                job,
                IngestionJobStatus.PROCESSING,
                checkpoint={
                    "resume_after": (
                        None
                        if resume_after is None
                        else resume_after.value
                    )
                },
            )

        try:
            result = self.processor.ingest(
                request,
                resume_after=resume_after,
                progress_callback=self._progress_callback(job.job_id),
            )
        except Exception as exc:
            current = self._reload(job.job_id)
            stored_resume = current.checkpoint.get("resume_after")
            resume_marker = (
                stored_resume
                if isinstance(stored_resume, str) and stored_resume
                else current.status.value
            )
            target = (
                IngestionJobStatus.FAILED
                if current.attempt_count >= self.max_attempts
                else IngestionJobStatus.RETRYABLE
            )
            failed_job = self._transition(
                current,
                target,
                checkpoint={
                    "resume_after": resume_marker,
                    "failure_attempt": current.attempt_count,
                },
                last_error=f"{type(exc).__name__}: {exc}",
            )
            return IngestionJobRunResult(
                job=failed_job,
                ingestion_result=None,
                replayed=not created,
                error=failed_job.last_error,
            )

        completed = self._transition(
            self._reload(job.job_id),
            IngestionJobStatus.COMPLETED,
            checkpoint={
                **self._result_checkpoint(result),
                "resume_after": None,
            },
            last_error=None,
        )
        return IngestionJobRunResult(
            job=completed,
            ingestion_result=result,
            replayed=not created,
        )

    def _progress_callback(self, job_id: str):
        def callback(
            status: IngestionJobStatus,
            checkpoint: Mapping[str, object],
        ) -> None:
            current = self._reload(job_id)
            if current.status is status:
                return
            self._transition(
                current,
                status,
                checkpoint=checkpoint,
                last_error=None,
            )

        return callback

    @staticmethod
    def _resume_after(job: IngestionJob) -> IngestionJobStatus | None:
        raw = job.checkpoint.get("resume_after")
        if isinstance(raw, str) and raw:
            try:
                return IngestionJobStatus(raw)
            except ValueError:
                return None
        if job.status in {
            IngestionJobStatus.EXTRACTED,
            IngestionJobStatus.MATCHED,
            IngestionJobStatus.MASTERED,
        }:
            return job.status
        return None

    def _reload(self, job_id: str) -> IngestionJob:
        job = self.boundary.execute(
            lambda repositories: repositories.jobs.get(job_id)
        )
        if job is None:
            raise IngestionConcurrencyError(
                f"ingestion job not found: {job_id}"
            )
        return job

    def _transition(
        self,
        job: IngestionJob,
        status: IngestionJobStatus,
        *,
        checkpoint: Mapping[str, object] | None = None,
        last_error: str | None = None,
    ) -> IngestionJob:
        now = self._now()
        updated = job.transition(
            status,
            checkpoint=checkpoint,
            last_error=last_error,
            now=now,
        )
        event = OutboxEvent.for_job_transition(
            job=updated,
            previous_status=job.status,
            now=now,
        )

        def save(repositories):
            repositories.jobs.save(
                updated,
                expected_version=job.version,
            )
            repositories.outbox.save(event)
            return updated

        return self.boundary.execute(save)

    @staticmethod
    def _result_checkpoint(result) -> dict[str, object]:
        values = {
            "question_count": result.question_count,
            "answer_resolution_count": result.answer_resolution_count,
            "unresolved_answer_count": result.unresolved_answer_count,
            "match_count": result.match_count,
            "appearance_count": result.appearance_count,
            "master_assignment_count": result.master_assignment_count,
            "historical_ingestion_allowed": result.historical_ingestion_allowed,
        }
        if result.history_skip_reason is not None:
            values["history_skip_reason"] = result.history_skip_reason
        return values
