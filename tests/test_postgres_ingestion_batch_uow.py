from ai_comp.database.postgres_ingestion_batch import (
    PostgresIngestionBatchUnitOfWork,
)


class Transaction:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        self.events.append("begin")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.events.append("rollback" if exc_type else "commit")
        return False


class Connection:
    def __init__(self):
        self.events = []

    def transaction(self):
        return Transaction(self.events)


def test_postgres_batch_unit_of_work_is_atomic():
    connection = Connection()
    uow = PostgresIngestionBatchUnitOfWork(connection)

    result = uow.execute(
        lambda repositories: (
            repositories.jobs is not None,
            repositories.batches is not None,
            repositories.outbox is not None,
        )
    )

    assert result == (True, True, True)
    assert connection.events == ["begin", "commit"]
