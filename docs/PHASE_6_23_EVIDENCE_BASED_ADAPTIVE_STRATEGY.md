# Phase 6.23 — Evidence-Based Adaptive Study Strategy

## Goal

Turn Phase 6.22's read-only study execution/outcome correlation into a conservative recommendation for the learner's next study strategy. The report is proposed guidance, not a mutation of learner history, an existing schedule, or the spaced-revision store.

## Existing contracts reused

- Phase 6.20: immutable schedule tasks and their evidence-backed concept/question scope.
- Phase 6.21: append-only task-execution observations and terminal skipped/postponed states.
- Phase 6.22: real assessment outcomes, explicit question/concept linkage, baseline/follow-up sample counts, trend and evidence sufficiency.
- Existing LearningTrend, StudyTaskKind and StudyTaskExecutionStatus vocabularies; no parallel history or scoring engine is introduced.

## Decision rules

- Only direct-question or explicit-concept linked evidence can drive a recommendation.
- Both baseline and follow-up samples must meet the configurable minimums, and the source trend must be supported.
- A declining linked trend modestly raises the task priority (bounded to 0–1) and suggests a short one-day review interval.
- An improving trend below the consolidation threshold continues targeted practice and suggests five days to review.
- An improving trend with follow-up accuracy meeting the consolidation threshold slightly reduces priority and suggests seven days to review.
- A stable trend keeps priority and suggests a three-day retest interval.
- Insufficient samples, missing linkage, skipped work, or postponed work leaves priority untouched and returns no revision interval.
- Assessment deltas are descriptive associations, not proof that study execution caused a score change.

## Deliverables

- Domain contracts in src/ai_comp/domain/adaptive_study_strategy.py.
- Deterministic strategy policy/service in src/ai_comp/analysis/adaptive_study_strategy.py.
- Regression tests in tests/test_adaptive_study_strategy.py.

No database migration is needed for this derived, read-only report. The suggested interval and priority are not silently written back into Phase 6.20/6.21 or the spaced-revision engine; a later integration can explicitly consume this contract.

## Validation scope

Covers decline/improvement/stability strategies, priority boundaries and conservative changes, insufficient samples, direct evidence requirements, skipped/postponed work, learner/schedule isolation, policy validation and timezone-aware report generation.
