# Phase 6.15 — Adaptive Test Session Orchestration

## Purpose

Phase 6.15 provides one application-level entry point that composes an adaptive test and hands it to the established Phase 6.7 TestEngine.

It connects:
- Phase 6.10 mistake history
- Phase 6.12 spaced revision
- Phase 6.13 mastery and difficulty decisions
- Phase 6.14 coverage-balanced test composition
- Phase 6.7 timed test sessions

## Flow

Learner histories + accepted ranked candidates
then AdaptiveTestCompositionService
then AdaptiveTestCompositionPlan
then TestSpecification
then TestEngine.create_session
then CREATED session
then explicit start call
then IN_PROGRESS session with deadline

## Contracts

- create_session returns the selected composition, test specification and created session together.
- The resulting session contains exactly the question IDs from the composition plan. Deterministic shuffling may change their order only when explicitly enabled.
- Creating a session does not start its timer. start(session_id) must be called explicitly.
- The existing TestEngine still owns validation, session persistence, timing, answers and scoring.
- All eligibility, answer-verification and quality gates from earlier phases remain unchanged.
- Insufficient pools, exclusions and reused session IDs fail closed.

## Persistence

No additional database migration is needed. The service uses the existing test-session repository configured in TestEngine. The service is provider-neutral and deterministic apart from the configured clock and explicit shuffle seed.
