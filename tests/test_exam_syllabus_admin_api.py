from __future__ import annotations

from contextlib import nullcontext

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


_AUTHOR_TOKEN = "configured-syllabus-admin-token"
_REVIEW_TOKEN = "configured-syllabus-review-token"
_AUTHOR_ID = "syllabus-editor-1"
_REVIEWER_ID = "syllabus-reviewer-1"


def _document_payload(**overrides):
    return {
        "syllabus_id": "TEST_SYLLABUS_001",
        "exam_id": "TEST_EXAM_001",
        "source_id": "TEST_OFFICIAL_SOURCE",
        "source_title": "Synthetic test notification and syllabus",
        "source_url": "https://official.example/notice.pdf",
        "notification_number": "TEST/001",
        "version_label": "synthetic-v1",
        "source_evidence": "Synthetic source lead; not official or verified.",
        **overrides,
    }


def _set_author(monkeypatch):
    monkeypatch.setenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", _AUTHOR_TOKEN)
    monkeypatch.setenv("AI_COMP_SYLLABUS_AUTHOR_ID", _AUTHOR_ID)


def _set_reviewer(monkeypatch):
    _set_author(monkeypatch)
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", _REVIEW_TOKEN)
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEWER_ID", _REVIEWER_ID)


class _Cursor:
    def __init__(self, rows=()):
        self._rows = list(rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, mode="default"):
        self.mode = mode
        self.calls = []
        self.closed = False
        self.audit_rows = []
        self.inserted_units = []
        self.updated_sql = []

    def transaction(self):
        return nullcontext(self)

    def execute(self, query, params=()):
        self.calls.append((query, params))
        normalized = " ".join(query.split())

        if "SELECT exam_id FROM exams" in normalized:
            return _Cursor([("TEST_EXAM_001",)])
        if "SELECT base_url, source_type, allowed_paths FROM sources" in normalized:
            return _Cursor([("https://official.example", "OFFICIAL_WEBSITE", [])])
        if "SELECT source_status FROM exam_syllabus_documents" in normalized and "FOR UPDATE" in normalized:
            return _Cursor([("REVIEW_PENDING",)])
        if "SELECT source_status, document_sha256" in normalized:
            digest = None if self.mode != "doc_digest" else "b" * 64
            return _Cursor([("REVIEW_PENDING", digest)])
        if "SELECT COUNT(*) FROM exam_syllabus_inventory_units WHERE" in normalized:
            return _Cursor([(0,)])
        if "SELECT COUNT(*) FROM exam_concept_applicability WHERE" in normalized:
            return _Cursor([(0,)])
        if "SELECT COUNT(*) FROM exam_syllabus_unit_concepts WHERE" in normalized:
            return _Cursor([(0,)])
        if "SELECT source_locator, source_evidence FROM exam_syllabus_inventory_units" in normalized:
            return _Cursor([("Page 2, Unit I", "Official heading: Unit I.")])
        if "SELECT proposed_status, source_locator, source_evidence FROM exam_concept_applicability" in normalized:
            return _Cursor([("IN_SCOPE", "Page 2, Unit I", "Official heading: Unit I.")])
        if "SELECT review_status FROM exam_syllabus_unit_concepts" in normalized and "FOR UPDATE" in normalized:
            return _Cursor([("NEEDS_REVIEW",)])
        if "FROM exam_syllabus_inventory_units AS u" in normalized and "COUNT(*) FILTER" in normalized:
            if self.mode == "complete":
                return _Cursor([(2, 0, 0)])
            return _Cursor([(0, 0, 0)])
        if "FROM concepts AS c" in normalized and "LEFT JOIN exam_concept_applicability AS a" in normalized:
            if self.mode == "complete":
                return _Cursor([(340, 0, 0)])
            return _Cursor([(340, 340, 0)])
        if "SELECT COUNT(*)::INTEGER FROM exam_syllabus_unit_concepts" in normalized:
            return _Cursor([(0,)])
        if "INSERT INTO exam_syllabus_review_audit" in normalized:
            self.audit_rows.append(params)
            return _Cursor()
        if "INSERT INTO exam_syllabus_inventory_units" in normalized:
            self.inserted_units.append(params)
            return _Cursor()
        if "INSERT INTO exam_syllabus_documents" in normalized:
            self.updated_sql.append(normalized)
            return _Cursor()
        if "UPDATE exam_syllabus_documents" in normalized or "UPDATE exam_syllabus_inventory_units" in normalized or "UPDATE exam_concept_applicability" in normalized or "UPDATE exam_syllabus_unit_concepts" in normalized:
            self.updated_sql.append(normalized)
            return _Cursor()
        if normalized.startswith("SELECT COUNT(*)") and "exam_syllabus_inventory_units" in normalized:
            return _Cursor([(0,)])
        raise AssertionError(f"unexpected SQL: {normalized}")

    def close(self):
        self.closed = True


