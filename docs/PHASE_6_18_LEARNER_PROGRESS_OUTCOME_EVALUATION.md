# Phase 6.18 — Learner Progress and Outcome Evaluation

## Goal

Measure whether a learner's recent completed-test outcomes are improving, stable, declining, or not yet supported by enough data. Surface the existing topic-priority and adaptive mastery signals in one read-only progress report.

## Flow

Phase 6.9 LearnerLearningHistory
plus Phase 6.10 LearnerQuestionHistory
plus optional Phase 6.13 AdaptiveDifficultyProfile
then Phase 6.18 LearningProgressService
then LearnerProgressReport

## Contract

- Overall progress compares the latest equal-sized window of completed-test percentages against the immediately preceding window.
- The default comparison window is up to three tests per side; fewer than two total tests yields INSUFFICIENT_DATA.
- A score movement of at least five percentage points is classified as IMPROVING or DECLINING; smaller changes are STABLE.
- Each topic uses the already-aggregated history accuracy/trend/priority. An optional adaptive profile adds existing mastery/action/reason and due-retention IDs.
- Question-level accuracy uses existing per-question outcomes and excludes unattempted questions from the denominator.
- Cross-learner data, duplicate sessions/outcomes, invalid score percentages and naive timestamps are rejected.
- The report is read-only: no history writes, schema migration, new schedule store, or model/LLM call.

## Interpretation boundary

This is descriptive progress, not a causal claim about learning. Percentages from tests with different difficulty or question composition are not strictly comparable; clients should display window counts and the trend as a signal, not a guarantee.

## Validation

Tests cover improving/stable/insufficient-data outcomes, question-level correctness, topic priority and adaptive decision reuse, learner isolation, and timezone validation.
