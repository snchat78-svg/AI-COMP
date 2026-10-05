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
