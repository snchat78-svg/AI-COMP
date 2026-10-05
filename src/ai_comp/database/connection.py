from typing import Any


class DatabaseConfigurationError(RuntimeError):
    """Raised when PostgreSQL configuration is incomplete."""


def connect_postgres(dsn: str) -> Any:
    """Create an autocommit Psycopg 3 connection for explicit transaction blocks."""
    if not dsn.strip():
        raise DatabaseConfigurationError("PostgreSQL DSN must not be empty")
    try:
        import psycopg
    except ImportError as exc:
        raise DatabaseConfigurationError(
            "PostgreSQL support requires the 'postgres' optional dependency"
        ) from exc
    return psycopg.connect(dsn, autocommit=True)
