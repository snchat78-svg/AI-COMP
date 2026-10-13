from __future__ import annotations

from collections.abc import Mapping

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from ai_comp.api.app import create_app
from ai_comp.api.firebase_auth import FirebaseIdTokenLearnerIdentityProvider


def make_request(authorization: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode("latin-1")))
    return Request({"type": "http", "method": "GET", "path": "/", "headers": headers})


def test_provider_resolves_uid_from_verified_bearer_token() -> None:
    seen_tokens: list[str] = []

    def verify(token: str) -> Mapping[str, object]:
        seen_tokens.append(token)
        return {"uid": "firebase-learner-1", "email_verified": True}

    provider = FirebaseIdTokenLearnerIdentityProvider(verify)

    assert provider(make_request("Bearer signed-token")) == "firebase-learner-1"
    assert seen_tokens == ["signed-token"]


@pytest.mark.parametrize(
    "authorization",
    [None, "", "Basic abc", "Bearer", "Bearer one two", "Bearer   "],
)
def test_provider_rejects_missing_or_malformed_authorization(
    authorization: str | None,
) -> None:
    called = False

    def verify(_token: str):
        nonlocal called
        called = True
        return {"uid": "firebase-learner-1", "email_verified": True}

    provider = FirebaseIdTokenLearnerIdentityProvider(verify)
    assert provider(make_request(authorization)) is None
    assert called is False


def test_provider_rejects_unverified_email_by_default() -> None:
    provider = FirebaseIdTokenLearnerIdentityProvider(
        lambda _token: {"uid": "firebase-learner-1", "email_verified": False}
    )
    assert provider(make_request("Bearer token")) is None


@pytest.mark.parametrize(
    "claims",
    [
        None,
        {},
        {"email_verified": True},
        {"uid": "", "email_verified": True},
        {"uid": " firebase-learner-1", "email_verified": True},
        {"uid": "firebase-learner-1", "email_verified": "true"},
    ],
)
def test_provider_rejects_invalid_or_incomplete_claims(claims) -> None:
    provider = FirebaseIdTokenLearnerIdentityProvider(lambda _token: claims)
    assert provider(make_request("Bearer token")) is None


def test_unexpected_token_verifier_error_propagates() -> None:
    def unavailable(_token: str):
        raise RuntimeError("Firebase verification service unavailable")

    provider = FirebaseIdTokenLearnerIdentityProvider(unavailable)
    with pytest.raises(RuntimeError, match="verification service unavailable"):
        provider(make_request("Bearer token"))


def test_api_rejects_unverified_token_before_loading_learner_data() -> None:
    provider = FirebaseIdTokenLearnerIdentityProvider(
        lambda _token: {"uid": "firebase-learner-1", "email_verified": False}
    )
    client = TestClient(create_app(learner_identity_provider=provider))

    response = client.get(
        "/api/v1/learners/firebase-learner-1/preparation-results/analytics",
        headers={"Authorization": "Bearer any-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_api_binds_url_learner_id_to_verified_firebase_uid() -> None:
    provider = FirebaseIdTokenLearnerIdentityProvider(
        lambda _token: {"uid": "firebase-user-a", "email_verified": True}
    )
    client = TestClient(create_app(learner_identity_provider=provider))

    response = client.get(
        "/api/v1/learners/firebase-user-b/preparation-results/analytics",
        headers={"Authorization": "Bearer verified-token"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "LEARNER_SCOPE_MISMATCH"


def test_api_reports_verifier_outage_as_authentication_unavailable() -> None:
    def unavailable(_token: str):
        raise RuntimeError("verification service unavailable")

    provider = FirebaseIdTokenLearnerIdentityProvider(unavailable)
    client = TestClient(create_app(learner_identity_provider=provider))

    response = client.get(
        "/api/v1/learners/firebase-user-a/preparation-results/analytics",
        headers={"Authorization": "Bearer some-token"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTHENTICATION_UNAVAILABLE"
