-- Phase 5.5 durable ingestion job, idempotency and transactional outbox.
-- Job state and its lifecycle event must be committed together.

BEGIN;

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id TEXT PRIMARY KEY,
    idempotency_key CHAR(64) NOT NULL UNIQUE,
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    document_sha256 CHAR(64) NOT NULL,
    paper_id TEXT NOT NULL REFERENCES papers(paper_id),
    exam_id TEXT NOT NULL REFERENCES exams(exam_id),
    year INTEGER NOT NULL CHECK (year >= 1900),
    shift TEXT,
    source_url TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN (
            'DISCOVERED',
            'FETCHED',
            'PROCESSING',
            'EXTRACTED',
            'MATCHED',
            'MASTERED',
            'HISTORICAL_RECORDED',
            'COMPLETED',
            'RETRYABLE',
            'FAILED'
        )
    ),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0),
    checkpoint JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ingestion_outbox (
    event_id TEXT PRIMARY KEY,
    dedupe_key TEXT NOT NULL UNIQUE,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL CHECK (aggregate_version >= 0),
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    last_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status
    ON ingestion_jobs(status);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_document
    ON ingestion_jobs(document_id);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_paper
    ON ingestion_jobs(paper_id);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_retryable
    ON ingestion_jobs(status, updated_at)
    WHERE status = 'RETRYABLE';

CREATE INDEX IF NOT EXISTS idx_ingestion_outbox_unpublished
    ON ingestion_outbox(created_at, event_id)
    WHERE published_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_ingestion_outbox_aggregate
    ON ingestion_outbox(aggregate_type, aggregate_id, aggregate_version);

COMMIT;
