-- Phase 5.1 master-question identity.
-- A master question is a canonical equivalence class of observed questions.
-- ONLY EXACT/REPHRASED memberships may belong to the class.

BEGIN;

CREATE TABLE IF NOT EXISTS master_questions (
    master_question_id TEXT PRIMARY KEY,
    canonical_question_id TEXT NOT NULL REFERENCES questions(question_id),
    stem TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (
        kind IN ('MCQ', 'TRUE_FALSE', 'UNKNOWN')
    ),
    concept_id TEXT REFERENCES concepts(concept_id),
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (
        status IN ('ACTIVE', 'MERGED', 'RETIRED')
    ),
    merged_into_master_id TEXT REFERENCES master_questions(master_question_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (canonical_question_id),
    CHECK (
        (status = 'MERGED' AND merged_into_master_id IS NOT NULL)
        OR
        (status <> 'MERGED' AND merged_into_master_id IS NULL)
    ),
    CHECK (
        merged_into_master_id IS NULL
        OR merged_into_master_id <> master_question_id
    )
);

CREATE TABLE IF NOT EXISTS master_question_options (
    master_question_id TEXT NOT NULL
        REFERENCES master_questions(master_question_id) ON DELETE CASCADE,
    option_key TEXT NOT NULL,
    option_text TEXT NOT NULL,
    option_order INTEGER NOT NULL CHECK (option_order > 0),
    PRIMARY KEY (master_question_id, option_key),
    UNIQUE (master_question_id, option_order)
);

CREATE TABLE IF NOT EXISTS master_question_memberships (
    master_question_id TEXT NOT NULL
        REFERENCES master_questions(master_question_id) ON DELETE CASCADE,
    question_id TEXT NOT NULL
        REFERENCES questions(question_id) ON DELETE CASCADE,
    relationship TEXT NOT NULL CHECK (
        relationship IN ('CANONICAL', 'EXACT', 'REPHRASED')
    ),
    confidence DOUBLE PRECISION NOT NULL CHECK (
        confidence BETWEEN 0.0 AND 1.0
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (master_question_id, question_id),
    UNIQUE (question_id)
);

CREATE INDEX IF NOT EXISTS idx_master_memberships_master
    ON master_question_memberships(master_question_id);

CREATE INDEX IF NOT EXISTS idx_master_questions_status
    ON master_questions(status);

CREATE INDEX IF NOT EXISTS idx_master_questions_concept
    ON master_questions(concept_id);

COMMIT;
