# Phase 6.20 — Daily and Weekly Study Schedule

## Goal

Convert the existing progress-aware preparation guidance into an actionable, time-bounded daily/weekly schedule. Inputs include learner histories, the existing personalized plan, accepted question records, available minutes per weekday, a planning horizon, and an optional upcoming exam date.

## Existing architecture reused

- Phase 6.9 / 6.10: durable learner and question-level history.
- Phase 6.11: the canonical personalized preparation plan, selected questions, weak concepts, and previous mistakes.
- Phase 6.12: SpacedRevisionService remains the authority for determining which selected questions are actually due.
- Phase 6.13 / 6.14: adaptive priorities and question ranking already reflected in the guidance plan.
- Phase 6.18 / 6.19: progress report and explainable preparation guidance.
- Phase 6.20: StudyScheduleService allocates this existing work into calendar days; it does not make a second question-selection engine.

## Schedule behavior

- Produces a day plan for each calendar date in the requested window.
- Supports one default number of study minutes per day and weekday-specific overrides (Monday=0 through Sunday=6).
- Plans stop at the earlier of the requested horizon or exam date. The exam date itself is present as a zero-study day so no learning task is assigned on exam day.
- Schedules due revision first, then selected previous mistakes, evidence-ranked weak concepts, and remaining accepted questions from the existing plan.
- Applies a configurable urgency bonus to practice questions when the exam date is close.
- Splits topic-study blocks across days when necessary; individual question reviews remain atomic.
- Keeps every daily plan within available minutes and caps each study block at the configured maximum duration.
- Reports work that could not fit in the calendar, including its remaining minutes, priority, evidence-based reason, and deadline rather than silently dropping it.

## Generic-code guarantees

- No exam names, subjects, concept IDs, or question IDs are hard-coded.
- The service accepts learner-selected availability and dates, and its minute estimates/urgency settings are configurable through StudySchedulePolicy.
- It schedules only accepted questions already present in the Phase 6.19 preparation plan.
- Question revision due dates are computed through the existing SpacedRevisionService and are not independently reimplemented.
- Question IDs cannot be scheduled twice in the same schedule or simultaneously be scheduled and reported as unallocated.
- Learner identity is validated across guidance and both histories. Missing/non-accepted planned questions and malformed availability are rejected clearly.
- No database migration, duplicate learning history, or mutable learner state is added.

## Validation

Tests cover each task type, weak-topic mapping, per-weekday capacity, exam-day exclusion, zero-time/unallocated work, learner isolation, accepted-question checks, invalid date/availability inputs, policy bounds, and daily-budget invariants.
