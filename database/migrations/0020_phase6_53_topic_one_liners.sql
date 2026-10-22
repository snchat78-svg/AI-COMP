-- Phase 6.53: topic-linked one-liner Q&A with auditable evidence.
-- Historical exam questions remain in the Phase 2.4 tables; this is a separate
-- learning-content store and must never be counted as historical exam history.

BEGIN;

CREATE TABLE IF NOT EXISTS question_bank_one_liners (
    one_liner_id TEXT PRIMARY KEY,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    question_text TEXT NOT NULL CHECK (length(btrim(question_text)) > 0),
    answer_text TEXT NOT NULL CHECK (length(btrim(answer_text)) > 0),
    language_code TEXT NOT NULL DEFAULT 'hi' CHECK (length(btrim(language_code)) > 0),
    source_url TEXT,
    source_evidence TEXT NOT NULL DEFAULT '',
    verification_status TEXT NOT NULL DEFAULT 'NEEDS_REVIEW' CHECK (
        verification_status IN ('DRAFT', 'NEEDS_REVIEW', 'VERIFIED', 'REJECTED')
    ),
    importance_score DOUBLE PRECISION NOT NULL DEFAULT 0.5 CHECK (
        importance_score BETWEEN 0.0 AND 1.0
    ),
    content_hash CHAR(64) NOT NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        verification_status <> 'VERIFIED'
        OR (
            source_url LIKE 'https://%'
            AND length(btrim(source_evidence)) > 0
            AND reviewed_at IS NOT NULL
        )
    ),
    UNIQUE (concept_id, language_code, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_question_bank_one_liners_concept_status
    ON question_bank_one_liners(concept_id, verification_status, importance_score DESC);

CREATE INDEX IF NOT EXISTS idx_question_bank_one_liners_language
    ON question_bank_one_liners(language_code, verification_status);

COMMIT;
