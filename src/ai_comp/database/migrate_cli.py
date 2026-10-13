from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Callable

from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner


def run_migrations(
    dsn: str,
    *,
    migrations_dir: str | Path = "database/migrations",
    connection_factory: Callable[[str], Any] | None = None,
) -> tuple[str, ...]:
    """Apply repository SQL migrations explicitly, outside API startup."""
    if not isinstance(dsn, str) or not dsn.strip():
        raise ValueError("AI_COMP_DATABASE_URL must be configured before migrating.")
    factory = connection_factory or connect_postgres
    connection = factory(dsn)
    try:
        return MigrationRunner(migrations_dir).apply(connection)
    finally:
        connection.close()


def main() -> int:
    dsn = os.environ.get("AI_COMP_DATABASE_URL", "").strip()
    if not dsn:
        print("AI_COMP_DATABASE_URL must be configured before migrating.", file=sys.stderr)
        return 2

    try:
        applied = run_migrations(dsn)
    except Exception as exc:
        # Avoid printing the DSN or credential-bearing exception details to logs.
        print(f"Database migration failed ({type(exc).__name__}). Check database access and migration logs.", file=sys.stderr)
        return 1

    if applied:
        print("Applied migration versions: " + ", ".join(applied))
    else:
        print("Database schema is already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
