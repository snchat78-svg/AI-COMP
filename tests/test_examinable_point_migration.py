from __future__ import annotations

from pathlib import Path


def test_examinable_point_migration_separates_points_dimensions_mappings_and_learning_links():
    migration = (
        Path(__file__).resolve().parents[1]
        / "database" / "migrations"
        / "0027_phase6_56_examinable_point_coverage.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS exam_syllabus_examinable_points" in migration
    assert "CREATE TABLE IF NOT EXISTS exam_syllabus_point_concepts" in migration
    assert "CREATE TABLE IF NOT EXISTS exam_syllabus_point_dimensions" in migration
    assert "CREATE TABLE IF NOT EXISTS exam_syllabus_point_one_liner_links" in migration
    assert "NOT_APPLICABLE" in migration
    assert "PRESENCE" in migration
    assert "MAPPING_GAP" in migration
    assert "BEFORE INSERT OR UPDATE OF examinable_points_inventory_complete" in migration
    assert "examinable-point inventory cannot be complete" in migration
    assert "ol.verification_status = 'VERIFIED'" in migration
    assert "examinable-point review evidence is append-only" in migration


def test_report_is_audited_in_existing_append_only_syllabus_review_table():
    migration = (
        Path(__file__).resolve().parents[1]
        / "database" / "migrations"
        / "0027_phase6_56_examinable_point_coverage.sql"
    ).read_text(encoding="utf-8")
    assert "'EXAMINABLE_POINT'" in migration
    assert "'POINT_CONCEPT'" in migration
    assert "'POINT_DIMENSION'" in migration
    assert "'POINT_LEARNING_ITEM'" in migration


def test_phase_6_56_migration_executes_on_ephemeral_postgres_when_configured(monkeypatch):
    import os
    import pytest

    dsn = os.environ.get("AI_COMP_DATABASE_URL", "").strip()
    if not dsn:
        pytest.skip("AI_COMP_DATABASE_URL is not configured outside the CI database service")

    from ai_comp.database.connection import connect_postgres
    from ai_comp.database.migrate_cli import run_migrations

    # The tests workflow supplies an ephemeral pgvector PostgreSQL service.
    # Never run this integration test against a production Render database.
    if "localhost" not in dsn and "127.0.0.1" not in dsn:
        pytest.skip("migration integration test is restricted to a local CI PostgreSQL service")

    run_migrations(dsn)
    connection = connect_postgres(dsn)
    try:
        rows = connection.execute(
            """SELECT table_name FROM information_schema.tables
               WHERE table_schema = current_schema()
                 AND table_name IN (
                   'exam_syllabus_examinable_points',
                   'exam_syllabus_point_concepts',
                   'exam_syllabus_point_dimensions',
                   'exam_syllabus_point_one_liner_links'
                 )"""
        ).fetchall()
        assert {str(row[0]) for row in rows} == {
            "exam_syllabus_examinable_points",
            "exam_syllabus_point_concepts",
            "exam_syllabus_point_dimensions",
            "exam_syllabus_point_one_liner_links",
        }
        triggers = connection.execute(
            """SELECT COUNT(*) FROM pg_trigger
               WHERE NOT tgisinternal
                 AND tgname IN (
                   'trg_exam_syllabus_points_inventory_lock',
                   'trg_exam_syllabus_point_concept_review_separation',
                   'trg_exam_syllabus_point_dimension_review_separation',
                   'trg_exam_syllabus_point_one_liner_verified'
                 )"""
        ).fetchone()
        assert int(triggers[0]) == 4
    finally:
        connection.close()
