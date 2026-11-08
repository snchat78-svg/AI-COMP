from __future__ import annotations

from contextlib import contextmanager
from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


class _Cursor:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class _Connection:
    def __init__(self, replies=()):
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
                if isinstance(response, list):
                    rows = response
                elif response is None or response == ():
                    rows = []
                else:
                    rows = [response]
                return _Cursor(rows)
        return _Cursor()

    def close(self):
        self.closed = True


def _client(connection=None):
    app = create_app()
    app.state.question_bank_connection_factory = (lambda: connection) if connection is not None else None
    return TestClient(app)


def _tokens(monkeypatch, *, author_id="author-1", reviewer_id="reviewer-1"):
    monkeypatch.setenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", "author-secret")
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", "reviewer-secret")
    monkeypatch.setenv("AI_COMP_SYLLABUS_AUTHOR_ID", author_id)
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEWER_ID", reviewer_id)
    monkeypatch.delenv("AI_COMP_CONTENT_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("AI_COMP_CONTENT_REVIEW_TOKEN", raising=False)


def _point_payload(**overrides):
    return {
        "point_id": "point-01",
        "unit_id": "unit-01",
        "point_type": "FACT",
        "point_statement": "Synthetic point statement",
        "page_number": 4,
        "source_locator": "p. 4, heading 2",
        "source_evidence": "Synthetic fixture excerpt only",
        "concept_ids": ["concept-1"],
        "author_note": "Submitted for independent review",
        **overrides,
    }


def _dimensions(*, gap=False):
    rows = [
        {"dimension_key": "PRESENCE", "assessment": "APPLICABLE"},
        {"dimension_key": "CORRECTNESS", "assessment": "APPLICABLE"},
        {"dimension_key": "ATOMICITY", "assessment": "APPLICABLE"},
        {"dimension_key": "RECALL_DEPTH", "assessment": "APPLICABLE"},
        {"dimension_key": "APPLICATION", "assessment": "NOT_APPLICABLE", "assessment_reason": "No application is required by this synthetic point."},
        {"dimension_key": "DISCRIMINATION", "assessment": "NOT_APPLICABLE", "assessment_reason": "No contrast is required by this synthetic point."},
        {"dimension_key": "LANGUAGE", "assessment": "APPLICABLE"},
        {"dimension_key": "PROVENANCE", "assessment": "APPLICABLE"},
        {"dimension_key": "DUPLICATION", "assessment": "GAP" if gap else "APPLICABLE",
         **({"assessment_reason": "A possible duplicate remains to be checked."} if gap else {})},
    ]
    return rows


def test_point_author_endpoint_requires_separate_syllabus_credentials(monkeypatch):
    monkeypatch.delenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", raising=False)
    response = _client().post(
        "/api/v1/admin/exam-syllabi/test-syllabus/examinable-points",
        json=_point_payload(),
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SYLLABUS_REVIEW_NOT_CONFIGURED"


def test_point_candidate_requires_concept_mapping_or_explicit_mapping_gap():
    response = _client().post(
        "/api/v1/admin/exam-syllabi/test-syllabus/examinable-points",
        json=_point_payload(concept_ids=[], mapping_gap_reason=""),
    )
    assert response.status_code == 422


def test_point_author_creates_only_needs_review_candidate(monkeypatch):
    _tokens(monkeypatch)
    connection = _Connection([
        ("SELECT source_status, syllabus_inventory_complete", ("VERIFIED", True, False)),
        ("SELECT unit_kind, review_status", ("UNIT", "VERIFIED")),
        ("SELECT review_status FROM exam_syllabus_examinable_points", ()),
    ])
    response = _client(connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/examinable-points",
        headers={"X-AI-COMP-Syllabus-Admin-Token": "author-secret"},
        json=_point_payload(),
    )
    assert response.status_code == 201, response.text
    assert response.json()["review_status"] == "NEEDS_REVIEW"
    assert any("INSERT INTO exam_syllabus_examinable_points" in query for query, _ in connection.calls)
    assert any("INSERT INTO exam_syllabus_point_concepts" in query for query, _ in connection.calls)
    assert any("'EXAMINABLE_POINT'" in query for query, _ in connection.calls)
    assert connection.closed


def test_point_reviewer_cannot_review_own_authored_point(monkeypatch):
    _tokens(monkeypatch, author_id="author-1", reviewer_id="reviewer-1")
    connection = _Connection([
        ("SELECT source_status, syllabus_inventory_complete", ("VERIFIED", True, False)),
        ("SELECT created_by, mapping_gap_reason", ("reviewer-1", "", "NEEDS_REVIEW")),
    ])
    response = _client(connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/examinable-points/point-01/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "reviewer-secret"},
        json={"decision": "VERIFIED", "review_note": "attempt", "dimensions": _dimensions()},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INDEPENDENT_REVIEW_REQUIRED"
    assert connection.closed


def test_point_review_requires_all_nine_distinct_dimensions():
    response = _client().post(
        "/api/v1/admin/exam-syllabi/test-syllabus/examinable-points/point-01/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "reviewer-secret"},
        json={"decision": "VERIFIED", "review_note": "review", "dimensions": _dimensions()[:-1]},
    )
    assert response.status_code == 422


def test_independent_point_review_records_dimensions_and_mapping(monkeypatch):
    _tokens(monkeypatch)
    connection = _Connection([
        ("SELECT source_status, syllabus_inventory_complete", ("VERIFIED", True, False)),
        ("SELECT created_by, mapping_gap_reason", ("author-1", "", "NEEDS_REVIEW")),
        ("SELECT concept_id FROM exam_syllabus_point_concepts", [("concept-1",)]),
    ])
    response = _client(connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/examinable-points/point-01/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "reviewer-secret"},
        json={"decision": "VERIFIED", "review_note": "Independently checked against synthetic fixture.",
              "dimensions": _dimensions()},
    )
    assert response.status_code == 200, response.text
    assert response.json()["mapping_status"] == "MAPPED"
    assert response.json()["review_status"] == "VERIFIED"
    assert sum("INSERT INTO exam_syllabus_point_dimensions" in query for query, _ in connection.calls) == 9
    assert any("UPDATE exam_syllabus_point_concepts" in query for query, _ in connection.calls)
    assert any("UPDATE exam_syllabus_examinable_points" in query for query, _ in connection.calls)
    assert connection.closed


def test_point_with_open_dimension_gap_cannot_be_verified():
    response = _client().post(
        "/api/v1/admin/exam-syllabi/test-syllabus/examinable-points/point-01/review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "reviewer-secret"},
        json={"decision": "VERIFIED", "review_note": "review",
              "dimensions": _dimensions(gap=True)},
    )
    assert response.status_code == 422


def test_gap_report_requires_independent_reviewer_auth(monkeypatch):
    _tokens(monkeypatch)
    response = _client().get(
        "/api/v1/admin/exam-syllabi/test-syllabus/examinable-point-gap-report"
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SYLLABUS_AUTHENTICATION_REQUIRED"


def test_gap_report_returns_unknown_until_both_inventories_are_complete(monkeypatch):
    _tokens(monkeypatch)
    connection = _Connection([
        ("FROM exam_syllabus_documents", ("TEST_EXAM", "REVIEW_PENDING", False, False, None, None, "")),
        ("AS total_points", (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
        ("SELECT point_id, unit_id", []),
    ])
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
