from __future__ import annotations

import logging

from fastapi import FastAPI, Request

from ai_comp.api.preparation_guidance_routes import _authenticated_learner_or_error


def test_authentication_unavailable_logs_only_exception_class(caplog) -> None:
    app = FastAPI()

    def broken_identity_provider(_request: Request) -> str | None:
        raise RuntimeError("sensitive-token-fragment must not be logged")

    app.state.learner_identity_provider = broken_identity_provider
    request = Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "https",
            "path": "/api/v1/learners/test-uid/preparation-results/analytics",
            "raw_path": b"/api/v1/learners/test-uid/preparation-results/analytics",
            "query_string": b"",
            "headers": [(b"authorization", b"Bearer test-only-token")],
            "client": ("testclient", 12345),
            "server": ("testserver", 443),
            "app": app,
        }
    )

    with caplog.at_level(logging.WARNING, logger="ai_comp.api.preparation_guidance_routes"):
        learner_id, response = _authenticated_learner_or_error("test-uid", request)

    assert learner_id is None
    assert response is not None
    assert response.status_code == 503
    assert b"AUTHENTICATION_UNAVAILABLE" in response.body
    assert "exception_type=RuntimeError" in caplog.text
    assert "sensitive-token-fragment" not in caplog.text
    assert "test-only-token" not in caplog.text
