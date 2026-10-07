BEGIN;

CREATE TABLE IF NOT EXISTS generated_questions (
    generated_question_id TEXT PRIMARY KEY,
    generation_id TEXT NOT NULL,
    material_id TEXT NOT NULL,
    stem TEXT NOT NULL,
    options JSONB NOT NULL,
    correct_option_key TEXT NOT NULL,
    explanation TEXT NOT NULL,
    fact_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    concept_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    difficulty TEXT NOT NULL,
    importance_score DOUBLE PRECISION NOT NULL CHECK (importance_score BETWEEN 0.0 AND 1.0),
    answer_verification_status TEXT NOT NULL CHECK (
        answer_verification_status IN ('VERIFIED', 'REJECTED', 'UNCERTAIN')
    ),
    answer_verification_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL CHECK (status IN ('ACCEPTED', 'REJECTED')),
    quality_score DOUBLE PRECISION NOT NULL CHECK (quality_score BETWEEN 0.0 AND 1.0),
    duplicate_of_master_question_id TEXT NULL
        REFERENCES master_questions(master_question_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generated_questions_material
    ON generated_questions(material_id);

CREATE INDEX IF NOT EXISTS idx_generated_questions_generation
    ON generated_questions(generation_id);

CREATE INDEX IF NOT EXISTS idx_generated_questions_status
    ON generated_questions(status);

COMMIT;
