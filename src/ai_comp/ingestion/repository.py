from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, TypeVar

from ai_comp.domain.ingestion import IngestionJob, OutboxEvent
from ai_comp.domain.ingestion_batch import IngestionBatch


class IngestionConcurrencyError(RuntimeError):
    """Raised when a job version changed before an update could be saved."""


class IngestionRepositoryError(RuntimeError):
    """Raised when durable ingestion persistence fails."""


class IngestionJobRepository(Protocol):
    def get(self, job_id: str) -> IngestionJob | None: ...

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> IngestionJob | None: ...

    def create_if_absent(
        self,
        job: IngestionJob,
    ) -> tuple[IngestionJob, bool]: ...

    def save(
        self,
        job: IngestionJob,
        *,
        expected_version: int,
    ) -> None: ...


class OutboxRepository(Protocol):
    def save(self, event: OutboxEvent) -> None: ...

    def list_unpublished(
        self,
        *,
        limit: int = 100,
    ) -> tuple[OutboxEvent, ...]: ...

    def mark_published(self, event_id: str) -> None: ...

    def record_publish_failure(
        self,
        event_id: str,
        error: str,
    ) -> None: ...


@dataclass(frozen=True)
class IngestionRepositories:
    jobs: IngestionJobRepository
    outbox: OutboxRepository


_T = TypeVar("_T")


class IngestionTransactionBoundary(Protocol):
    def execute(
        self,
        operation: Callable[[IngestionRepositories], _T],
    ) -> _T: ...



class IngestionBatchRepository(Protocol):
    def get(self, batch_id: str) -> IngestionBatch | None: ...

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> IngestionBatch | None: ...

    def create_if_absent(
        self,
        batch: IngestionBatch,
    ) -> tuple[IngestionBatch, bool]: ...

    def save(
        self,
        batch: IngestionBatch,
        *,
        expected_version: int,
    ) -> None: ...


@dataclass(frozen=True)
class BatchIngestionRepositories:
    jobs: IngestionJobRepository
    batches: IngestionBatchRepository
    outbox: OutboxRepository


class IngestionBatchTransactionBoundary(Protocol):
    def execute(
        self,
        operation: Callable[[BatchIngestionRepositories], _T],
    ) -> _T: ...
