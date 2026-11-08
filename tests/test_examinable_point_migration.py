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
    assert "one_liner.verification_status = 'VERIFIED'" in migration
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