def _client(connection=None):
    app = create_app()
    if connection is not None:
        app.state.question_bank_connection_factory = lambda: connection
    return TestClient(app)


def test_syllabus_authoring_fails_closed_without_server_secret(monkeypatch):
    monkeypatch.delenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("AI_COMP_SYLLABUS_AUTHOR_ID", raising=False)
    response = _client().post(
        "/api/v1/admin/question-bank/exam-syllabus/documents",
        json=_document_payload(),
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SYLLABUS_AUTHORING_NOT_CONFIGURED"


def test_syllabus_document_authoring_rejects_wrong_token(monkeypatch):
    _set_author(monkeypatch)
    response = _client().post(
        "/api/v1/admin/question-bank/exam-syllabus/documents",
        headers={"X-AI-COMP-Syllabus-Admin-Token": "wrong"},
        json=_document_payload(),
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SYLLABUS_AUTHOR_AUTHENTICATION_REQUIRED"


def test_syllabus_document_authoring_saves_only_pending_source_and_audits_author(monkeypatch):
    _set_author(monkeypatch)
    connection = _Connection()
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents",
        headers={"X-AI-COMP-Syllabus-Admin-Token": _AUTHOR_TOKEN},
        json=_document_payload(document_sha256="a" * 64),
    )

    assert response.status_code == 201, response.text
    assert response.json()["source_status"] == "REVIEW_PENDING"
    assert response.json()["syllabus_inventory_complete"] is False
    insert_sql = next(sql for sql, _ in connection.calls if "INSERT INTO exam_syllabus_documents" in sql)
    assert "'REVIEW_PENDING'" in insert_sql
    assert "VERIFIED" not in insert_sql
    assert len(connection.audit_rows) == 1
    audit = connection.audit_rows[0]
    assert audit[2] == "AUTHOR"
    assert audit[3] == _AUTHOR_ID
    assert audit[4] == "SOURCE_SUBMITTED"
    assert connection.closed


def test_syllabus_document_rejects_url_outside_registered_official_host(monkeypatch):
    _set_author(monkeypatch)
    connection = _Connection()
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents",
        headers={"X-AI-COMP-Syllabus-Admin-Token": _AUTHOR_TOKEN},
        json=_document_payload(source_url="https://other.example/notice.pdf"),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SYLLABUS_SOURCE_HOST_NOT_ALLOWED"
    assert not any("INSERT INTO exam_syllabus_documents" in sql for sql, _ in connection.calls)


def test_syllabus_document_rejects_malformed_https_url_before_database_access():
    connection = _Connection()
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents",
        headers={"X-AI-COMP-Syllabus-Admin-Token": _AUTHOR_TOKEN},
        json=_document_payload(source_url="https://"),
    )
    assert response.status_code == 422
    assert connection.calls == []


