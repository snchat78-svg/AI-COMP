from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any


class MigrationError(RuntimeError):
    """Raised when database migration state is unsafe or invalid."""


@dataclass(frozen=True)
class Migration:
    version: str
    filename: str
    checksum: str
    sql: str


class MigrationRunner:
    """Applies ordered SQL migrations and records immutable checksums."""

    TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        filename TEXT NOT NULL UNIQUE,
        checksum CHAR(64) NOT NULL,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """

    def __init__(self, migrations_dir: str | Path) -> None:
        self.migrations_dir = Path(migrations_dir)

    def discover(self) -> tuple[Migration, ...]:
        if not self.migrations_dir.exists():
            raise MigrationError(
                f"migration directory does not exist: {self.migrations_dir}"
            )

        migrations = []
        for path in sorted(self.migrations_dir.glob("*.sql")):
            version = path.stem.split("_", 1)[0]
            if not version.isdigit():
                raise MigrationError(
                    f"migration filename must start with numeric version: {path.name}"
                )
            sql = path.read_text(encoding="utf-8")
            migrations.append(
                Migration(
                    version=version,
                    filename=path.name,
                    checksum=sha256(sql.encode("utf-8")).hexdigest(),
                    sql=sql,
                )
            )

        versions = [item.version for item in migrations]
        if len(versions) != len(set(versions)):
            raise MigrationError("duplicate migration version detected")
        return tuple(migrations)

    def apply(self, connection: Any) -> tuple[str, ...]:
        migrations = self.discover()
        connection.execute(self.TABLE_SQL)

        applied = {
            str(row[0]): str(row[1])
            for row in connection.execute(
                "SELECT version, checksum FROM schema_migrations"
            ).fetchall()
        }

        applied_now: list[str] = []
        for migration in migrations:
            existing_checksum = applied.get(migration.version)
            if existing_checksum is not None:
                if existing_checksum != migration.checksum:
                    raise MigrationError(
                        f"applied migration changed: {migration.filename}"
                    )
                continue

            try:
                migration_sql = self._without_transaction_wrappers(migration.sql)
                with connection.transaction():
                    connection.execute(migration_sql)
                    connection.execute(
                        """
                        INSERT INTO schema_migrations (
                            version, filename, checksum
                        )
                        VALUES (%s, %s, %s)
                        """,
                        (
                            migration.version,
                            migration.filename,
                            migration.checksum,
                        ),
                    )
                applied_now.append(migration.version)
            except MigrationError:
                raise
            except Exception as exc:
                raise MigrationError(
                    f"failed to apply migration: {migration.filename}"
                ) from exc

        connection.commit()
        return tuple(applied_now)

    @staticmethod
    def _without_transaction_wrappers(sql: str) -> str:
        value = sql.strip()

        begin = value.upper().find("BEGIN;")
        if begin >= 0:
            value = value[begin + len("BEGIN;"):].lstrip()

        commit = value.upper().rfind("COMMIT;")
        if commit >= 0:
            value = value[:commit].rstrip()

        if not value:
            raise MigrationError("migration SQL is empty after normalization")
        return value
