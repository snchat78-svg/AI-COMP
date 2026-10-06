# Phase 5.5.1 — Durable Ingestion Job, Idempotency & Transactional Outbox

## Purpose

Phase 5.5 starts the durable paper-processing lifecycle after Phase 5.4.

The first increment establishes a durable identity for an ingestion attempt and an atomic job-state + outbox-event transaction boundary.

## Durable job identity

The idempotency key is derived from:

- document SHA-256
- exam ID
- paper ID
- year
- shift

The source URL is intentionally excluded. Therefore, a copy of the same document discovered from another website resolves to the same logical ingestion job instead of creating another processing record.

The job table also carries an optimistic version. A transition can only update the version it previously read, which prevents two workers from silently overwriting one another.

## Job lifecycle

Defined statuses:

DISCOVERED -> FETCHED -> PROCESSING -> EXTRACTED -> MATCHED -> MASTERED -> HISTORICAL_RECORDED -> COMPLETED

Failure states:

RETRYABLE

FAILED

The current 5.5.1 runner activates the durable coarse-grained path:

DISCOVERED -> FETCHED -> PROCESSING -> COMPLETED

The finer extraction/matching/master/history checkpoints are defined now and will be activated by the next resume increment.

## Transactional outbox

Every durable lifecycle transition writes:

1. the new ingestion job version;
2. one deterministic outbox event for that version;

inside the same transaction.

If the transaction fails, neither the job transition nor its outbox event remains committed.

Outbox delivery is intentionally separate from the transaction. The stored event can later be published by a worker and marked published_at. A real external broker still requires idempotent consumers; the outbox itself guarantees durable event intent, not exactly-once delivery to an external system.

## Exactly-once logical processing

This phase does not claim that the processor never executes twice.

The guarantee being established is:

- one logical job per idempotency key;
- completed jobs are not processed again;
- retryable jobs may be executed again;
- persistence uses deterministic/idempotent keys so future retries can converge to one logical paper/history record.

## Scope of this increment

Implemented:

- IngestionJob
- status model and versioned transitions
- deterministic idempotency key
- transactional job + outbox boundary
- PostgreSQL persistence
- in-memory rollback tests
- retryable/terminal failure state
- durable result checkpoint

Next increment, Phase 5.5.2:

- stage-by-stage checkpoints from Phase 5.4
- true resume from EXTRACTED / MATCHED / MASTERED / HISTORICAL_RECORDED
- partial-failure recovery
- restart-safe continuation
- batch paper lifecycle with durable batch state
