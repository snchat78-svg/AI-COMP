from __future__ import annotations

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


def test_verified_one_liner_must_have_source_evidence() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/admin/question-bank/one-liners",
        json=_payload(
            verification_status="VERIFIED",
            source_url=None,
            source_evidence="",
        ),
    )

    assert response.status_code == 422
