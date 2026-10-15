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


def test_runtime_loads_configured_firebase_service_account_explicitly(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    import firebase_admin
    from types import SimpleNamespace
    from ai_comp.api import runtime

    credential_file = tmp_path / "firebase-service-account.json"
    credential_file.write_text("test placeholder", encoding="utf-8")
    sentinel_credential = object()
    fake_app = SimpleNamespace(project_id="test-firebase-project")
    initialize_calls: list[dict[str, Any]] = []

    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(credential_file))
    monkeypatch.setattr(
        firebase_admin.credentials,
        "Certificate",
        lambda path: sentinel_credential if path == str(credential_file) else None,
    )
    monkeypatch.setattr(
        firebase_admin,
        "get_app",
        lambda: (_ for _ in ()).throw(ValueError("no default app")),
    )

    def fake_initialize_app(*, credential=None, options=None):
        initialize_calls.append({"credential": credential, "options": options})
        return fake_app

    monkeypatch.setattr(firebase_admin, "initialize_app", fake_initialize_app)

    result = runtime._initialize_firebase_app("test-firebase-project")

    assert result is fake_app
    assert len(initialize_calls) == 1
    assert initialize_calls[0]["credential"] is sentinel_credential
    assert initialize_calls[0]["options"] == {
        "projectId": "test-firebase-project",
        "httpTimeout": 10,
    }


def test_runtime_rejects_missing_configured_firebase_service_account_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    from ai_comp.api import runtime

    missing_file = tmp_path / "missing-service-account.json"
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(missing_file))

    with pytest.raises(RuntimeError, match="missing or unreadable"):
        runtime._initialize_firebase_app("test-firebase-project")
