# Phase 6.35 — Test Session History and Results Integration

## API

- `GET /api/v1/learners/{learner_id}/preparation-sessions?limit=50&offset=0&status=SUBMITTED` lists learner-scoped session history.
- `GET /api/v1/learners/{learner_id}/preparation-results?limit=50&offset=0` lists persisted results for submitted and expired sessions.
- `GET /api/v1/learners/{learner_id}/preparation-results/summary` aggregates session count, completed tests, average/best percentage, total questions, attempted, correct, incorrect, and unattempted totals.
- Limits and offsets are bounded; rows are ordered newest first. Responses do not include answer keys/question snapshots.

## Learning-history integration

On submit and timeout, the existing TestAnalysisService derives outcomes from the persisted question snapshots. The existing LearningHistoryService records the overall attempt and topic snapshots; QuestionLearningHistoryService records per-question outcomes. These records feed the previously implemented learning progress and revision analysis instead of a separate, disconnected result store.

The overall attempt and question outcomes are written in one transaction. Stable learner/session/question IDs and a stable completion timestamp make synchronization retries idempotent. Finished session reads retry synchronization if a previous request failed after saving the result.

## Database

Migration `0017_phase6_35_test_result_history.sql` adds a partial index for terminal session history; it reuses the existing learning-history tables. Session/result APIs filter by authenticated learner ID. A 503 from learning-history synchronization means the session result was saved but the analytics write should be retried.

## Validation

PostgreSQL integration tests cover status-filtered session history, result history, aggregate score summary, persistence to overall/topic and per-question outcome tables, and no duplicated records on repeat reads.
