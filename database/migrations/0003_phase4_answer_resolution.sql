-- Phase 4 answer-resolution persistence.
-- Source answer keys remain separate from resolved question answers.

BEGIN;

CREATE TABLE IF NOT EXISTS question_answer_records (
    answer_record_id BIGSERIAL PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    question_number INTEGER NOT NULL CHECK (question_number > 0),
    answer_key TEXT NOT NULL,
    selected_option_key TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('RESOLVED', 'MISSING_QUESTION', 'INVALID_OPTION', 'AMBIGUOUS')
    ),
    method TEXT CHECK (
        method IS NULL OR method IN (
            'DIRECT_OPTION_KEY',
            'POSITIONAL_NUMERIC',
            'POSITIONAL_HINDI'
        )
    ),
    source_line INTEGER NOT NULL CHECK (source_line > 0),
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (question_id, document_id)
);

CREATE INDEX IF NOT EXISTS idx_question_answers_question
    ON question_answer_records(question_id);

COMMIT;