def test_author_submits_whole_inventory_as_unreviewed_rows(monkeypatch):
    _set_author(monkeypatch)
    connection = _Connection()
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents/TEST_SYLLABUS_001/inventory",
        headers={"X-AI-COMP-Syllabus-Admin-Token": _AUTHOR_TOKEN},
        json={
            "submission_note": "Extracted every listed heading for review.",
            "units": [
                {
                    "unit_id": "unit-1", "parent_unit_id": None, "unit_kind": "UNIT",
                    "official_label": "Unit I", "source_locator": "Page 2, heading Unit I",
                    "source_evidence": "Exact official heading text.", "order_index": 0,
                },
                {
                    "unit_id": "topic-1", "parent_unit_id": "unit-1", "unit_kind": "TOPIC",
                    "official_label": "Topic A", "source_locator": "Page 2, Unit I, Topic A",
                    "source_evidence": "Exact official topic text.", "order_index": 1,
                },
            ],
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["submitted_unit_count"] == 2
    assert response.json()["review_status"] == "NEEDS_REVIEW"
    assert len(connection.inserted_units) == 2
    assert all("NEEDS_REVIEW" in sql for sql, _ in connection.calls if "INSERT INTO exam_syllabus_inventory_units" in sql)
    assert all(params[-1] == _AUTHOR_ID for params in connection.inserted_units)
    assert connection.audit_rows[0][4] == "INVENTORY_SUBMITTED"


def test_inventory_hierarchy_must_be_parent_first(monkeypatch):
    _set_author(monkeypatch)
    connection = _Connection()
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents/TEST_SYLLABUS_001/inventory",
        headers={"X-AI-COMP-Syllabus-Admin-Token": _AUTHOR_TOKEN},
        json={
            "submission_note": "Inventory hierarchy test.",
            "units": [
                {
                    "unit_id": "child", "parent_unit_id": "parent", "unit_kind": "TOPIC",
                    "official_label": "Child", "source_locator": "p.2", "source_evidence": "Topic.",
                    "order_index": 0,
                },
                {
                    "unit_id": "parent", "parent_unit_id": None, "unit_kind": "UNIT",
                    "official_label": "Parent", "source_locator": "p.1", "source_evidence": "Unit.",
                    "order_index": 1,
                },
            ],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INVENTORY_HIERARCHY"
    assert connection.calls == []


def test_reviewer_fails_closed_without_distinct_server_credentials(monkeypatch):
    monkeypatch.setenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", _AUTHOR_TOKEN)
    monkeypatch.setenv("AI_COMP_SYLLABUS_AUTHOR_ID", _AUTHOR_ID)
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", _AUTHOR_TOKEN)
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEWER_ID", _REVIEWER_ID)
    connection = _Connection()
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents/TEST_SYLLABUS_001/inventory-units/unit-1/review",
        json={"decision": "VERIFIED", "review_note": "Checked unit evidence carefully."},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SYLLABUS_REVIEW_NOT_CONFIGURED"
    assert connection.calls == []


def test_reviewer_rejects_wrong_token_and_never_uses_body_identity(monkeypatch):
    _set_reviewer(monkeypatch)
    connection = _Connection()
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents/TEST_SYLLABUS_001/inventory-units/unit-1/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "wrong"},
        json={"decision": "VERIFIED", "review_note": "Checked official source."},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SYLLABUS_REVIEW_AUTHENTICATION_REQUIRED"
    assert connection.calls == []

    body_identity = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents/TEST_SYLLABUS_001/inventory-units/unit-1/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": _REVIEW_TOKEN},
        json={"decision": "VERIFIED", "review_note": "Checked official source.", "reviewer_id": "attacker"},
    )
    assert body_identity.status_code == 422
    assert connection.calls == []


