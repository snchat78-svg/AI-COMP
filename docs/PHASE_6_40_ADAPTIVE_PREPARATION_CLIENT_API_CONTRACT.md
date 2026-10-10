# Phase 6.40 — Adaptive Preparation Client/API Contract

## Scope and repository boundary

The repository currently contains the FastAPI/Python backend and its tests; it does not contain a Flutter, Dart, web, or other client application. This phase publishes and tests the backend contract a client can consume, rather than inventing a placeholder UI. Existing endpoints and JSON payloads remain the source of behavior.

## OpenAPI response schemas

The FastAPI OpenAPI document describes request and response shapes for the adaptive preparation journey. Fetch `GET /openapi.json` from the running API or visit `/docs` in a configured development runtime.

Contract models live in `src/ai_comp/api/preparation_client_contract.py`. They are attached to route response metadata (not used to silently rewrite successful JSON response bodies), allowing generated mobile clients to understand the wire contract while endpoint tests check the actual payloads.

Important schemas include:

- `AdaptivePreparationRecommendationResponse`: saved request plus recommendation rationale, focus concepts, revision question IDs, and whether question count was capped.
- `PreparationTestRequestResponse`: durable request status/settings, including the saved mode.
- `PreparationTestSessionResponse`: safe session state, position, answered/review counts, remaining seconds, and optional result; no answer key.
- `CurrentQuestionResponse`: question stem and options; does not include the correct option.
- `SubmittedTestResponse`, `AnswerReviewResponse`, and `TestResultResponse`: submitted result and post-submit review.
- `CompletedTestAnalyticsResponse` and `PreparationResultsSummaryResponse`: result/analytics contracts for the dashboard.

Common API errors use `{ "error": { "code": "...", "message": "..." } }`. Clients should branch on stable `error.code` values and show the message as text, not parse it for control flow. Request-body validation errors generated automatically by FastAPI may use FastAPI's standard 422 validation envelope.

## Suggested client journey

1. `POST /api/v1/learners/{learner_id}/preparation-recommendations` with optional `question_count`, `duration_seconds`, scoring fields, and `max_concepts`.
2. On 201, retain `request_id`, display the focus concepts/count adjustment, then `POST /api/v1/learners/{learner_id}/preparation-sessions`.
3. Use the returned `session_id` for `POST .../{session_id}/start`, `GET .../{session_id}/current-question`, `POST .../{session_id}/answer`, and `POST .../{session_id}/next|previous|review`.
4. Submit with `POST .../{session_id}/submit`; show its result.
5. Only after submission or expiry, call `GET .../{session_id}/answer-review`.
6. Refresh `GET /api/v1/learners/{learner_id}/preparation-results/summary` and `GET .../preparation-results/analytics`. A later recommendation is derived from persisted results.

## Client state and recovery rules

- Treat `session_id` as the durable session handle; refetch server session state after reconnect rather than reconstructing progress locally.
- Use server-returned `remaining_seconds` as the timer authority; a device-side countdown is presentation only.
- Do not expect correct answers from the current-question endpoint. Answer keys and explanations are released only by answer-review after completion.
- A response mode describes the composed session. A saved adaptive request can remain `ADAPTIVE` while the composer reports an effective `MIXED` session when both prior-mistake revision and weak-topic focus are selected.
- Common statuses: `201` created, `200` success, `401` unauthenticated, `403` learner-scope mismatch, `404` missing learner-scoped resource, `409` invalid state/no recommendation signal/no eligible questions, `503` dependencies unavailable.
- Send credentials through the host application's configured authentication mechanism; do not treat a client-supplied learner ID as proof of identity.

## Validation

`tests/test_adaptive_preparation_client_contract.py` checks OpenAPI success response schemas for the main flow, validates a recommendation response against its documented model, verifies the common error envelope, and protects the rule that current-question responses exclude correct-answer fields. The PostgreSQL feedback-loop integration is separately covered by Phase 6.39.

No new database migration, question composer, or result store is introduced.
