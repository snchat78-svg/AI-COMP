from __future__ import annotations

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


def _payload(**overrides):
    return {
        "concept_id": "catalog.rajasthan_geography_rivers_and_drainage_luni_river",
        "source_url": "https://environment.rajasthan.gov.in/river-reference",
        "source_locator": "Official geography reference, Rivers section",
        "source_text": (
            "The Luni River is the largest river system in the Thar Desert region. "
            "It flows southwest and drains into the Rann of Kutch."
        ),
        "language_code": "hi",
        "requested_count": 10,
        **overrides,
    }


def test_ai_candidate_endpoint_fails_closed_without_content_admin_secret(monkeypatch):
    monkeypatch.delenv("AI_COMP_CONTENT_ADMIN_TOKEN", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/generate-candidates",
        json=_payload(),
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUESTION_BANK_CONTENT_AUTHORING_NOT_CONFIGURED"


def test_ai_candidate_endpoint_rejects_wrong_content_admin_secret(monkeypatch):
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "expected-secret")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/generate-candidates",
        headers={"X-AI-COMP-Content-Admin-Token": "wrong-secret"},
        json=_payload(),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "CONTENT_ADMIN_AUTHENTICATION_REQUIRED"


def test_ai_candidate_endpoint_fails_closed_without_gemini_key(monkeypatch):
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "expected-secret")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/generate-candidates",
        headers={"X-AI-COMP-Content-Admin-Token": "expected-secret"},
        json=_payload(),
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ONE_LINER_GENERATION_NOT_CONFIGURED"


def test_ai_candidate_endpoint_rejects_non_https_source_before_processing(monkeypatch):
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "expected-secret")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/generate-candidates",
        headers={"X-AI-COMP-Content-Admin-Token": "expected-secret"},
        json=_payload(source_url="http://example.gov.in/facts"),
    )

    assert response.status_code == 422


def test_ai_candidate_endpoint_rejects_empty_or_oversized_request(monkeypatch):
    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "expected-secret")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = TestClient(create_app())

    empty = client.post(
        "/api/v1/admin/question-bank/one-liners/generate-candidates",
        headers={"X-AI-COMP-Content-Admin-Token": "expected-secret"},
        json=_payload(source_text=""),
    )
    too_many = client.post(
        "/api/v1/admin/question-bank/one-liners/generate-candidates",
        headers={"X-AI-COMP-Content-Admin-Token": "expected-secret"},
        json=_payload(requested_count=51),
    )

    assert empty.status_code == 422
    assert too_many.status_code == 422
