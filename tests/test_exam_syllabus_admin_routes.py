from __future__ import annotations

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


def _client(connection=None):
    app = create_app(learner_identity_provider=lambda _request: "learner-1")
    app.state.question_bank_connection_factory = (lambda: connection) if connection is not None else None
    return TestClient(app)


def test_syllabus_author_endpoint_fails_closed_without_distinct_server_credentials(monkeypatch):
    monkeypatch.delenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", raising=False)
    response = _client().post("/api/v1/admin/exam-syllabi", json={
        "syllabus_id": "test-syllabus",
        "exam_id": "test-exam",
        "source_id": "test-source",
        "source_title": "Synthetic test syllabus",
        "source_url": "https://official.example/test.pdf",
        "version_label": "test-v1",
        "source_evidence": "Synthetic fixture only",
    })
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SYLLABUS_REVIEW_NOT_CONFIGURED"


def test_syllabus_reviewer_identity_is_server_derived_and_missing_token_is_rejected(monkeypatch):
    monkeypatch.setenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", "author-secret")
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", "review-secret")
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEWER_ID", "independent-reviewer")
    response = _client().post(
        "/api/v1/admin/exam-syllabi/test-syllabus/source-review",
        json={"decision": "REJECTED", "review_note": "test only"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SYLLABUS_AUTHENTICATION_REQUIRED"


def test_syllabus_review_rejects_verified_without_digest_evidence_and_inventory():
    response = _client().post(
        "/api/v1/admin/exam-syllabi/test-syllabus/source-review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "review-secret"},
        json={"decision": "VERIFIED", "review_note": "not enough evidence"},
    )
    assert response.status_code == 422


def test_mapping_review_rejects_in_scope_without_source_locator():
    response = _client().post(
        "/api/v1/admin/exam-syllabi/test-syllabus/concept-mappings/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "review-secret"},
        json={"concept_id": "concept-1", "decision": "IN_SCOPE", "review_note": "missing evidence"},
    )
    assert response.status_code == 422


def test_syllabus_migration_creates_append_only_audit_table():
    from pathlib import Path
    migration = Path(__file__).resolve().parents[1] / "database" / "migrations" / "0024_phase6_56_syllabus_review_workflow.sql"
    sql = migration.read_text(encoding="utf-8")
    assert "exam_syllabus_review_audit" in sql
    assert "BEFORE UPDATE OR DELETE" in sql
    assert "BEFORE TRUNCATE" in sql
    assert "append-only" in sql



def test_syllabus_unit_payload_requires_hierarchical_parent_and_source_evidence():
    import pytest
    from pydantic import ValidationError
    from ai_comp.api.exam_syllabus_admin_routes import SyllabusUnitDraft, SyllabusUnitDecision

    with pytest.raises(ValidationError):
        SyllabusUnitDraft(
            unit_id="topic-1", unit_kind="TOPIC", official_label="Topic",
            source_locator="page 1", source_evidence="Synthetic test evidence",
        )
    with pytest.raises(ValidationError):
        SyllabusUnitDraft(
            unit_id="unit-1", unit_kind="UNIT", parent_unit_id="other",
            official_label="Unit", source_locator="page 1", source_evidence="Synthetic test evidence",
        )
    with pytest.raises(ValidationError):
        SyllabusUnitDecision(decision="NEEDS_REVIEW", review_note="cannot be a reviewer decision")


def test_syllabus_unit_inventory_migration_requires_reviewed_rows_before_complete():
    from pathlib import Path
    migration = Path(__file__).resolve().parents[1] / "database" / "migrations" / "0025_phase6_56_syllabus_unit_inventory.sql"
    sql = migration.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS exam_syllabus_units" in sql
    assert "UNIT" in sql and "TOPIC" in sql and "SUBTOPIC" in sql
    assert "review_status <> 'VERIFIED'" in sql
    assert "syllabus inventory cannot be complete until at least one unit exists and every unit is VERIFIED" in sql
    assert "trg_exam_syllabus_units_inventory_lock" in sql
