from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "database"
    / "migrations"
    / "0031_phase_6_56_question_bank_delta_cursor_index.sql"
)


def test_question_bank_delta_cursor_has_ordering_index():
    sql = MIGRATION.read_text(encoding="utf-8")

    assert sql.startswith("-- Phase 6.56")
    assert "BEGIN;" in sql
    assert "COMMIT;" in sql
    assert "CREATE INDEX IF NOT EXISTS idx_question_bank_one_liners_updated_at_id" in sql
    assert "ON question_bank_one_liners(updated_at ASC, one_liner_id ASC)" in sql
    assert "DROP TABLE" not in sql
    assert "UPDATE question_bank_one_liners" not in sql
