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

    registry = build_initial_registry()
    counts = sync_source_registry(connection, registry)

    sql = [statement for statement, _ in connection.calls]
    assert counts.conducting_bodies == len(registry.bodies())
    assert counts.exams == len(registry.exams())
    assert counts.paper_categories == len(registry.categories())
    assert counts.sources == len(registry.sources())
    assert len(sql) == (
        counts.conducting_bodies + counts.exams
        + counts.paper_categories + counts.sources
    )
    assert "INSERT INTO conducting_bodies" in sql[0]
    assert f"INSERT INTO exams" in sql[counts.conducting_bodies]
    category_start = counts.conducting_bodies + counts.exams
    source_start = category_start + counts.paper_categories
    assert "INSERT INTO paper_categories" in sql[category_start]
    assert "INSERT INTO sources" in sql[source_start]
    assert all("ON CONFLICT" in statement for statement in sql)
    assert not any("DELETE" in statement.upper() for statement in sql)


def test_registry_sync_is_repeatable_without_deleting_existing_history():
    connection = Connection()
    registry = build_initial_registry()

    first = sync_source_registry(connection, registry)
    second = sync_source_registry(connection, registry)

    assert first == second
    count = (
        len(registry.bodies()) + len(registry.exams())
        + len(registry.categories()) + len(registry.sources())
    )
    assert len(connection.calls) == count * 2
    assert all("ON CONFLICT" in statement for statement, _ in connection.calls)
