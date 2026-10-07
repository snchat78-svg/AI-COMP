# Phase 6.9 — Durable Learning History and Long-Term Personalization

Phase 6.9 extends the Phase 6.8 short-term remediation loop into persistent,
learner-specific memory:

```
Completed Test
    ↓
Phase 6.8 TestAnalysis
    ↓
Learner Test Attempt
    ↓
Per-Concept Test Snapshot
    ↓
Cross-Test Aggregation
    ↓
Long-Term Accuracy + Recent Accuracy
    ↓
Trend + Weak Streak + Priority
    ↓
Personalized Recommendation
    ↓
Personalized Next-Test Selection
    ↓
Phase 6.7 Test Engine
```

## Durable model

Two records are persisted:

- `learner_test_attempts`: immutable test-level outcome for a learner/session.
- `learner_topic_attempts`: immutable per-concept snapshot for that attempt.

The attempt identity is SHA-256 over learner ID + session ID. The same learner/session
cannot create duplicate logical history. Replaying the same completed analysis is
idempotent; conflicting data is rejected.

## Long-term aggregation

For each concept the service computes:

- cumulative accuracy,
- latest-test accuracy,
- number of test appearances,
- weak streak,
- trend,
- deterministic priority score.

Priority:

`0.55*(1-cumulative_accuracy) + 0.30*(1-recent_accuracy) +
0.15*min(weak_streak,3)/3`

The score is bounded to 0..1.

## Personalization rules

- Long-term weak topics are preferred over a single-test recommendation.
- Declining topics receive a specific trend reason.
- Two or more consecutive weak tests are explicitly surfaced.
- Very low recent accuracy recommends EASY remediation; otherwise MEDIUM.
- The selector reserves up to 75% of the next test for long-term remediation.
- Recent question IDs are still avoided before older questions when possible.
- Phase 6.6 ranking remains the scoring source for candidate quality.
- Only ACCEPTED generated questions can enter the next test.

## Safety and boundaries

This phase does not modify historical exam provenance, master-question identity,
or answer verification. Learner performance is based only on stored TestAnalysis
outcomes and the immutable stored correct answers already used by Phase 6.7.

Long-term history is learner-scoped. One learner's performance cannot affect another
learner's recommendations.

The next layer can add durable user preferences, retention/forgetting models, spaced
repetition, and time-aware learning schedules without replacing this history contract.
