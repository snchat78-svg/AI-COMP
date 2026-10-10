# AI-COMP — Competitive Exam Intelligence

AI-COMP is a Python/FastAPI backend for competitive-exam paper research, verified question storage, persisted test sessions, results, and adaptive learner preparation.

## Current adaptive preparation work

- Phase 6.39 verifies the PostgreSQL feedback loop from a submitted test through analytics, an adaptive recommendation, a saved request, a new session, and the next result.
- Phase 6.40 publishes client-facing OpenAPI response contracts at `/openapi.json`.
- Phase 6.41 adds the initial Flutter client package under `apps/mobile/`: adaptive-preparation dashboard, timed question session, answer autosave/recovery, result review, and session resume.

## Backend tests

From the repository root:

```sh
python -m pip install -e ".[test,postgres,server]"
python -m pytest tests -q
```

PostgreSQL integration tests use `AI_COMP_DATABASE_URL`; GitHub Actions supplies a disposable PostgreSQL service.

## Flutter client

See [apps/mobile/README.md](apps/mobile/README.md) for requirements, local setup, authentication expectations, and device-run instructions. The mobile CI runs `flutter analyze` and `flutter test`. Android/iOS runner scaffolding and signed APK release are not yet part of the committed client foundation.

## Roadmap and evidence

- [Master roadmap coverage audit](docs/MASTER_ROADMAP_COVERAGE_AUDIT.md)
- [Phase 6.40 client/API contract](docs/PHASE_6_40_ADAPTIVE_PREPARATION_CLIENT_API_CONTRACT.md)
- [Phase 6.41 Flutter client foundation](docs/PHASE_6_41_FLUTTER_ADAPTIVE_PREPARATION_CLIENT.md)

A passing test suite proves the tested contracts; it does not imply full official-exam source coverage or production deployment.
