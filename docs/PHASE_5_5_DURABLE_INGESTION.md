# Phase 5.5 — Durable Ingestion, Recovery & Batch Lifecycle

## Verified baseline

Phase 5.4 provides the auditable ingestion lifecycle:

NormalizedDocument
-> QuestionExtraction
-> QuestionPersistence
-> AnswerResolution
-> MatchPersistence
-> MasterAssignment
-> Verified ExamAppearance

Only VERIFIED source evidence can create historical exam appearances.

## Phase 5.5.1 — Durable job identity

A durable IngestionJob is keyed by a SHA-256 idempotency key derived from:

- document SHA-256;
- exam ID;
- paper ID;
- year;
- shift.

Source URL is excluded so the same document discovered through a mirror does not create a second logical job.

Job state is versioned for optimistic concurrency. Job state and its lifecycle outbox event are committed together.

## Phase 5.5.2 — Resume & partial-failure recovery

The job lifecycle now persists these checkpoints:

DISCOVERED -> FETCHED -> PROCESSING -> EXTRACTED -> MATCHED -> MASTERED -> HISTORICAL_RECORDED -> COMPLETED

A retry carries the last durable checkpoint as resume_after.

Examples:

- EXTRACTED committed -> matching fails -> retry resumes from persisted questions.
- MATCHED committed -> master assignment fails -> retry reuses persisted matches.
- MASTERED committed -> history write fails -> retry reuses existing memberships and deterministic appearance IDs.

The implementation does not claim physical exactly-once execution. It guarantees one logical job per idempotency key and restart-safe convergence through idempotent persistence and versioned transitions.

## Phase 5.5.3 — Batch paper lifecycle

An IngestionBatch groups the logical jobs produced from one discovered paper set.

### Batch identity

Batch idempotency is the SHA-256 digest of the sorted logical job idempotency keys.

Therefore:

- request order does not change the batch identity;
- duplicate mirror URLs for the same logical paper do not increase batch size;
- one real paper maps to one logical job inside the batch.

When duplicate requests share a logical job key, the canonical request prefers stronger source verification (VERIFIED > SECONDARY_LIKELY > UNVERIFIED) and then deterministic source URL ordering.

### Batch states

DISCOVERED -> RUNNING -> COMPLETED

RUNNING -> PARTIAL_FAILURE

RUNNING -> FAILED

PARTIAL_FAILURE -> RUNNING -> COMPLETED / PARTIAL_FAILURE / FAILED

PARTIAL_FAILURE is resumable. FAILED is terminal when every item is terminally failed.

### Aggregate progress

The batch persists:

- total_jobs
- completed_jobs
- retryable_jobs
- failed_jobs
- pending_jobs (derived)

A batch refresh reads the durable job state for every item. If the process crashes after a job completes but before the batch refresh commits, the next run recomputes the counts safely.

### Restart behavior

On rerun:

- COMPLETED jobs are skipped;
- RETRYABLE jobs are retried through the existing IngestionJobService;
- FAILED jobs are retained as terminal failures;
- the batch recomputes aggregate progress before deciding its next state.

Batch state and batch outbox events use an optimistic version and deterministic dedupe key.

### Exactly-once logical processing boundary

The platform now has two nested idempotency levels:

Batch idempotency
-> one stable paper-set aggregate

Job idempotency
-> one stable logical paper-processing aggregate

The physical processor may run again after a crash, but the durable job/batch state and downstream deduplication prevent duplicate logical history from being counted.

The outbox is a durable event-intent store. External delivery remains an at-least-once concern and consumers must be idempotent.

## Phase 5.5 completion

The requested durable chain is now covered:

Durable Transaction Boundary
-> Ingestion Job
-> Idempotency Key
-> Outbox Event
-> Retry / Resume
-> Partial Failure Recovery
-> Exactly-once logical processing
-> Batch Paper Lifecycle

Next major product phase: Phase 6 — AI Material Analysis, while continuous exam-research scheduling can later consume the same durable batch lifecycle.
