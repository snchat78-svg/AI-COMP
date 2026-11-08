from __future__ import annotations

from contextlib import contextmanager
from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class _Connection:
    def __init__(self, source=None):
        self.source = source
        self.calls = []
        self.closed = False

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if "FROM exam_syllabus_documents" in query:
            return _Cursor([] if self.source is None else [self.source])
        if "AS total_points" in query:
            return _Cursor([(1, 1, 0, 1, 1, 1, 0, 0, 0, 0)])
        if "SELECT point_id, unit_id" in query:
            return _Cursor([])
        raise AssertionError(f"unexpected SQL: {query}")

    def close(self):
        self.closed = True


def _client(connection=None):
    app = create_app()
    app.state.question_bank_connection_factory = (lambda: connection) if connection is not None else None
    return TestClient(app)


def _tokens(monkeypatch):
    monkeypatch.setenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", "author-secret")
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", "reviewer-secret")
    monkeypatch.setenv("AI_COMP_SYLLABUS_AUTHOR_ID", "author-1")
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEWER_ID", "reviewer-1")
    monkeypatch.delenv("AI_COMP_CONTENT_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("AI_COMP_CONTENT_REVIEW_TOKEN", raising=False)


def test_gap_report_requires_independent_reviewer_auth(monkeypatch):
    _tokens(monkeypatch)
    response = _client().get(
        "/api/v1/admin/exam-syllabi/test-syllabus/examinable-point-gap-report"
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SYLLABUS_AUTHENTICATION_REQUIRED"


def test_gap_report_returns_unknown_until_both_inventories_are_complete(monkeypatch):
    _tokens(monkeypatch)
    connection = _Connection(
        ("TEST_EXAM", "REVIEW_PENDING", False, False, None, None, "")
    )
    response = _client(connection).get(
        "/api/v1/admin/exam-syllabi/test-syllabus/examinable-point-gap-report",
        headers={"X-AI-COMP-Syllabus-Review-Token": "reviewer-secret"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["coverage_percentage"] is None
    assert payload["coverage_label"] == "COVERAGE UNKNOWN — INVENTORY INCOMPLETE"
    assert payload["generated_by"] == "reviewer-1"
    assert connection.closed


def test_gap_report_404s_unknown_syllabus_and_closes_connection(monkeypatch):
    _tokens(monkeypatch)
    connection = _Connection()
    response = _client(connection).get(
        "/api/v1/admin/exam-syllabi/missing/examinable-point-gap-report",
        headers={"X-AI-COMP-Syllabus-Review-Token": "reviewer-secret"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SYLLABUS_NOT_FOUND"
    assert connection.closed


def test_gap_report_bounds_page_size(monkeypatch):
    _tokens(monkeypatch)
    response = _client().get(
        "/api/v1/admin/exam-syllabi/test/examinable-point-gap-report?limit=101",
        headers={"X-AI-COMP-Syllabus-Review-Token": "reviewer-secret"},
    )
    assert response.status_code == 422
