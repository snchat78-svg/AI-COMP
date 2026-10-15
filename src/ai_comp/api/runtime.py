from __future__ import annotations

import os

from fastapi import FastAPI

from ai_comp.api.app import create_postgres_app
from ai_comp.api.firebase_auth import FirebaseIdTokenLearnerIdentityProvider


def _initialize_firebase_app(project_id: str):
    """Initialize Firebase Admin using the explicitly configured service key.

    Render Secret Files are mounted at a known path. Loading that file directly
    avoids relying on google.auth.default() to discover credentials later during
    token verification, where such discovery errors otherwise become opaque 503s.
    If no file path is configured, environments such as Cloud Run may still use
    Application Default Credentials.
    """
    from firebase_admin import credentials, get_app, initialize_app

    credential_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    firebase_credential = None
    if credential_path:
        if not os.path.isfile(credential_path) or not os.access(credential_path, os.R_OK):
            raise RuntimeError(
                "The configured Firebase service-account file is missing or unreadable."
            )
        try:
            firebase_credential = credentials.Certificate(credential_path)
        except Exception:
            # Never surface JSON/private-key parser details in startup logs.
            raise RuntimeError("The configured Firebase service-account file is invalid.") from None

    try:
        firebase_app = get_app()
    except ValueError:
        options = {"projectId": project_id, "httpTimeout": 10}
        if firebase_credential is not None:
            firebase_app = initialize_app(credential=firebase_credential, options=options)
        else:
            firebase_app = initialize_app(options=options)

    return firebase_app


def create_runtime_app() -> FastAPI:
    """Build the configured production API from runtime environment variables.

    Run with:
      uvicorn ai_comp.api.runtime:create_runtime_app --factory

    The existing create_app() factory remains unchanged and fail-closed for tests
    and unconfigured hosts. This factory is the explicit production composition.
    No service-account private key belongs in source control or the APK.
    """
    # The Firebase Admin SDK treats this environment variable as permission to
    # accept emulator-issued (including unsigned) ID tokens. This factory is a
    # production boundary, so reject emulator mode before initializing Firebase
    # or creating the database-backed app.
    if "FIREBASE_AUTH_EMULATOR_HOST" in os.environ:
        raise RuntimeError(
            "FIREBASE_AUTH_EMULATOR_HOST must not be set for the production API runtime."
        )

    dsn = os.environ.get("AI_COMP_DATABASE_URL", "").strip()
    project_id = os.environ.get("FIREBASE_PROJECT_ID", "").strip()
    if not dsn:
        raise RuntimeError("AI_COMP_DATABASE_URL must be configured for the production API.")
    if not project_id:
        raise RuntimeError("FIREBASE_PROJECT_ID must be configured for the production API.")

    # Import the Admin SDK only when this configured runtime is started.
    try:
        from firebase_admin import auth
    except ImportError as exc:  # pragma: no cover - exercised in the deployment environment.
        raise RuntimeError(
            "Install the server extras, including firebase-admin, to run the configured API."
        ) from exc

    firebase_app = _initialize_firebase_app(project_id)

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
