from ai_comp.database.postgres_uow import PostgresUnitOfWork


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


def test_postgres_unit_of_work_builds_all_phase4_repositories():
    connection = Connection()

    with PostgresUnitOfWork(connection) as repositories:
        assert repositories.registry is not None
        assert repositories.research is not None
        assert repositories.papers is not None
        assert repositories.questions is not None
        assert repositories.answer_keys is not None
        assert repositories.answer_resolutions is not None
        assert repositories.concepts is not None
        assert repositories.matches is not None
        assert repositories.appearances is not None
        assert repositories.embeddings is not None

    assert connection.events == ["begin", "commit"]
