from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


def _payload(**overrides):
    return {
        "concept_id": "rajasthan-geography-rivers",
        "question_text": "राजस्थान की प्रमुख पश्चिमवाहिनी नदी कौनसी है?",
        "answer_text": "लूणी नदी",
        "language_code": "hi",
        "source_url": "https://example.gov.in/rajasthan-rivers",
        "source_evidence": "Official source, heading: Rivers of Rajasthan.",
        "verification_status": "NEEDS_REVIEW",
        "importance_score": 0.9,
        **overrides,
    }


class _Cursor:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _ReviewConnection:
    def __init__(
        self,
        *,
        status="NEEDS_REVIEW",
        source_url="https://example.gov.in/rajasthan-rivers",
        source_evidence="Official source, heading: Rivers of Rajasthan.",
        exists=True,
    ):
        now = datetime.now(timezone.utc)
        self.status = status
        self.source_url = source_url
        self.source_evidence = source_evidence
        self.exists = exists
        self.reviewed_at = None
        self.reviewed_by = None
        self.review_note = ""
        self.created_at = now
        self.updated_at = now
        self.calls = []
        self.review_entries = []
        self.closed = False

    def transaction(self):
        return nullcontext(self)

    def _row(self):
        return (
            "one-liner-1",
            "catalog.rajasthan_geography_rivers_and_drainage_luni_river",
            "राजस्थान की प्रमुख पश्चिमवाहिनी नदी कौनसी है?",
            "लूणी नदी",
            "hi",
            self.source_url,
            self.source_evidence,
            self.status,
            0.9,
            self.reviewed_at,
            self.created_at,
            self.updated_at,
        )

    def execute(self, query, params):
        self.calls.append((query, params))
        if "SELECT one_liner_id" in query and "FOR UPDATE" in query:
            return _Cursor(self._row() if self.exists else None)
        if "UPDATE question_bank_one_liners" in query:
            self.status = params[0]
            self.reviewed_at = (
                None if self.status == "NEEDS_REVIEW" else datetime.now(timezone.utc)
            )
            self.reviewed_by = None if self.status == "NEEDS_REVIEW" else params[3]
            self.review_note = params[4]
            self.updated_at = datetime.now(timezone.utc)
            return _Cursor(self._row())
        if "INSERT INTO question_bank_one_liner_reviews" in query:
            self.review_entries.append(params)
            now = datetime.now(timezone.utc)
            return _Cursor((now, now))
        raise AssertionError(f"Unexpected SQL in test double: {query[:80]}")

    def close(self):
        self.closed = True


def test_direct_one_liner_authoring_fails_closed_without_server_secret(monkeypatch) -> None:
    monkeypatch.delenv("AI_COMP_CONTENT_ADMIN_TOKEN", raising=False)
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/admin/question-bank/one-liners",
        json=_payload(),
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUESTION_BANK_CONTENT_AUTHORING_NOT_CONFIGURED"


def test_direct_one_liner_authoring_rejects_wrong_admin_secret(monkeypatch) -> None:
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "configured-test-token")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/admin/question-bank/one-liners",
        headers={"X-AI-COMP-Content-Admin-Token": "wrong-token"},
        json=_payload(),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "CONTENT_ADMIN_AUTHENTICATION_REQUIRED"


def test_authoring_cannot_self_verify_even_with_source_evidence() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/admin/question-bank/one-liners",
        json=_payload(
            verification_status="VERIFIED",
            source_url="https://example.gov.in/rajasthan-rivers",
            source_evidence="Specific fact and official source section identified.",
        ),
    )

    assert response.status_code == 422


def test_reviewer_fails_closed_without_separate_server_secret(monkeypatch) -> None:
    monkeypatch.delenv("AI_COMP_CONTENT_REVIEW_TOKEN", raising=False)
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/one-liner-1/review",
        json={"decision": "VERIFIED", "review_note": "Compared with source."},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUESTION_BANK_CONTENT_REVIEW_NOT_CONFIGURED"


def test_review_endpoint_rejects_wrong_review_token(monkeypatch) -> None:
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEW_TOKEN", "configured-review-token")
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "configured-author-token")
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEWER_ID", "reviewer-test")
    connection = _ReviewConnection()
    app = create_app()
    app.state.question_bank_connection_factory = lambda: connection
    client = TestClient(app)

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/one-liner-1/review",
        headers={"X-AI-COMP-Content-Review-Token": "wrong-token"},
        json={"decision": "VERIFIED", "review_note": "Compared with source."},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "CONTENT_REVIEW_AUTHENTICATION_REQUIRED"
    assert connection.calls == []


