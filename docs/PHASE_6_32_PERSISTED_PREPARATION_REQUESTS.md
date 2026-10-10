# Phase 6.32 — Persisted Preparation Request Lifecycle

## Goal

Persist the learner's selected preparation settings and have the Phase 6.31 context provider load the current active request from PostgreSQL.

## Endpoints

- \`POST /api/v1/learners/{learner_id}/preparation-requests\` validates and stores test settings.
- \`GET /api/v1/learners/{learner_id}/preparation-requests/active\` reads the learner's active saved settings.
- \`GET /api/v1/learners/{learner_id}/preparation-guidance?history_limit=50\` uses the active saved settings when \`create_postgres_app()\` is composed without a custom request provider.

The POST body includes title, question count, duration, scoring, preparation mode, concept IDs, exclusions, shuffle settings, and optional exam/subject identifiers. Request IDs and test IDs are generated server-side; clients cannot select another learner's request.

## Persistence and lifecycle

Migration \`0015_phase6_32_preparation_test_requests.sql\` adds \`preparation_test_requests\`, a partial unique index ensuring at most one ACTIVE request per learner, status history (\`ACTIVE\`, \`SUPERSEDED\`, \`CANCELLED\`), scoring settings, concept scope, exclusions, and timestamps. Creating a replacement request atomically supersedes the previous active row; older request metadata remains for history.

A table lock serializes active-request replacement transactions. This is straightforward for the current low-volume API; if request writes become high-throughput, a per-learner locking strategy can replace the global lock with a separately tested migration.

## Context integration

The PostgreSQL-backed app uses a connection-scoped repository proxy. The default request provider reads the learner's active request from PostgreSQL. Missing active settings do not create a fake test; guidance returns an unavailable response instead.

Question selection still reads only accepted, answer-verified, non-duplicate generated questions. The question pool is filtered by concept IDs when supplied and ranked using the canonical \`QuestionIntelligenceService\`.

## Scope limitation: exam/subject metadata

Optional \`exam_id\` and \`subject_id\` are persisted as selection metadata and returned by the active-request endpoint. In the current schema, generated questions do not carry a reliable direct exam/subject ownership relationship, so these fields do **not** claim to filter questions by exam. Actual exam-specific selection should be added after a source-backed question-to-exam/syllabus mapping exists. \`concept_ids\` are the operative question-pool filter in this phase.

## Security

The POST and active-read routes reuse Phase 6.30's trusted learner identity provider and reject URL/authenticated learner mismatches before persistence. Database errors are mapped to generic server responses; SQL details are not returned. The unconfigured default app remains fail-closed.

## Validation

PostgreSQL integration tests cover durable POST/GET lifecycle, replacement/superseding, saved scoring/duration flowing into preparation guidance, learner scope enforcement, payload validation, and the no-active-request response.
