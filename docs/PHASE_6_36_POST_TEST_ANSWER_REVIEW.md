# Phase 6.36 — Post-Test Answer Review

## API

- `GET /api/v1/learners/{learner_id}/preparation-sessions/{session_id}/answer-review` returns the stable saved question order after a session is `SUBMITTED` or `EXPIRED`.
- Each review item includes the saved question and options, selected and correct option keys/text, outcome (`CORRECT`, `INCORRECT`, or `UNATTEMPTED`), explanation, concept/fact IDs, difficulty, answer-verification status/evidence, review flag, and elapsed answer time.
- The response also includes the original test result and reconciled per-question outcome counts.

## Safety and integrity

- The endpoint authenticates the learner and uses the existing learner-scoped session repository; other learners cannot review the session.
- Before submit/expiry, the endpoint returns `409 ANSWER_REVIEW_NOT_AVAILABLE` and does not return correct answers.
- Review is reconstructed from the persisted question snapshot and saved answers, not from a newly ranked pool. A missing snapshot question fails closed with a service-unavailable response.
- Existing API security headers include `Cache-Control: no-store`.

## Validation

PostgreSQL integration coverage checks pre-completion answer-key protection, submitted answer review and outcome reconciliation, saved explanations and verification status, and learner-scope isolation. The test requires the configured `AI_COMP_DATABASE_URL` integration database.
