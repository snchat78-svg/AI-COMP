# Phase 6.26 — Adaptive Strategy Workflow and History Comparison

## Goal

Wire Phase 6.24 strategy-aware schedule replanning into Phase 6.25 durable audit persistence, then provide learner-scoped retrieval and descriptive comparisons over prior audit records.

## Application flow

AdaptiveStudyStrategyWorkflow.apply_and_record performs the canonical schedule replan with the Phase 6.23 report, persists the exact source/report/result triple through AdaptiveStudyStrategyAuditService, and returns the resulting schedule with its audit record. Callers provide a stable audit_id and timezone-aware as_of clock, enabling deterministic retries. Replanning validation failures do not write audit records.

## History comparison

AdaptiveStudyStrategyHistoryService reads only the supplied learner's existing immutable audits. It returns ordered audit entries and groups decisions by stable concept IDs (or question IDs when no concept scope exists) plus task kind. Summaries contain observed trend counts, baseline/follow-up accuracy means, mean accuracy delta, recommended priority delta, and the change visible in the resulting schedule.

These are descriptive historical summaries, not causal estimates or mastery guarantees. Results are bounded to at most 500 records and are not written back into learner history.

## Tests

Unit tests cover orchestration, schedule + audit consistency, repeat-call idempotency with stable request inputs, no audit after failed replanning, and history trend aggregation/scoping/time validation. The PostgreSQL integration test runs the combined workflow against the existing Phase 6.21 execution repository and Phase 6.25 audit repository.
