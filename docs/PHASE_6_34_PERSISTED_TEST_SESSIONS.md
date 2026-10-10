# Phase 6.34 — Persisted Preparation Test Sessions

## Purpose

Connect the Phase 6.32–6.33 saved preparation-request lifecycle to the canonical adaptive test engine. Sessions are created from the authenticated learner's active saved request and the accepted, answer-verified, non-duplicate question pool.

## API endpoints

- POST /api/v1/learners/{learner_id}/preparation-sessions creates a ready-to-start persisted session from active settings.
- GET /api/v1/learners/{learner_id}/preparation-sessions/{session_id} resumes session state and timer metadata.
- POST .../{session_id}/start starts the timer.
- GET .../{session_id}/current-question returns stem/options but no answer key.
- POST .../{session_id}/answer accepts a JSON option_key such as A.
- POST .../{session_id}/next, previous, and review persist navigation and review state.
- POST .../{session_id}/submit stores and returns the result; repeated submissions return the same result.

## Persistence and security

Migration 0016_phase6_34_preparation_test_sessions.sql stores learner/request linkage, the immutable test specification and selected question snapshots, plus status, cursor, answers, review flags, timer timestamps, and final score. Snapshots allow a later request or worker to reconstruct the same session without reranking its questions.

New session insertion locks the linked preparation request and confirms it remains ACTIVE in the same transaction. Every read/write is scoped by authenticated learner ID and session ID. Saved scoring/timing settings flow into TestEngine; the timer does not start until the explicit start endpoint.

The API uses wall-clock epoch timestamps for durable deadlines, instead of process-local monotonic time. The current-question response never returns the correct option or explanation.

## Scope

This phase exposes the persisted adaptive MCQ session lifecycle. It does not deploy a frontend or claim that optional exam/subject labels filter question selection. Verified eligibility and concept filtering remain governed by the existing question-context provider.

## Validation

PostgreSQL integration tests cover request-to-session linking, session reconstruction across requests, timer start, question loading without answer leakage, answer/navigation/review persistence, score calculation, repeat submit, learner isolation, and the no-active-request case.
