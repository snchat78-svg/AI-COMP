# Phase 6.22 — Study Execution and Learning Outcome Feedback

## Goal

Connect persisted Phase 6.21 execution events to a later, real CompletedTestFeedback snapshot so the app can report which follow-up outcomes overlap previously completed study work.

## Reused architecture

- Phase 6.20 schedule tasks supply planned question IDs and concept IDs.
- Phase 6.21 execution events supply append-only completion/partial/skip/postpone observations.
- Phase 6.16 CompletedTestFeedback and its TestAnalysis supply actual scored question outcomes.
- Phase 6.9/6.10 question history supplies pre-study baseline observations.
- The service is read-only over those systems: no second history store, fake questions, synthetic outcomes, or migration.

## Correlation rules

- Only execution events that occurred strictly before the completed assessment are eligible.
- The latest task event before assessment controls its status.
- COMPLETED and PARTIAL work can be compared; SKIPPED and POSTPONED work is not attributed as completed study.
- Direct overlap between studied question IDs and assessment question IDs has priority.
- Otherwise the service may associate the test with shared, explicit concept IDs.
- With no direct or concept evidence, the report explicitly records NO_RELATED_EVIDENCE.
- Baseline question outcomes must predate the first study execution event; follow-up outcomes come only from the assessment passed to this call.
- Accuracy is based on attempted answers; unattempted counts remain visible and do not inflate accuracy.

## Interpretation safeguards

- Configurable minimum baseline and follow-up sample counts are required before calculating a trend.
- Trends use a configurable percentage-point threshold and reuse the shared LearningTrend vocabulary.
- A positive delta means observed accuracy increased in the linked evidence; it is not proof the study task caused the change.
- Test difficulty and question mix can differ. Study completion alone is never treated as mastery.
- Missing, too-small, skipped, postponed, or post-assessment evidence yields insufficient/absent attribution, not a guessed improvement.
- Learner identity, assessment/session identity, timezone-aware timestamps, schedule/task scope, and deterministic event ordering are validated.

## Validation

Tests cover concept and direct-question correlation, baseline/follow-up score deltas, insufficient samples, skipped work, post-assessment exclusion, learner isolation, and policy validation. Existing persistence remains the responsibility of Phase 6.21 and CompletedTestFeedback repositories.
