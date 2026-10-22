from __future__ import annotations

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


_PROFILE_ROW = (
    "RSSB_CET_GRADUATION_2026",
    "Rajasthan Common Eligibility Test (Graduation Level) 2026",
    "RSSB_CET_GRADUATION_2026_ADVT_09_2026",
    "Common Eligibility Test (Graduation Level) 2026 — syllabus clause",
    "https://rssb.rajasthan.gov.in/storage/advertisement_item/1782966142.pdf",
    "Advertisement No. 09/2026",
    "REVIEW_PENDING",
    340,
    0,
    0,
)


class _Cursor:
    def __init__(self, rows):
        self._rows = list(rows)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _Connection:
    def __init__(self, *, profile_rows=None, exists=True):
        self.profile_rows = [_PROFILE_ROW] if profile_rows is None else profile_rows
        self.exists = exists
        self.calls = []
        self.closed = False

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if "SELECT 1" in query and "FROM exams AS e" in query:
            return _Cursor([(1,)] if self.exists else [])
        if "FROM exams AS e" in query and "COUNT(DISTINCT c.concept_id)" in query:
            return _Cursor(self.profile_rows)
        if "FROM concepts AS c" in query:
            return _Cursor([])
        raise AssertionError(f"unexpected SQL: {query}")

    def close(self):
        self.closed = True


def _client(connection, identity="learner-1"):
    app = create_app(learner_identity_provider=lambda _request: identity)
    app.state.question_bank_connection_factory = lambda: connection
    return TestClient(app)


def test_exam_profiles_endpoint_exposes_pending_mapping_without_claiming_ready():
    connection = _Connection()
    client = _client(connection)

    response = client.get("/api/v1/learners/learner-1/question-bank/exam-profiles")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["items"]) == 1
    profile = payload["items"][0]
    assert profile["exam_id"] == "RSSB_CET_GRADUATION_2026"
    assert profile["source_status"] == "REVIEW_PENDING"
    assert profile["concept_count"] == 340
    assert profile["mapped_concept_count"] == 0
    assert profile["unmapped_concept_count"] == 340
    assert profile["selection_ready"] is False
    assert connection.closed


def test_subject_endpoint_returns_no_generic_subjects_for_unmapped_exam_profile():
    connection = _Connection()
    client = _client(connection)

    response = client.get(
        "/api/v1/learners/learner-1/question-bank/subjects",
        params={"exam_id": "RSSB_CET_GRADUATION_2026"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["items"] == []
    assert any("d.source_status = 'VERIFIED'" in query for query, _ in connection.calls)
    assert connection.closed


def test_topics_endpoint_rejects_unknown_exam_profile_before_loading_topics():
    connection = _Connection(exists=False)
    client = _client(connection)

    response = client.get(
        "/api/v1/learners/learner-1/question-bank/topics",
        params={
            "subject": "Rajasthan Geography",
            "exam_id": "DOES_NOT_EXIST",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EXAM_PROFILE_NOT_FOUND"
    assert len(connection.calls) == 1
    assert "SELECT 1" in connection.calls[0][0]
    assert connection.closed


def test_exam_profile_endpoint_enforces_learner_scope_before_database_access():
    connection = _Connection()
    client = _client(connection, identity="different-learner")

    response = client.get("/api/v1/learners/learner-1/question-bank/exam-profiles")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "LEARNER_SCOPE_MISMATCH"
    assert connection.calls == []
    assert not connection.closed
