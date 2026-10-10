from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app
from ai_comp.api.dependencies import PreparationContextUnavailable


class FakeAPIResponse:
    def to_payload(self):
        return {
            "schema_version": "1.0",
            "learner_id": "learner-1",
            "generated_at": "2026-10-10T00:00:00+00:00",
            "guidance": {"actions": []},
            "strategy_history": {"summary": {"audit_count": 0}},
            "strategy_feedback": {"findings": []},
        }


class FakePreparationGuidanceService:
    def __init__(self):
        self.calls = []

    def build_response(self, learner_id, **kwargs):
        self.calls.append((learner_id, kwargs))
        return FakeAPIResponse()


def valid_context():
    return {
        "test_id": "test-1",
        "title": "Rajasthan practice",
        "question_count": 10,
        "duration_seconds": 600,
        "history": object(),
        "question_history": object(),
        "candidates": (),
        "questions": (),
        "generated_at": datetime(2026, 10, 10, tzinfo=timezone.utc),
    }


class FakeContextProvider:
    def __init__(self, context=None, error=None):
        self.context = valid_context() if context is None else context
        self.error = error
        self.calls = []

    def load_context(self, learner_id, *, request):
        self.calls.append((learner_id, request.url.path))
        if self.error:
            raise self.error
        return self.context


def make_client(*, identity="learner-1", service=None, context_provider=None):
    def authenticate(_request):
        return identity

    app = create_app(
        preparation_guidance_api_service=service or FakePreparationGuidanceService(),
        learner_identity_provider=authenticate,
        preparation_context_provider=context_provider or FakeContextProvider(),
    )
    return TestClient(app)


def test_fastapi_route_mounts_phase_629_adapter_and_preserves_contract():
    service = FakePreparationGuidanceService()
    context_provider = FakeContextProvider()
    client = make_client(service=service, context_provider=context_provider)

    response = client.get(
        "/api/v1/learners/learner-1/preparation-guidance?history_limit=25"
    )

    assert response.status_code == 200
    assert response.json()["schema_version"] == "1.0"
    assert response.json()["learner_id"] == "learner-1"
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert context_provider.calls == [("learner-1", "/api/v1/learners/learner-1/preparation-guidance")]
    assert service.calls[0][0] == "learner-1"
    assert service.calls[0][1]["history_limit"] == 25


def test_default_app_fails_closed_without_authentication_provider():
    client = TestClient(create_app())

    response = client.get("/api/v1/learners/learner-1/preparation-guidance")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_route_enforces_learner_scope_before_loading_context():
    context_provider = FakeContextProvider()
    client = make_client(identity="learner-2", context_provider=context_provider)

    response = client.get("/api/v1/learners/learner-1/preparation-guidance")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "LEARNER_SCOPE_MISMATCH"
    assert context_provider.calls == []


def test_invalid_queries_are_rejected_before_context_is_loaded():
    context_provider = FakeContextProvider()
    client = make_client(context_provider=context_provider)

    zero = client.get("/api/v1/learners/learner-1/preparation-guidance?history_limit=0")
    unknown = client.get("/api/v1/learners/learner-1/preparation-guidance?other=value")
    duplicate = client.get(
        "/api/v1/learners/learner-1/preparation-guidance?history_limit=10&history_limit=20"
    )

    assert zero.status_code == 400
    assert zero.json()["error"]["code"] == "INVALID_HISTORY_LIMIT"
    assert unknown.status_code == 400
    assert duplicate.status_code == 400
    assert context_provider.calls == []


def test_missing_runtime_configuration_returns_503_after_authentication():
    app = create_app(learner_identity_provider=lambda _request: "learner-1")
    response = TestClient(app).get("/api/v1/learners/learner-1/preparation-guidance")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PREPARATION_GUIDANCE_NOT_CONFIGURED"


def test_unavailable_or_broken_context_provider_fails_without_leaking_details():
    unavailable = make_client(
        context_provider=FakeContextProvider(error=PreparationContextUnavailable("no context"))
    ).get("/api/v1/learners/learner-1/preparation-guidance")
    failed = make_client(
        context_provider=FakeContextProvider(error=RuntimeError("secret database detail"))
    ).get("/api/v1/learners/learner-1/preparation-guidance")

    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "PREPARATION_CONTEXT_UNAVAILABLE"
    assert failed.status_code == 500
    assert failed.json()["error"]["code"] == "PREPARATION_CONTEXT_LOAD_FAILED"
    assert "secret database detail" not in failed.text


def test_incomplete_server_context_is_not_reported_as_a_client_error():
    client = make_client(context_provider=FakeContextProvider(context={}))

    response = client.get("/api/v1/learners/learner-1/preparation-guidance")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PREPARATION_CONTEXT_UNAVAILABLE"


def test_non_get_route_method_is_rejected_with_security_headers():
    client = make_client()

    response = client.post("/api/v1/learners/learner-1/preparation-guidance")

    assert response.status_code == 405
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
