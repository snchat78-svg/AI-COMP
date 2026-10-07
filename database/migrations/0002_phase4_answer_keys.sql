-- Phase 4 persistence completion: extracted answer-key records.
-- Kept separate from questions because extraction observes source text;
-- answer reconciliation/verification is a later business step.

BEGIN;

CREATE TABLE IF NOT EXISTS answer_key_entries (
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    question_number INTEGER NOT NULL CHECK (question_number > 0),
    answer_key TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (document_id, question_number)
);

CREATE INDEX IF NOT EXISTS idx_answer_key_question_number
    ON answer_key_entries(question_number);

COMMIT;
