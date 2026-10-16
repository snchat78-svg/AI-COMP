-- Phase 2.4: audited linkage between a question paper and its official key.
-- Pairing is persisted separately from appearances and never inferred from URL similarity alone.

BEGIN;

CREATE TABLE IF NOT EXISTS paper_answer_key_pairs (
    pair_id TEXT PRIMARY KEY,
    question_paper_id TEXT NOT NULL REFERENCES papers(paper_id),
    answer_key_paper_id TEXT NOT NULL REFERENCES papers(paper_id),
    question_candidate_id TEXT NOT NULL REFERENCES paper_candidates(candidate_id),
    answer_key_candidate_id TEXT NOT NULL REFERENCES paper_candidates(candidate_id),
    question_document_id TEXT NOT NULL REFERENCES documents(document_id),
    answer_key_document_id TEXT NOT NULL REFERENCES documents(document_id),
    exam_id TEXT NOT NULL REFERENCES exams(exam_id),
    year INTEGER NOT NULL CHECK (year >= 1900),
    shift TEXT,
    pair_status TEXT NOT NULL CHECK (pair_status IN ('MATCHED', 'NEEDS_REVIEW')),
    match_reason TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (question_candidate_id <> answer_key_candidate_id),
    UNIQUE (question_candidate_id, answer_key_candidate_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_matched_question_paper_answer_key
    ON paper_answer_key_pairs(question_candidate_id)
    WHERE pair_status = 'MATCHED';

CREATE UNIQUE INDEX IF NOT EXISTS uq_matched_answer_key_candidate
    ON paper_answer_key_pairs(answer_key_candidate_id)
    WHERE pair_status = 'MATCHED';

CREATE INDEX IF NOT EXISTS idx_paper_answer_key_pairs_exam_year
    ON paper_answer_key_pairs(exam_id, year, shift, pair_status);

CREATE TABLE IF NOT EXISTS paper_verification_state (
    candidate_id TEXT PRIMARY KEY REFERENCES paper_candidates(candidate_id) ON DELETE CASCADE,
    exam_id TEXT REFERENCES exams(exam_id),
    year INTEGER CHECK (year IS NULL OR year >= 1900),
    shift TEXT,
    artifact_role TEXT NOT NULL CHECK (
        artifact_role IN ('QUESTION_PAPER', 'ANSWER_KEY', 'UNKNOWN')
    ),
    state TEXT NOT NULL CHECK (
        state IN ('READY', 'NEEDS_REVIEW', 'HISTORY_RECORDED', 'FAILED')
    ),
    paired_answer_key_candidate_id TEXT REFERENCES paper_candidates(candidate_id),
    paired_answer_key_sha256 CHAR(64),
    reason TEXT NOT NULL DEFAULT '',
    last_processed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_paper_verification_state_state
    ON paper_verification_state(state, updated_at);

-- Keep the question-paper document identity used by the resolver separate
-- from the actual source document that supplied the answer key.
ALTER TABLE question_answer_records
    ADD COLUMN IF NOT EXISTS source_answer_key_document_id TEXT
    REFERENCES documents(document_id);

CREATE INDEX IF NOT EXISTS idx_question_answer_key_source_document
    ON question_answer_records(source_answer_key_document_id);

COMMIT;
