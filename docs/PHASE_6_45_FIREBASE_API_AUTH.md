# Phase 6.45 — Firebase API Authentication and Runtime

## Goal

Connect the existing Flutter Firebase sign-in to the existing PostgreSQL-backed FastAPI service without replacing the existing question-selection, test-session, scoring, answer-review, analytics, or adaptive-learning contracts.

## Change boundary

- `FirebaseIdTokenLearnerIdentityProvider` is a new adapter implementing the existing `LearnerIdentityProvider` protocol.
- The adapter reads only a Bearer ID token, uses verified Firebase claims, requires `email_verified == true`, and returns the verified Firebase UID.
- Existing routes continue to compare that UID with the learner ID in the URL. A mismatch remains a 403 and a missing/invalid identity remains unauthenticated.
- `create_app()` stays fail-closed and unchanged. The new `create_runtime_app()` is an explicit configured production composition of the existing PostgreSQL app and Firebase Admin SDK.
- Database migrations are explicit and are not executed on every API startup.

## Runtime configuration

Configure these values in the backend hosting environment, never in the Flutter APK or source files:

- `FIREBASE_PROJECT_ID`: the exact Firebase project ID from `project_info.project_id` in the matching `google-services.json`. This is the project ID, not the display name.
- `AI_COMP_DATABASE_URL`: PostgreSQL DSN. Store credential-bearing DSNs in the hosting platform's secret manager and inject the secret as an environment variable.
- `PORT`: supplied by Cloud Run; the container uses it automatically.

The Firebase Admin SDK uses Application Default Credentials from the hosting environment. Do not commit service-account JSON or paste private keys into GitHub, the app, or chat.

## Database preparation

1. Provision PostgreSQL with the `vector` extension available. The first repository migration creates it and requires a database role allowed to create extensions.
2. Configure the runtime identity to reach that database.
3. Run migrations once, as a controlled deployment step, using the same built container and the environment variable `AI_COMP_DATABASE_URL`:

   `python -m ai_comp.database.migrate_cli`

4. Check the migration command's exit code and logs before starting the API. Re-running it is safe for already applied matching checksums; modified applied migrations are rejected.

Do not call the migration CLI from API startup; multiple replicas must not race schema changes.

## Container runtime

The root `Dockerfile` installs the existing project with the `postgres` and `server` extras. The configured application is started with:

`uvicorn ai_comp.api.runtime:create_runtime_app --factory --host 0.0.0.0 --port ${PORT:-8080}`

The runtime fails startup if `AI_COMP_DATABASE_URL` or `FIREBASE_PROJECT_ID` is missing. It also rejects a Firebase Admin app initialized for a different project.

## API security behavior

- Firebase Admin validates ID-token signature, issuer, audience/project and expiry.
- Invalid/expired tokens produce no learner identity. Email-unverified tokens also produce no learner identity.
- Temporary certificate/verification infrastructure errors remain distinguishable from ordinary invalid credentials and fail closed.
- URL learner identity must exactly match the verified Firebase UID; request body or a typed learner ID cannot grant identity.
- Revocation checks are not enabled on every request in this first increment; ID tokens remain subject to Firebase's normal expiry. A later operational decision may enable revocation checks and provide the needed Firebase Auth permissions.

## Deployment acceptance criteria

- [ ] Backend service has a real PostgreSQL DSN from Secret Manager.
- [ ] Backend runtime has the correct `FIREBASE_PROJECT_ID` and Application Default Credentials.
- [ ] All SQL migrations complete successfully before service traffic is enabled.
- [ ] `GET /openapi.json` returns the API schema from the deployed HTTPS service.
- [ ] Missing, malformed, expired, and unverified tokens are rejected.
- [ ] A verified token can only access the route whose learner ID matches its UID.
- [ ] Existing Python/PostgreSQL integration tests and Flutter tests remain green.
- [ ] The actual HTTPS service URL is then entered as the mobile app's API base URL.

Until those deployment checks complete, there is intentionally no API URL to enter in the mobile app. Firebase Console alone does not host this FastAPI/PostgreSQL service.
