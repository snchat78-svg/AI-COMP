# Phase 6.13 — Adaptive Difficulty Evolution + Learning Retention Intelligence

## Purpose

Phase 6.13 converts the durable learner history from Phases 6.9, 6.10 and 6.12 into a conservative adaptive difficulty decision.

The system answers:
- whether a learner is still learning a concept
- whether performance is stable enough to advance
- whether a concept has reached repeated high-performance mastery
- whether a previously strong question now requires retention review

## Evidence flow

Phase 6.9 LearnerLearningHistory
+
Phase 6.10 LearnerQuestionHistory
+
Phase 6.12 SpacedRevisionService
then Phase 6.13 AdaptiveDifficultyService
then concept-level mastery/action/difficulty plus due retention question IDs
then Phase 6.11 PersonalizedPreparationPlan

No historical truth is created by this phase. It only derives learner-state decisions from persisted outcome records already established by earlier phases.

## Deterministic policy

### Remediation

A concept is LEARNING and receives REMEDIATE + EASY when recent or cumulative accuracy is below 0.50, the weak streak is active, or a repeated-concept weakness alert exists.

### Stabilization

Insufficient evidence or non-mastery performance remains MEDIUM. The system does not jump to HARD from a single good test.

### Advancement

A concept becomes MASTERED only after at least 3 tests with cumulative accuracy >= 0.85, recent accuracy >= 0.85, and no declining trend. It receives ADVANCE + HARD.

### Retention

A strong concept with at least one due spaced-review question becomes RETENTION_DUE and receives RETAIN + MEDIUM. Retention is checked before advancement so mastery never removes a topic permanently.

## Safety properties

- Only existing learner history is used.
- No AI/LLM call is required.
- No new mutable schedule table duplicates Phase 6.12.
- Difficulty preference never changes score truth or answer verification.
- GeneratedQuestionStatus.ACCEPTED remains the test-engine gate.
- Phase 6.6 ranking remains the candidate quality/ranking source.
- Retention due is advisory state derived from the existing question schedule.
- With no history, the global default is MEDIUM.
