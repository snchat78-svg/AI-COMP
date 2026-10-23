from pathlib import Path


def test_phase_6_56_syllabus_review_migration_has_full_inventory_and_append_only_audit():
    root = Path(__file__).resolve().parents[1]
    migration = (
        root
        / "database"
        / "migrations"
        / "0024_phase6_56_syllabus_review_workflow.sql"
    ).read_text(encoding="utf-8")

    assert "ALTER TABLE exam_concept_applicability" in migration
    assert "proposed_status" in migration
    assert "CREATE TABLE IF NOT EXISTS exam_syllabus_inventory_units" in migration
    assert "CREATE TABLE IF NOT EXISTS exam_syllabus_unit_concepts" in migration
    assert "CREATE TABLE IF NOT EXISTS exam_syllabus_review_audit" in migration
    assert "review_status TEXT NOT NULL DEFAULT 'NEEDS_REVIEW'" in migration
    assert "reviewed_by TEXT" in migration
    assert "source_locator TEXT NOT NULL" in migration
    assert "source_evidence TEXT NOT NULL" in migration
    assert "CREATE TRIGGER trg_exam_syllabus_audit_no_update" in migration
    assert "BEFORE UPDATE OR DELETE ON exam_syllabus_review_audit" in migration
    assert "RAISE EXCEPTION 'exam_syllabus_review_audit is append-only'" in migration
    assert "INSERT INTO exam_syllabus_documents" not in migration
    assert "source_status = 'VERIFIED'" not in migration


def test_syllabus_admin_routes_use_separate_server_author_and_reviewer_credentials():
    root = Path(__file__).resolve().parents[1]
    source = (
        root / "src" / "ai_comp" / "api" / "exam_syllabus_admin_routes.py"
    ).read_text(encoding="utf-8")

    assert 'AI_COMP_SYLLABUS_ADMIN_TOKEN' in source
    assert 'AI_COMP_SYLLABUS_REVIEW_TOKEN' in source
    assert 'AI_COMP_SYLLABUS_AUTHOR_ID' in source
    assert 'AI_COMP_SYLLABUS_REVIEWER_ID' in source
    assert 'X-AI-COMP-Syllabus-Admin-Token' in source
    assert 'X-AI-COMP-Syllabus-Review-Token' in source
    assert 'hmac.compare_digest(author_token, review_token)' in source
    assert 'reviewed_by = %s' in source
    assert 'SYLLABUS_REVIEW_GATES_NOT_MET' in source
    assert '"reviewer_id"' not in source
