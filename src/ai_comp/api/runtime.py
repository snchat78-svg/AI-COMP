from __future__ import annotations

import os

from fastapi import FastAPI

from ai_comp.api.app import create_postgres_app
from ai_comp.api.firebase_auth import FirebaseIdTokenLearnerIdentityProvider


def create_runtime_app() -> FastAPI:
    """Build the configured production API from runtime environment variables.

    Run with:
      uvicorn ai_comp.api.runtime:create_runtime_app --factory

    The existing create_app() factory remains unchanged and fail-closed for tests
    and unconfigured hosts. This factory is the explicit production composition.
    Cloud Run should provide application default credentials to Firebase Admin SDK;
    no service-account private key belongs in source control or the APK.
    """
    dsn = os.environ.get("AI_COMP_DATABASE_URL", "").strip()
    project_id = os.environ.get("FIREBASE_PROJECT_ID", "").strip()
    if not dsn:
        raise RuntimeError("AI_COMP_DATABASE_URL must be configured for the production API.")
    if not project_id:
        raise RuntimeError("FIREBASE_PROJECT_ID must be configured for the production API.")

    # Import the Admin SDK only when this configured runtime is started.
    try:
        from firebase_admin import auth, get_app, initialize_app
    except ImportError as exc:  # pragma: no cover - exercised in the deployment environment.
        raise RuntimeError(
            "Install the server extras, including firebase-admin, to run the configured API."
        ) from exc

    try:
        firebase_app = get_app()
    except ValueError:
        # Application Default Credentials are supplied by the hosting environment.
        firebase_app = initialize_app(
            options={"projectId": project_id, "httpTimeout": 10}
        )

    actual_project_id = firebase_app.project_id
    if not actual_project_id:
        raise RuntimeError("The Firebase Admin app has no resolved project ID.")
    if actual_project_id != project_id:
        raise RuntimeError(
            "FIREBASE_PROJECT_ID does not match the initialized Firebase Admin app."
        )

    def verify_token(token: str):
        try:
            # Firebase Admin validates signature, issuer, audience, and expiry.
            # Revocation lookups are disabled here; normal ID-token expiry still applies.
            return auth.verify_id_token(token, app=firebase_app, check_revoked=False)
        except (auth.InvalidIdTokenError, ValueError):
            # Malformed, expired, or otherwise invalid client tokens are unauthenticated.
            return None

    identity_provider = FirebaseIdTokenLearnerIdentityProvider(verify_token)
    return create_postgres_app(
        dsn=dsn,
        learner_identity_provider=identity_provider,
    )


__all__ = ["create_runtime_app"]
