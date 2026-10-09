# Phase 6.24 — Adaptive Strategy and Schedule Integration

## Goal

Connect Phase 6.23's evidence-based strategy recommendations to the canonical Phase 6.21 capacity-aware schedule replan path without creating a second scheduler or mutating the source schedule/history.

## Implementation

StudyScheduleExecutionService.replan now accepts an optional AdaptiveStudyStrategyReport.

- Verifies learner identity, source schedule fingerprint, source task existence/kind, and that the supplied planning clock does not precede strategy report generation.
- Reuses Phase 6.21 execution events and unfinished-work calculation. Completed/skipped tasks remain excluded by the existing replan contract.
- Applies recommendations only to unfinished work with explicit overlap in question IDs or concept IDs from the source task.
- COLLECT_MORE_EVIDENCE recommendations have no scheduling effect.
- Linked recommendations update proposed priority and earliest suggested next-review date; task deadline takes precedence when it is earlier.
- For overlapping recommendations, the highest suggested priority and earliest review date win deterministically.
- Existing postponement, partial completion, daily capacity, exam-day, unscheduled-work and legacy no-strategy behavior remain owned by the original replan path.

The original schedule fingerprint and append-only execution records are not rewritten. Only the newly generated schedule reflects eligible recommendations. If no report is supplied, existing Phase 6.21 behavior is preserved.

## Files

- src/ai_comp/analysis/study_schedule_execution.py
- tests/test_adaptive_schedule_strategy_integration.py

No migration is necessary: this feature consumes Phase 6.23's derived report and the existing execution repository.

## Regression coverage

Tests cover priority propagation and interval-aware scheduling, evidence-limited no-op behaviour, schedule fingerprint isolation, planning-clock validation, and backwards compatibility when the optional strategy report is omitted.
