from __future__ import annotations

from contextlib import contextmanager
from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


class _Cursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row

    def fetchall(self):
        return []


class _Connection:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.closed = False

    @contextmanager
    def transaction(self):
        yield self

    def execute(self, query, params=()):
        self.calls.append((query, params))
        for fragment, response in self.replies:
            if fragment in query:
                return _Cursor(response)
        return _Cursor(None)

    def close(self):
        self.closed = True


def _client(connection=None):
    app = create_app(learner_identity_provider=lambda _request: "learner-1")
    app.state.question_bank_connection_factory = (lambda: connection) if connection is not None else None
    return TestClient(app)


def _configure_tokens(monkeypatch, *, author_id="syllabus-author", reviewer_id="independent-reviewer"):
    monkeypatch.setenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", "syllabus-author-secret")
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", "syllabus-review-secret")
    monkeypatch.setenv("AI_COMP_SYLLABUS_AUTHOR_ID", author_id)
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEWER_ID", reviewer_id)
    monkeypatch.delenv("AI_COMP_CONTENT_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("AI_COMP_CONTENT_REVIEW_TOKEN", raising=False)


def _unit_payload(**overrides):
    return {
        "unit_id": "unit-01",
        "unit_kind": "UNIT",
        "official_label": "History",
        "page_number": 3,
        "source_locator": "p. 3, section 17.1",
        "source_evidence": "Synthetic test fixture evidence",
        "author_note": "Submitted for independent review",
        **overrides,
    }


def test_unit_author_endpoint_fails_closed_without_server_credentials(monkeypatch):
    monkeypatch.delenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", raising=False)
    response = _client().post("/api/v1/admin/exam-syllabi/test-syllabus/units", json=_unit_payload())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SYLLABUS_REVIEW_NOT_CONFIGURED"


def test_unit_hierarchy_rejects_topic_without_parent_before_database_access():
    response = _client().post(
        "/api/v1/admin/exam-syllabi/test-syllabus/units",
        json=_unit_payload(unit_kind="TOPIC"),
    )
    assert response.status_code == 422


def test_author_creates_unit_as_needs_review_and_audits_it(monkeypatch):
    _configure_tokens(monkeypatch, author_id="author-1", reviewer_id="reviewer-1")
    connection = _Connection([
        ("SELECT source_status, syllabus_inventory_complete", ("REVIEW_PENDING", False)),
    ])
    response = _client(connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/units",
        headers={"X-AI-COMP-Syllabus-Admin-Token": "syllabus-author-secret"},
        json=_unit_payload(),
    )
    assert response.status_code == 201, response.text
    assert response.json()["review_status"] == "NEEDS_REVIEW"
    unit_insert = next((q, p) for q, p in connection.calls if "INSERT INTO exam_syllabus_units" in q)
    assert "'NEEDS_REVIEW'" in unit_insert[0]
    assert any("'SYLLABUS_UNIT'" in query for query, _ in connection.calls)
    assert connection.closed


def test_reviewer_can_review_unit_authored_by_a_different_server_identity(monkeypatch):
    _configure_tokens(monkeypatch, author_id="author-1", reviewer_id="reviewer-1")
    connection = _Connection([
        ("SELECT source_status, syllabus_inventory_complete", ("REVIEW_PENDING", False)),
        ("FROM exam_syllabus_units", ("unit-01", "UNIT", "History", 3, "p. 3, section 17.1", "Synthetic evidence", "NEEDS_REVIEW", "author-1")),
    ])
    response = _client(connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/units/unit-01/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "syllabus-review-secret"},
        json={"decision": "VERIFIED", "review_note": "Independently checked against the cited document"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["review_status"] == "VERIFIED"
    assert any("UPDATE exam_syllabus_units" in query for query, _ in connection.calls)
    assert connection.closed


def test_unit_author_cannot_review_their_own_inventory_record(monkeypatch):
    _configure_tokens(monkeypatch, author_id="author-1", reviewer_id="reviewer-1")
    connection = _Connection([
        ("SELECT source_status, syllabus_inventory_complete", ("REVIEW_PENDING", False)),
        ("FROM exam_syllabus_units", ("unit-01", "UNIT", "History", 3, "p. 3, section 17.1", "Synthetic evidence", "NEEDS_REVIEW", "reviewer-1")),
    ])
    response = _client(connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/units/unit-01/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "syllabus-review-secret"},
        json={"decision": "VERIFIED", "review_note": "Attempted self-review"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INDEPENDENT_REVIEW_REQUIRED"
    assert not any("UPDATE exam_syllabus_units" in query for query, _ in connection.calls)


def test_inventory_cannot_be_attested_complete_while_any_unit_is_pending(monkeypatch):
    _configure_tokens(monkeypatch, author_id="author-1", reviewer_id="reviewer-1")
    connection = _Connection([
        ("SELECT syllabus_id FROM exam_syllabus_documents", ("test-syllabus",)),
        ("SELECT actor_id FROM exam_syllabus_review_audit", ("author-1",)),
        ("FROM exam_syllabus_source_fetches", ("fetch-1", "a" * 64, "https://rssb.rajasthan.gov.in/syllabus.pdf", "https://rssb.rajasthan.gov.in/syllabus.pdf", 1234, 3, "CET Syllabus", "2026-10-23T10:00:00Z", "FETCHED")),
        ("SELECT source_url FROM exam_syllabus_documents", ("https://rssb.rajasthan.gov.in/syllabus.pdf",)),
        ("SELECT COUNT(*)", (4, 1)),
    ])
    response = _client(connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/source-review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "syllabus-review-secret"},
        json={
            "decision": "VERIFIED",
            "document_sha256": "a" * 64,
            "source_evidence": "Document and version were independently reviewed",
            "inventory_complete": True,
            "inventory_review_note": "Unit inventory manually reconciled",
            "review_note": "Verification attempted while some units remain pending",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SYLLABUS_INVENTORY_INCOMPLETE"
    assert not any("UPDATE exam_syllabus_documents" in query for query, _ in connection.calls)


def test_inventory_migration_tracks_hierarchy_and_guards_complete_attestation():
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[1]
        / "database"
        / "migrations"
        / "0025_phase6_56_syllabus_unit_inventory.sql"
    ).read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS exam_syllabus_units" in migration
    assert "UNIT', 'TOPIC', 'SUBTOPIC" in migration
    assert "REFERENCES exam_syllabus_units(syllabus_id, unit_id)" in migration
    assert "review_status <> 'VERIFIED'" in migration
    assert "BEFORE INSERT OR UPDATE OF syllabus_inventory_complete" in migration
    assert "syllabus inventory cannot be complete until at least one unit exists and every unit is VERIFIED" in migration
    assert "SYLLABUS_UNIT" in migration
    assert "BEFORE TRUNCATE" not in migration  # Append-only triggers live in migration 0024.


def test_author_cannot_downgrade_a_reviewed_concept_mapping(monkeypatch):
    _configure_tokens(monkeypatch, author_id="author-1", reviewer_id="reviewer-1")
    connection = _Connection([
        ("SELECT syllabus_id FROM exam_syllabus_documents", ("test-syllabus",)),
        ("SELECT applicability_status FROM exam_concept_applicability", ("IN_SCOPE",)),
    ])
    response = _client(connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/concept-mappings",
        headers={"X-AI-COMP-Syllabus-Admin-Token": "syllabus-author-secret"},
        json={
            "concept_id": "concept-1",
            "decision": "NEEDS_REVIEW",
            "official_unit": "Unit 1",
            "source_locator": "p. 3",
            "source_evidence": "Evidence",
            "review_note": "Proposed edit",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MAPPING_ALREADY_REVIEWED"
    assert not any("INSERT INTO exam_concept_applicability" in query for query, _ in connection.calls)


def test_verified_inventory_item_must_be_reopened_by_reviewer_before_edit(monkeypatch):
    _configure_tokens(monkeypatch, author_id="author-1", reviewer_id="reviewer-1")
    connection = _Connection([
        ("SELECT source_status, syllabus_inventory_complete", ("REVIEW_PENDING", False)),
        ("SELECT review_status FROM exam_syllabus_units", ("VERIFIED",)),
    ])
    response = _client(connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/units",
        headers={"X-AI-COMP-Syllabus-Admin-Token": "syllabus-author-secret"},
        json=_unit_payload(),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SYLLABUS_UNIT_ALREADY_VERIFIED"
    assert not any("INSERT INTO exam_syllabus_units" in query for query, _ in connection.calls)


def test_source_review_can_attest_complete_only_when_every_inventory_row_is_verified(monkeypatch):
    _configure_tokens(monkeypatch, author_id="author-1", reviewer_id="reviewer-1")
    connection = _Connection([
        ("SELECT syllabus_id FROM exam_syllabus_documents", ("test-syllabus",)),
        ("SELECT actor_id FROM exam_syllabus_review_audit", ("author-1",)),
        ("FROM exam_syllabus_source_fetches", ("fetch-2", "b" * 64, "https://rssb.rajasthan.gov.in/syllabus.pdf", "https://rssb.rajasthan.gov.in/syllabus.pdf", 2000, 3, "CET Syllabus", "2026-10-23T10:00:00Z", "FETCHED")),
        ("SELECT source_url FROM exam_syllabus_documents", ("https://rssb.rajasthan.gov.in/syllabus.pdf",)),
        ("SELECT COUNT(*)", (3, 0)),
    ])
    response = _client(connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/source-review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "syllabus-review-secret"},
        json={
            "decision": "VERIFIED",
            "document_sha256": "b" * 64,
            "source_evidence": "Independently checked exact official notification bytes and revision",
            "inventory_complete": True,
            "inventory_review_note": "Three inventory rows checked against every relevant page",
            "review_note": "All inventory rows independently verified",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["source_status"] == "VERIFIED"
    assert any("UPDATE exam_syllabus_documents" in query for query, _ in connection.calls)
