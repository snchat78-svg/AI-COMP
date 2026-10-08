# Phase 6.14 — Adaptive Test Composition + Topic Coverage Balancing

## Purpose

Phase 6.14 adds the selection layer that converts learner state into a balanced test composition.

It combines:
- Phase 6.10 previous-mistake memory
- Phase 6.12 spaced-review due state
- Phase 6.13 remediation, stabilization, retention and advancement decisions
- Phase 6.6 question-intelligence ranking

The existing TestEngine contract is unchanged.

## Selection order

1. Retention-due questions
2. Previous-mistake questions
3. Remediation questions for weak concepts
4. Advancement questions for mastered concepts
5. General Phase 6.6 ranked questions

Earlier stages do not blindly consume the entire test. Configurable ratios leave room for later stages.

## Topic coverage

When alternatives exist, the composer prefers concepts with lower current representation and respects a configurable maximum concept ratio.

The maximum is a balancing preference, not a hard rejection: when the pool cannot satisfy diversity, available questions are still selected.

## Difficulty

Candidate difficulty is matched against the Phase 6.13 concept recommendation before Phase 6.6 selection quality tie-breakers.

This does not mutate the question difficulty, answer, score, verification status or historical truth.

## Safety and compatibility

- Only GeneratedQuestionStatus.ACCEPTED candidates are eligible.
- Explicit exclusions remain enforced.
- Duplicate question IDs are rejected.
- Insufficient pools fail closed.
- Phase 6.6 ranking remains a deterministic quality signal.
- Phase 6.12 remains the only source of review-due state.
- Phase 6.13 remains the source of mastery/action state.
- No LLM call is required.
- No database migration is required.
- Existing Phase 6.7 TestEngine.create_session() can consume the returned ranked candidates directly.
