# Phase 6.16 — Completed Test Feedback Integration

## Purpose

Phase 6.16 connects the existing timed test engine to immediate analytics and both existing learner-history services. It closes the feedback loop without adding a parallel state store or changing the current database schema.

## End-to-end flow

TestEngine session
then persisted TestResult
then TestAnalysisService
then immediate score, per-question outcomes and weak topics
then LearningHistoryService
then QuestionLearningHistoryService
then a single CompletedTestFeedback response containing the updated learner histories

## Contracts

- Only SUBMITTED and EXPIRED sessions with a stored result can be processed. CREATED, IN_PROGRESS and CANCELLED sessions fail closed.
- The stored result must match the session ID, test ID and final status.
- The supplied question set must exactly match the session question IDs, have no duplicates, and contain only ACCEPTED questions.
- The existing TestAnalysisService remains the source for per-question and weak-topic analysis.
- Both existing history services remain the source of durable writes and aggregation. Attempt identity is learner plus session; question outcome identity is learner plus session plus question.
- The long-term attempt is written first. Its persisted completion timestamp anchors retries if question-level history temporarily fails; retrying with the same learner/session pair reuses that timestamp and avoids conflicting duplicate rows.
- Persistence remains owned by each repository. This service does not claim a cross-repository transaction. A persistence failure is surfaced to the caller; retry the same learner/session pair to finish any missing idempotent write.
- Callers must authenticate and authorize that the learner owns the session. TestSession does not currently persist learner ownership, so the service does not infer ownership from a session ID.
- Completion time comes from an injected timezone-aware wall clock, not TestEngine's monotonic timer values.

## Non-goals

- No schema migration or duplicate mutable history store.
- No replacement of Phase 6.7 scoring, Phase 6.8 analytics, Phase 6.9 long-term history or Phase 6.10 question-level memory.
- No claim of atomic commit across separate repositories. A future database transaction/outbox boundary can provide stronger cross-store guarantees.

## Validation coverage

- End-to-end score, weak topic, long-term topic aggregate and per-question memory.
- Idempotent re-processing of one completed session.
- Rejection of unfinished sessions, mismatched question sets, unaccepted questions and mismatched stored result identity.
- Retry after a question-history write failure with the original timestamp preserved.