def test_inventory_review_uses_server_reviewer_id_and_writes_audit(monkeypatch):
    _set_reviewer(monkeypatch)
    connection = _Connection()
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents/TEST_SYLLABUS_001/inventory-units/unit-1/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": _REVIEW_TOKEN},
        json={"decision": "VERIFIED", "review_note": "Compared label and locator with official PDF."},
    )
    assert response.status_code == 200, response.text
    assert response.json()["reviewed_by"] == _REVIEWER_ID
    update = next(sql for sql, _ in connection.calls if "UPDATE exam_syllabus_inventory_units" in sql)
    assert "reviewed_by = %s" in update
    assert connection.audit_rows[0][2] == "REVIEWER"
    assert connection.audit_rows[0][3] == _REVIEWER_ID
    assert connection.audit_rows[0][4] == "INVENTORY_UNIT_REVIEWED"
    assert connection.closed


def test_concept_applicability_review_requires_cited_evidence(monkeypatch):
    _set_reviewer(monkeypatch)
    connection = _Connection()
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents/TEST_SYLLABUS_001/concepts/concept-1/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": _REVIEW_TOKEN},
        json={
            "decision": "IN_SCOPE",
            "source_locator": "Page 2, Unit I",
            "source_evidence": "Unit I explicitly includes this concept.",
            "review_note": "Independently matched concept to the official unit.",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["applicability_status"] == "IN_SCOPE"
    assert response.json()["reviewed_by"] == _REVIEWER_ID
    update = next(sql for sql, _ in connection.calls if "UPDATE exam_concept_applicability" in sql)
    assert "reviewed_by = %s" in update
    assert connection.audit_rows[0][4] == "CONCEPT_APPLICABILITY_REVIEWED"


def test_syllabus_finalize_refuses_incomplete_inventory_and_concepts(monkeypatch):
    _set_reviewer(monkeypatch)
    connection = _Connection(mode="blocked")
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents/TEST_SYLLABUS_001/finalize",
        headers={"X-AI-COMP-Syllabus-Review-Token": _REVIEW_TOKEN},
        json={
            "confirmed_document_sha256": "a" * 64,
            "source_evidence": "Official notification, section 17, source details.",
            "source_review_note": "Retrieved the official bytes over validated HTTPS and independently computed SHA-256.",
            "inventory_review_note": "Compared every official heading and subheading against the extracted complete inventory.",
        },
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "SYLLABUS_REVIEW_GATES_NOT_MET"
    assert any("complete official unit inventory" in item for item in response.json()["error"]["missing_gates"])
    assert not any("UPDATE exam_syllabus_documents" in sql for sql, _ in connection.calls)
    assert connection.audit_rows == []
    assert connection.closed


def test_syllabus_finalize_attests_hash_and_full_inventory_only_after_all_gates(monkeypatch):
    _set_reviewer(monkeypatch)
    connection = _Connection(mode="complete")
    response = _client(connection).post(
        "/api/v1/admin/question-bank/exam-syllabus/documents/TEST_SYLLABUS_001/finalize",
        headers={"X-AI-COMP-Syllabus-Review-Token": _REVIEW_TOKEN},
        json={
            "confirmed_document_sha256": "a" * 64,
            "source_evidence": "Official notification, section 17, source URL and version confirmed.",
            "source_review_note": "Retrieved the official bytes over validated HTTPS and independently computed SHA-256.",
            "inventory_review_note": "Every unit is mapped and every canonical concept has a reviewed scope decision.",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["source_status"] == "VERIFIED"
    assert response.json()["syllabus_inventory_complete"] is True
    assert response.json()["selection_ready"] is True
    final_update = next(sql for sql, _ in connection.calls if "UPDATE exam_syllabus_documents" in sql)
    assert "source_status = 'VERIFIED'" in final_update
    assert "syllabus_inventory_complete = TRUE" in final_update
    assert len(connection.audit_rows) == 1
    audit = connection.audit_rows[0]
    assert audit[2] == "REVIEWER"
    assert audit[3] == _REVIEWER_ID
    assert audit[4] == "SYLLABUS_FINALIZED"
    assert audit[7] == "VERIFIED"
    assert connection.closed
