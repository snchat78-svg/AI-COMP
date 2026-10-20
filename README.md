# AI-COMP — Competitive Exam Intelligence

AI-COMP is a Python/FastAPI backend for competitive-exam paper research, verified question storage, persisted test sessions, results, and adaptive learner preparation.

## Current adaptive preparation work

- Phase 6.39 verifies the PostgreSQL feedback loop from a submitted test through analytics, an adaptive recommendation, a saved request, a new session, and the next result.
- Phase 6.40 publishes client-facing OpenAPI response contracts at `/openapi.json`.
- Phase 6.41 adds the initial Flutter client package under `apps/mobile/`: adaptive-preparation dashboard, timed question session, answer autosave/recovery, result review, and session resume.
- Phase 6.42 adds Android runner configuration and CI build verification; successful Flutter Actions runs publish a test APK artifact.
- Phase 6.44 adds Firebase email/password registration, confirmation, email verification gating, password-reset email, and English auth/dashboard copy.
- Phase 6.45 adds fail-closed Firebase ID-token verification, the configured PostgreSQL/Firebase API runtime, explicit migrations, and a Cloud Run-ready container.
- Phase 6.46 adds a Render Free Blueprint and a manually triggered GitHub Actions database-migration workflow. It prepares a free-tier deployment path but does not create cloud resources or claim the API is deployed.

## Backend tests

From the repository root:

```sh
python -m pip install -e ".[test,postgres,server]"
python -m pytest tests -q
```

PostgreSQL integration tests use `AI_COMP_DATABASE_URL`; GitHub Actions supplies a disposable PostgreSQL service.

## Flutter / Android client

See [apps/mobile/README.md](apps/mobile/README.md) for requirements, local setup, authentication expectations, device-run instructions, and APK artifact retrieval. Mobile CI runs `flutter analyze`, `flutter test`, and `flutter build apk --release`. The generated APK is for testing and uses a debug signing key; production signing and iOS scaffolding are not claimed as complete.

## Hosting readiness

Read [Phase 6.46 — Free-Tier Cloud Hosting Readiness](docs/PHASE_6_46_FREE_HOSTING_READINESS.md) before creating resources. Never commit database credentials or Firebase service-account JSON. Render Free services may sleep and Supabase Free projects may pause; check the current provider limits before public launch. API URL configuration in the APK must wait for a real HTTPS service.

## Roadmap and evidence

- [Master roadmap coverage audit](docs/MASTER_ROADMAP_COVERAGE_AUDIT.md)
- [Phase 2.5 source health and secondary-source policy](docs/PHASE_2_5_SOURCE_HEALTH_AND_SECONDARY_SOURCE_POLICY.md)
- [Phase 2.6 Mumbai regional source probe](docs/PHASE_2_6_MUMBAI_REGIONAL_SOURCE_PROBE.md)
- [Phase 6.40 client/API contract](docs/PHASE_6_40_ADAPTIVE_PREPARATION_CLIENT_API_CONTRACT.md)
- [Phase 6.41 Flutter client foundation](docs/PHASE_6_41_FLUTTER_ADAPTIVE_PREPARATION_CLIENT.md)
- [Phase 6.42 Android platform and APK build](docs/PHASE_6_42_ANDROID_PLATFORM_AND_APK_BUILD.md)
- [Phase 6.45 Firebase API authentication and runtime](docs/PHASE_6_45_FIREBASE_API_AUTH.md)
- [Phase 6.46 free-tier hosting readiness](docs/PHASE_6_46_FREE_HOSTING_READINESS.md)

A passing test suite proves the tested contracts; it does not imply full official-exam source coverage or production deployment.
