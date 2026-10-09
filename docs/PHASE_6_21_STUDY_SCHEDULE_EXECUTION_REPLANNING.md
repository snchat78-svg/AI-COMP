# Phase 6.21 — Study Schedule Execution and Replanning

## Goal

Make Phase 6.20 schedules actionable and auditable. Learners can record a task as completed, partially completed, skipped, or postponed. The next schedule carries forward unfinished work according to these events and actual remaining availability.

## Architecture

- \`StudySchedule.schedule_id\` is a stable SHA-256 fingerprint of the schedule's content and generation timestamp.
- \`StudyTaskExecution\` is an immutable event; \`event_id\` is its idempotency key.
- \`StudyTaskExecutionRepository\` separates the application service from storage.
- \`PostgresStudyTaskExecutionRepository\` stores append-only execution events in migration \`0013_phase6_21_schedule_execution.sql\`.
- \`StudyScheduleExecutionService\` validates event scope/transition rules and replans from the latest event for each task.

## Behavior

- COMPLETED tasks are removed from the next plan.
- SKIPPED tasks are not requeued.
- PARTIAL tasks carry their remaining minutes and omit question IDs explicitly marked completed.
- POSTPONED tasks are not eligible before the requested date; if that date exceeds the replan window, the task remains visible as unallocated work.
- Previous unscheduled work is carried forward. Unallocated items retain their next eligible date.
- Replanning respects daily minutes, weekday overrides, an optional first-day remaining-time budget, exam-day exclusion, and the configured maximum planning window.
- The service returns to the existing generated-question/task contracts; it does not generate questions, assert answer correctness, or write fake test outcomes.

## Data integrity

- Learner ID, schedule fingerprint, task membership, timezone-aware event timestamps, and question membership are validated.
- Same event ID + identical payload is idempotent; reuse with different data raises a conflict.
- Event records are append-only. A task in a terminal state cannot be reopened in the same schedule. Partial progress is monotonic.
- PostgreSQL persistence is database-neutral at the domain/service boundary; a schema migration and repository implementation make execution state durable.
- There is no new question-selection logic. Existing personalized plan, learning history, and spaced revision remain the source of recommendations.

## Validation

Unit tests cover idempotency/conflicts, partial-progress monotonicity, task transitions, completed/skipped removal, postponed dates, carry-forward, exam-day exclusion, capacity budgets, learner/schedule/question isolation, and invalid input. A PostgreSQL integration test covers round-trip persistence and conflict behavior.
