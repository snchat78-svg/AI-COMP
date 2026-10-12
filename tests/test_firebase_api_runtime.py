from __future__ import annotations

from typing import Any

import pytest

from ai_comp.database import migrate_cli


class FakeConnection:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_run_migrations_closes_connection_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeConnection()
    monkeypatch.setattr(migrate_cli, "connect_postgres", lambda _dsn: connection)

    class FakeMigrationRunner:
        def __init__(self, migrations_dir: str) -> None:
            assert migrations_dir == "database/migrations"

        def apply(self, actual_connection: Any) -> tuple[str, ...]:
            assert actual_connection is connection
            return ("0001", "0002")

    monkeypatch.setattr(migrate_cli, "MigrationRunner", FakeMigrationRunner)

    assert migrate_cli.run_migrations("postgresql://test") == ("0001", "0002")
    assert connection.closed is True


def test_run_migrations_closes_connection_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeConnection()
    monkeypatch.setattr(migrate_cli, "connect_postgres", lambda _dsn: connection)

    class FailingMigrationRunner:
        def __init__(self, _migrations_dir: str) -> None:
            pass

        def apply(self, _connection: Any) -> tuple[str, ...]:
            raise RuntimeError("migration failure")

    monkeypatch.setattr(migrate_cli, "MigrationRunner", FailingMigrationRunner)

    with pytest.raises(RuntimeError, match="migration failure"):
        migrate_cli.run_migrations("postgresql://test")
    assert connection.closed is True


def test_run_migrations_rejects_empty_dsn_before_connecting() -> None:
    called = False

    def unexpected_connect(_dsn: str):
        nonlocal called
        called = True
        raise AssertionError("database must not be contacted")

    with pytest.raises(ValueError, match="AI_COMP_DATABASE_URL"):
        migrate_cli.run_migrations("  ", connection_factory=unexpected_connect)
    assert called is False


def test_runtime_factory_requires_environment_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    from ai_comp.api.runtime import create_runtime_app

    monkeypatch.delenv("AI_COMP_DATABASE_URL", raising=False)
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)

    with pytest.raises(RuntimeError, match="AI_COMP_DATABASE_URL"):
        create_runtime_app()


@pytest.mark.parametrize("emulator_host", ["127.0.0.1:9099", ""])
def test_runtime_factory_rejects_firebase_auth_emulator_mode(
    monkeypatch: pytest.MonkeyPatch,
    emulator_host: str,
) -> None:
    from ai_comp.api.runtime import create_runtime_app

    # Reject the setting even before other environment configuration is checked,
    # and before Firebase Admin or the database runtime can be initialized.
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", emulator_host)
    monkeypatch.delenv("AI_COMP_DATABASE_URL", raising=False)
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)

    with pytest.raises(RuntimeError, match="FIREBASE_AUTH_EMULATOR_HOST"):
        create_runtime_app()
