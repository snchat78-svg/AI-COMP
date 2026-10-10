from __future__ import annotations

from datetime import datetime, timezone

from ai_comp.application.preparation_guidance_http import PreparationGuidanceHTTPAdapter


class FakeAPIResponse:
    def to_payload(self):
        return {
            "schema_version": "1.0",
            "learner_id": "learner-1",
            "guidance": {"actions": []},
            "strategy_history": {"summary": {"audit_count": 0}},
            "strategy_feedback": {"findings": []},
        }


class FakePreparationService:
    def __init__(self, result=None, error=None):
        self.result = result or FakeAPIResponse()
        self.error = error
        self.calls = []

    def build_response(self, learner_id, **kwargs):
        self.calls.append((learner_id, kwargs))
        if self.error:
            raise self.error
        return self.result


def valid_context():
    return {
        "test_id": "test-1",
        "title": "Practice",
        "question_count": 10,
        "duration_seconds": 600,
        "history": object(),
        "question_history": object(),
        "candidates": (),
        "questions": (),
        "generated_at": datetime(2026, 10, 10, tzinfo=timezone.utc),
    }


def make_adapter(service=None):
    service = service or FakePreparationService()
    return PreparationGuidanceHTTPAdapter(service), service


def call(adapter, **kwargs):
    defaults = {
        "method": "GET",
        "target": "/api/v1/learners/learner-1/preparation-guidance",
        "authenticated_learner_id": "learner-1",
        "request_context": valid_context(),
    }
    defaults.update(kwargs)
    return adapter.handle(**defaults)


def test_http_adapter_returns_json_payload_and_security_headers():
    adapter, service = make_adapter()
    response = call(adapter, target="/api/v1/learners/learner-1/preparation-guidance?history_limit=25")

    assert response.status_code == 200
    assert response.json()["schema_version"] == "1.0"
    assert response.json()["learner_id"] == "learner-1"
    assert dict(response.headers)["Cache-Control"] == "no-store"
    assert dict(response.headers)["X-Content-Type-Options"] == "nosniff"
    assert service.calls[0][0] == "learner-1"
    assert service.calls[0][1]["history_limit"] == 25


def test_http_adapter_rejects_wrong_method_and_unknown_route():
    adapter, _ = make_adapter()
    assert call(adapter, method="POST").status_code == 405
    assert call(adapter, target="/api/v1/unknown").status_code == 404


def test_http_adapter_requires_authenticated_learner_and_enforces_scope():
    adapter, service = make_adapter()
    unauthenticated = call(adapter, authenticated_learner_id=None)
    mismatch = call(adapter, authenticated_learner_id="learner-2")

    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert mismatch.status_code == 403
    assert mismatch.json()["error"]["code"] == "LEARNER_SCOPE_MISMATCH"
    assert service.calls == []


def test_http_adapter_validates_learner_id_query_and_required_context():
    adapter, service = make_adapter()
    assert call(adapter, target="/api/v1/learners/%2Fother/preparation-guidance").status_code == 400
    assert call(adapter, target="/api/v1/learners/learner-1/preparation-guidance?history_limit=0").status_code == 400
    assert call(adapter, target="/api/v1/learners/learner-1/preparation-guidance?history_limit=abc").status_code == 400
    assert call(adapter, target="/api/v1/learners/learner-1/preparation-guidance?other=x").status_code == 400
    missing = call(adapter, request_context={})
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == "PREPARATION_CONTEXT_REQUIRED"
    assert service.calls == []


def test_http_adapter_hides_internal_exception_details():
    adapter, _ = make_adapter(FakePreparationService(error=RuntimeError("secret database detail")))
    response = call(adapter)

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "secret database detail" not in response.body.decode("utf-8")
