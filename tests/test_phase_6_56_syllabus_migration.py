from pathlib import Path


def test_phase_6_56_syllabus_migration_is_https_and_review_gated() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "database"
        / "migrations"
        / "0023_phase6_56_exam_syllabus_mapping.sql"
    )
    sql = migration_path.read_text(encoding="utf-8")

    assert "source_url TEXT NOT NULL CHECK (source_url LIKE 'https://%')" in sql
    assert "source_status IN ('DISCOVERED', 'REVIEW_PENDING', 'VERIFIED', 'SUPERSEDED', 'REJECTED')" in sql
    assert "source_status <> 'VERIFIED'" in sql
    assert "document_sha256 IS NOT NULL" in sql
    assert "source_checked_at IS NOT NULL" in sql
    assert "source_checked_by IS NOT NULL" in sql
    assert "syllabus_inventory_complete BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "inventory_reviewed_at IS NOT NULL" in sql
    assert "inventory_reviewed_by IS NOT NULL" in sql
    assert "btrim(inventory_review_note) <> ''" in sql
    assert "applicability_status IN ('IN_SCOPE', 'OUT_OF_SCOPE', 'UNMAPPED', 'NEEDS_REVIEW')" in sql
    assert "m.reviewed_by" in sql or "reviewed_by TEXT" in sql
    assert "'REVIEW_PENDING'" in sql
    # The seed must not automatically mark any syllabus or concept mapping verified.
    assert "'VERIFIED'" not in sql[sql.index("INSERT INTO exam_syllabus_documents"):sql.index("COMMIT;")]
    assert "INSERT INTO exam_concept_applicability" not in sql