def test_review_fails_closed_when_author_and_reviewer_secrets_are_identical(monkeypatch) -> None:
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "same-secret")
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEW_TOKEN", "same-secret")
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEWER_ID", "reviewer-test")
    connection = _ReviewConnection()
    app = create_app()
    app.state.question_bank_connection_factory = lambda: connection
    client = TestClient(app)

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/one-liner-1/review",
        headers={"X-AI-COMP-Content-Review-Token": "same-secret"},
        json={"decision": "VERIFIED", "review_note": "Checked source."},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUESTION_BANK_CONTENT_REVIEW_NOT_CONFIGURED"
    assert connection.calls == []


def test_authoring_rejects_https_url_without_hostname() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/admin/question-bank/one-liners",
        json=_payload(source_url="https://"),
    )
    assert response.status_code == 422


def test_independent_reviewer_verifies_pending_item_and_writes_audit(monkeypatch) -> None:
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEW_TOKEN", "configured-review-token")
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "configured-author-token")
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEWER_ID", "reviewer-test")
    connection = _ReviewConnection()
    app = create_app()
    app.state.question_bank_connection_factory = lambda: connection
    client = TestClient(app)

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/one-liner-1/review",
        headers={"X-AI-COMP-Content-Review-Token": "configured-review-token"},
        json={
            "decision": "VERIFIED",
            "review_note": "Checked the cited official source and confirmed the answer.",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["item"]["verification_status"] == "VERIFIED"
    assert payload["review"]["reviewer_id"] == "reviewer-test"
    assert payload["review"]["decision"] == "VERIFIED"
    assert payload["review"]["source_checked_at"]
    assert connection.status == "VERIFIED"
    assert len(connection.review_entries) == 1
    assert "FOR UPDATE" in connection.calls[0][0]
    assert "UPDATE question_bank_one_liners" in connection.calls[1][0]
    assert "INSERT INTO question_bank_one_liner_reviews" in connection.calls[2][0]
    assert connection.closed


def test_reviewer_cannot_verify_without_source_evidence(monkeypatch) -> None:
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEW_TOKEN", "configured-review-token")
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "configured-author-token")
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEWER_ID", "reviewer-test")
    connection = _ReviewConnection(source_url=None, source_evidence="")
    app = create_app()
    app.state.question_bank_connection_factory = lambda: connection
    client = TestClient(app)

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/one-liner-1/review",
        headers={"X-AI-COMP-Content-Review-Token": "configured-review-token"},
        json={"decision": "VERIFIED", "review_note": "Tried to approve without source."},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ONE_LINER_SOURCE_EVIDENCE_REQUIRED"
    assert connection.status == "NEEDS_REVIEW"
    assert len(connection.review_entries) == 0
    assert connection.closed


def test_review_cannot_overwrite_already_verified_item(monkeypatch) -> None:
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEW_TOKEN", "configured-review-token")
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "configured-author-token")
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEWER_ID", "reviewer-test")
    connection = _ReviewConnection(status="VERIFIED")
    app = create_app()
    app.state.question_bank_connection_factory = lambda: connection
    client = TestClient(app)

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/one-liner-1/review",
        headers={"X-AI-COMP-Content-Review-Token": "configured-review-token"},
        json={"decision": "REJECTED", "review_note": "Needs a content correction."},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ONE_LINER_ALREADY_VERIFIED"
    assert len(connection.review_entries) == 0


def test_review_returns_not_found_for_unknown_item(monkeypatch) -> None:
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEW_TOKEN", "configured-review-token")
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "configured-author-token")
    monkeypatch.setenv("AI_COMP_CONTENT_REVIEWER_ID", "reviewer-test")
    connection = _ReviewConnection(exists=False)
    app = create_app()
    app.state.question_bank_connection_factory = lambda: connection
    client = TestClient(app)

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/missing-item/review",
        headers={"X-AI-COMP-Content-Review-Token": "configured-review-token"},
        json={"decision": "NEEDS_REVIEW", "review_note": "Item was not found in source set."},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ONE_LINER_NOT_FOUND"
    assert connection.closed
