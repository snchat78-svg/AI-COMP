from pathlib import Path

import pytest

from ai_comp.database.migrations import MigrationError, MigrationRunner


def test_migration_discovery_is_ordered_and_checksumed(tmp_path: Path):
    (tmp_path / "0002_second.sql").write_text("CREATE TABLE second (id INT);", encoding="utf-8")
    (tmp_path / "0001_first.sql").write_text("CREATE TABLE first (id INT);", encoding="utf-8")

    migrations = MigrationRunner(tmp_path).discover()

    assert [item.version for item in migrations] == ["0001", "0002"]
    assert all(len(item.checksum) == 64 for item in migrations)


def test_migration_discovery_rejects_duplicate_versions(tmp_path: Path):
    (tmp_path / "0001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "0001_second.sql").write_text("SELECT 2;", encoding="utf-8")

    with pytest.raises(MigrationError, match="duplicate migration version"):
        MigrationRunner(tmp_path).discover()


def test_migration_discovery_rejects_bad_version_names(tmp_path: Path):
    (tmp_path / "first.sql").write_text("SELECT 1;", encoding="utf-8")

    with pytest.raises(MigrationError, match="must start with numeric"):
        MigrationRunner(tmp_path).discover()

def test_transaction_wrappers_are_removed_even_when_prefixed_by_comments():
    sql = """-- header comment
BEGIN;
CREATE TABLE example (id INT);
COMMIT;
"""
    normalized = MigrationRunner._without_transaction_wrappers(sql)

    assert "BEGIN;" not in normalized
    assert "COMMIT;" not in normalized
    assert "CREATE TABLE example" in normalized


class MigrationConnection:
    def __init__(self, applied=()):
        self.applied = dict(applied)
        self.events = []

    def execute(self, sql, params=()):
        self.events.append((sql, params))
        if sql.strip().startswith("SELECT version, checksum"):
            return type("Result", (), {"fetchall": lambda result_self: list(self.applied.items())})()
        return type("Result", (), {})()

    def transaction(self):
        owner = self

        class Tx:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                if exc_type is None:
                    owner.events.append(("commit", ()))
                return False

        return Tx()

    def commit(self):
        self.events.append(("commit-final", ()))


def test_migration_runner_rejects_checksum_drift(tmp_path: Path):
    migration = tmp_path / "0001_first.sql"
    migration.write_text("CREATE TABLE first (id INT);", encoding="utf-8")
    checksum = __import__("hashlib").sha256(
        "different".encode("utf-8")
    ).hexdigest()
    connection = MigrationConnection(applied=(("0001", checksum),))

    with pytest.raises(MigrationError, match="applied migration changed"):
        MigrationRunner(tmp_path).apply(connection)
