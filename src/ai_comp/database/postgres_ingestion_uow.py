from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from ai_comp.database.postgres_ingestion import (
    PostgresIngestionJobRepository,
    PostgresOutboxRepository,
)
from ai_comp.ingestion.repository import IngestionRepositories


@dataclass(frozen=True)
class PostgresIngestionRepositories:
    jobs: PostgresIngestionJobRepository
    outbox: PostgresOutboxRepository


_T = TypeVar("_T")


class PostgresIngestionUnitOfWork:
    """Atomic job-state + outbox boundary for one durable lifecycle transition."""

    def __init__(self, connection: Any) -> None:
        self.connection = connection
        self.repositories = PostgresIngestionRepositories(
            jobs=PostgresIngestionJobRepository(connection),
            outbox=PostgresOutboxRepository(connection),
        )

    def execute(
        self,
        operation: Callable[[IngestionRepositories], _T],
    ) -> _T:
        with self.connection.transaction():
            repositories = IngestionRepositories(
                jobs=self.repositories.jobs,
                outbox=self.repositories.outbox,
            )
            return operation(repositories)
