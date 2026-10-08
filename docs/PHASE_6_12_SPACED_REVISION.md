# Phase 6.12 — Spaced Revision and Time-Aware Personalization

Phase 6.12 extends the existing learner memory with deterministic, time-aware
review scheduling. It uses the durable Phase 6.10 question outcomes and does not
create a second answer-judging system.

Flow:

Phase 6.7 Test Result
-> Phase 6.8 Analysis
-> Phase 6.9 Long-Term Topic History
-> Phase 6.10 Question-Level Memory
-> Phase 6.12 Review Schedule
-> Due / Upcoming Questions
-> Time-Aware Question Selector
-> Phase 6.6 Ranked Candidate
-> Phase 6.7 Test Engine

Spaced intervals:

- first successful review: 1 day
- second consecutive successful review: 3 days
- third consecutive successful review: 7 days
- later consecutive successes: interval doubles up to 30 days
- an incorrect or unattempted latest outcome resets the next interval to 1 day

A question is DUE when the calculated next review time has arrived. Overdue time
increases its deterministic priority.

Question selection:

- due questions are reserved for up to 60% of requested slots by default;
- among due questions, mistake history and overdue duration are preferred;
- upcoming review questions are preferred before unscheduled questions;
- Phase 6.6 selection score remains the quality ranking for non-review tie-breaks;
- only ACCEPTED generated questions are eligible;
- explicit exclusions are honored.

Safety:

The schedule is derived only from stored learner question outcomes. It does not
modify exam history, master-question identity, source verification, or answers.
No AI provider is required. Learner data remains scoped to the requested learner.

This layer is intentionally derived rather than a new mutable schedule table: the
existing durable outcome timestamps are the source of truth, avoiding duplicated
state that could drift from actual learner history.
