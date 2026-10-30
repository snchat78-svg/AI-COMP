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


def test_ai_candidate_response_exposes_separate_batch_audit_counts(monkeypatch):
    from ai_comp.application.one_liner_candidate_generation import OneLinerDraft
    from ai_comp.database import postgres_topic_question_bank
    from ai_comp.material import gemini_one_liner_generation

    monkeypatch.setenv("AI_COMP_CONTENT_ADMIN_TOKEN", "author-secret")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    source_text = _payload()["source_text"]
    evidence = "The Luni River is the largest river system in the Thar Desert region."

    class FakeProvider:
        def __init__(self, **kwargs):
            pass

        def generate(self, **kwargs):
            return (
                OneLinerDraft(
                    question_text="Which river system is the largest in the Thar Desert region?",
                    answer_text="The Luni River system.",
                    evidence_quote=source_text,
                    answer_evidence_quote=evidence,
                    importance_score=0.95,
                ),
            )

    class FakeRepository:
        def __init__(self, connection):
            pass

        def list_one_liners(self, *args, **kwargs):
            return ()

        def save_one_liner(self, item):
            return item

    class FakeConnection:
        def execute(self, query, params):
            return type("Result", (), {"fetchone": lambda self: (params[0], "Luni River")})()

        def close(self):
            pass

    monkeypatch.setattr(
        gemini_one_liner_generation,
        "GeminiOneLinerGenerationProvider",
        FakeProvider,
    )
    monkeypatch.setattr(
        postgres_topic_question_bank,
        "PostgresTopicQuestionBankRepository",
        FakeRepository,
    )
    app = create_app()
    app.state.question_bank_connection_factory = FakeConnection
    client = TestClient(app)

    response = client.post(
        "/api/v1/admin/question-bank/one-liners/generate-candidates",
        headers={"X-AI-COMP-Content-Admin-Token": "author-secret"},
        json=_payload(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["generated_count"] == 1
    assert payload["saved_count"] == 1
    assert payload["duplicate_count"] == 0
    assert payload["rejected_count"] == 0
    assert payload["pending_review_count"] == 1
    assert payload["verified_count"] == 0
    assert payload["batch_audit"] == {
        "generated_count": 1,
        "rejected_count": 0,
        "duplicate_count": 0,
        "pending_review_count": 1,
        "verified_count": 0,
    }
    assert payload["items"][0]["verification_status"] == "NEEDS_REVIEW"
