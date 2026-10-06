# Phase 5.5.2 — Durable Resume & Partial-Failure Recovery

## Completed baseline: Phase 5.5.1

Phase 5.5.1 established:

- durable ingestion job identity;
- idempotency key based on document SHA-256 + exam/paper/year/shift;
- optimistic job version;
- transactional job-state + outbox writes;
- retryable and terminal failure states.

CI Run #192 verified that baseline with all tests green.

## Stage checkpoints

Phase 5.5.2 now activates the stage lifecycle:

DISCOVERED
-> FETCHED
-> PROCESSING
-> EXTRACTED
-> MATCHED
-> MASTERED
-> HISTORICAL_RECORDED
-> COMPLETED

The durable job status represents the last completed ingestion checkpoint.

## Resume rules

On failure:

- the current durable checkpoint is preserved;
- the job becomes RETRYABLE until the configured attempt limit;
- resume_after records the last successful checkpoint.

On retry:

- the job transitions back to PROCESSING;
- the processor receives resume_after;
- EXTRACTED resumes from persisted questions/answer-key data;
- MATCHED resumes from persisted question matches;
- MASTERED resumes from persisted master memberships;
- HISTORICAL_RECORDED only needs the final job completion transition.

Earlier persistence operations remain idempotent so a crash between a side effect and its checkpoint transition can safely replay that one stage.

## Partial-failure examples

Extraction succeeds -> EXTRACTED is committed -> matching fails.

Retry resumes from EXTRACTED; question extraction is not repeated.

Matching succeeds -> MATCHED is committed -> master assignment fails.

Retry resumes from MATCHED; persisted matches are reused.

Master assignment succeeds -> MASTERED is committed -> history write fails.

Retry resumes from MASTERED; existing master memberships are reused and deterministic appearance IDs keep history logically single.

## Exactly-once logical processing

The system may physically execute a stage more than once after a crash boundary.

The logical guarantee is stronger:

- one ingestion job per idempotency key;
- versioned transitions prevent silent concurrent overwrites;
- each transition has one deterministic outbox dedupe key;
- question, match, master and appearance persistence already use idempotent/deduplicated identities;
- retries converge on one logical paper/history state.

No claim is made that an external message broker provides exactly-once delivery. Outbox consumers must remain idempotent.

## Current scope

Implemented:

- durable stage checkpoints;
- checkpoint-aware resume;
- partial-failure recovery tests;
- reuse of persisted questions, matches and master memberships;
- retry-safe continuation of verified history.

Next: **Phase 5.5.3 — durable batch paper lifecycle**, where a discovered paper set becomes a batch with its own idempotency, aggregate progress, partial-success status and restart-safe batch resume.
