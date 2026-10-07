import sys
from types import SimpleNamespace

import pytest

from ai_comp.database.connection import DatabaseConfigurationError, connect_postgres


def test_empty_dsn_is_rejected():
    with pytest.raises(DatabaseConfigurationError, match="DSN"):
        connect_postgres("")


def test_connection_factory_uses_autocommit(monkeypatch):
    calls = []

    def connect(dsn, *, autocommit):
        calls.append((dsn, autocommit))
        return SimpleNamespace(dsn=dsn, autocommit=autocommit)

    fake_psycopg = SimpleNamespace(connect=connect)
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)

    connection = connect_postgres("postgresql://example")

    assert connection.dsn == "postgresql://example"
    assert connection.autocommit is True
    assert calls == [("postgresql://example", True)]
