-- Phase 5.5.3 durable batch paper lifecycle.
-- A batch groups logical ingestion jobs and tracks aggregate progress.

BEGIN;

CREATE TABLE IF NOT EXISTS ingestion_batches (
    batch_id TEXT PRIMARY KEY,
    idempotency_key CHAR(64) NOT NULL UNIQUE,
    total_jobs INTEGER NOT NULL CHECK (total_jobs > 0),
    completed_jobs INTEGER NOT NULL DEFAULT 0 CHECK (completed_jobs >= 0),
    retryable_jobs INTEGER NOT NULL DEFAULT 0 CHECK (retryable_jobs >= 0),
    failed_jobs INTEGER NOT NULL DEFAULT 0 CHECK (failed_jobs >= 0),
    status TEXT NOT NULL CHECK (
        status IN (
            'DISCOVERED',
            'RUNNING',
            'COMPLETED',
            'PARTIAL_FAILURE',
            'FAILED'
        )
    ),
    version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0),
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CHECK (completed_jobs + retryable_jobs + failed_jobs <= total_jobs)
);

CREATE TABLE IF NOT EXISTS ingestion_batch_items (
    batch_id TEXT NOT NULL
        REFERENCES ingestion_batches(batch_id) ON DELETE CASCADE,
    job_id TEXT NOT NULL
        REFERENCES ingestion_jobs(job_id),
    item_order INTEGER NOT NULL CHECK (item_order > 0),
    PRIMARY KEY (batch_id, job_id),
    UNIQUE (batch_id, item_order)
);

CREATE INDEX IF NOT EXISTS idx_ingestion_batches_status
    ON ingestion_batches(status);

CREATE INDEX IF NOT EXISTS idx_ingestion_batches_retryable
    ON ingestion_batches(status, updated_at)
    WHERE status = 'PARTIAL_FAILURE';

CREATE INDEX IF NOT EXISTS idx_ingestion_batch_items_job
    ON ingestion_batch_items(job_id);

COMMIT;
