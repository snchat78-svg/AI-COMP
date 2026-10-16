from ai_comp.research.registry_sync import sync_source_registry
from ai_comp.research.seed_registry import build_initial_registry


class Connection:
    def __init__(self):
        self.calls = []

    def transaction(self):
        class Transaction:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return Transaction()

    def execute(self, sql, params=()):
        self.calls.append((sql, params))


def test_registry_sync_upserts_parent_rows_before_dependent_rows():
    connection = Connection()

    counts = sync_source_registry(connection, build_initial_registry())

    sql = [statement for statement, _ in connection.calls]
    assert counts.conducting_bodies == 2
    assert counts.exams == 2
    assert counts.paper_categories == 2
    assert counts.sources == 2
    assert len(sql) == 8
    assert "INSERT INTO conducting_bodies" in sql[0]
    assert "INSERT INTO exams" in sql[2]
    assert "INSERT INTO paper_categories" in sql[4]
    assert "INSERT INTO sources" in sql[6]
    assert all("ON CONFLICT" in statement for statement in sql)
    assert not any("DELETE" in statement.upper() for statement in sql)


def test_registry_sync_is_repeatable_without_deleting_existing_history():
    connection = Connection()
    registry = build_initial_registry()

    first = sync_source_registry(connection, registry)
    second = sync_source_registry(connection, registry)

    assert first == second
    assert len(connection.calls) == 16
    assert all("ON CONFLICT" in statement for statement, _ in connection.calls)
