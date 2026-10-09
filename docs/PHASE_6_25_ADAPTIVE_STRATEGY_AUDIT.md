# Phase 6.25 — Adaptive Strategy Persistence and Audit History

## Goal

Persist the evidence, strategy recommendation, and resulting schedule from Phase 6.23/6.24 as a durable, immutable audit. This adds no parallel scheduler and does not overwrite learner history or prior schedules.

## Persistence model

Migration 0014_phase6_25_adaptive_strategy_audit.sql adds:

- adaptive_study_strategy_audits: idempotency key, learner and assessment scope, source/result schedule fingerprints, recorded time, canonical payload SHA-256, and JSONB snapshots of the source schedule, strategy report, and resulting schedule.
- adaptive_study_strategy_audit_adjustments: queryable per-task action, evidence/trend, previous and recommended priority, applied priority observed in the resulting schedule, revision interval, baseline/follow-up counts and accuracy, score delta, and reason.

## Contracts and behavior

- AdaptiveStudyStrategyAudit validates learner identity, source schedule/report fingerprint, task identity/kind, previous priority, result timing, and timezone-aware audit timestamps.
- AdaptiveStudyStrategyAuditService captures the source schedule, report, and result schedule through one repository operation. If recorded_at is omitted, it uses the resulting schedule's deterministic generation time so identical retries stay idempotent.
- PostgresAdaptiveStudyStrategyAuditRepository writes parent snapshots and adjustment rows in one transaction.
- Reusing an audit_id with the same evidence returns the original record. Reusing that key with different snapshots raises AdaptiveStudyStrategyAuditConflictError; no update path exists.
- History is learner-scoped and paginated with a bounded limit. JSONB snapshots are reconstructed into the existing typed domain contracts.

## Tests

Unit tests cover round-trip through a repository contract, same-payload retry, conflicting retry, identity/fingerprint checks, and timestamp ordering. PostgreSQL integration tests cover migration application, durable readback, idempotency, conflicting retries, and learner-scoped history. The schema contract checks the append-only parent/adjustment tables and indexed history path.
