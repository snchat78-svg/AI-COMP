# Phase 6.31 — PostgreSQL-backed Preparation Context

## Goal

Connect the Phase 6.30 FastAPI route to the existing PostgreSQL learning-history repositories, accepted generated-question store, and canonical question-intelligence ranker.

## Runtime composition

\`create_postgres_app(...)\` composes:

1. A required host-owned learner identity provider.
2. A required host-owned \`PreparationTestRequestProvider\` that resolves the current \`TestSpecification\` and optional concept scope from trusted application/session state.
3. PostgreSQL learning history through \`LearningHistoryService\` + \`PostgresLearningHistoryRepository\`.
4. Question-level history through \`QuestionLearningHistoryService\` + \`PostgresQuestionLearningHistoryRepository\`.
5. Candidate questions through \`PostgresGeneratedQuestionRepository.list_accepted()\`, which returns only accepted, answer-verified, non-duplicate generated questions.
6. Ranking through the canonical \`QuestionIntelligenceService\`; no second ranking implementation is introduced.
7. Strategy audit history through short-lived PostgreSQL connections and the existing \`AdaptiveStudyStrategyHistoryService\`.

Each context load uses a short-lived connection and closes it even on failure. The strategy-history repository also opens and closes a connection per operation, so the application does not retain a connection after request completion.

## Ranking evidence and history rules

The ranker uses the persisted generated-question importance score and concept overlap against the trusted test request. When a concept scope is supplied, PostgreSQL filters to questions intersecting that scope before the pool limit is applied; unrelated questions are never used just to fill the requested count. Historical verified appearances and fact/concept confidence are not fabricated when the generated-question record does not contain that evidence. Accepted questions with unsupported difficulty metadata are excluded from the candidate pool. The existing domain rule that accepted questions must have verified answers and cannot be known duplicates remains in force.

## Context request boundary

The endpoint still accepts only \`history_limit\`. Test ID, title, question count, duration, mode, concept scope and exclusions must come from a trusted \`PreparationTestRequestProvider\` rather than arbitrary query parameters. The provider must bind its result to the authenticated learner. If the request is missing, belongs to another learner, or the verified question pool is too small, the route fails closed instead of inventing test settings/questions.

This phase intentionally does not invent an authentication mechanism or a persisted draft-test UI/API. The host still supplies those two boundaries.

## Run

Install dependencies:

    python -m pip install -e ".[server,postgres]"

A configured host can construct the app with \`create_postgres_app(dsn=..., learner_identity_provider=..., preparation_test_request_provider=...)\`. A bare \`ai_comp.api.app:app\` remains fail-closed because it has no credentials, DSN or current test request configured.

## Validation

PostgreSQL integration tests apply existing migrations, persist an accepted verified generated question, request preparation guidance through FastAPI, verify the selected question comes from PostgreSQL, and check that an undersized candidate pool returns an unavailable response.
