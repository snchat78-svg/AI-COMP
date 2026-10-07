-- Phase 6.4 verified material-to-exam matching results.
-- Only matches against verified active master questions are persisted.

BEGIN;

CREATE TABLE IF NOT EXISTS material_question_matches (
    material_id TEXT NOT NULL,
    probe_id TEXT NOT NULL,
    probe_type TEXT NOT NULL CHECK (
        probe_type IN ('QUESTION_TEXT', 'CONCEPT')
    ),
    master_question_id TEXT NOT NULL
        REFERENCES master_questions(master_question_id),
    match_type TEXT NOT NULL CHECK (
        match_type IN ('EXACT', 'REPHRASED', 'SAME_CONCEPT', 'RELATED_TOPIC')
    ),
    confidence DOUBLE PRECISION NOT NULL CHECK (
        confidence BETWEEN 0.0 AND 1.0
    ),
    verified_appearance_count INTEGER NOT NULL CHECK (
        verified_appearance_count > 0
    ),
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (material_id, probe_id, master_question_id, match_type)
);

CREATE INDEX IF NOT EXISTS idx_material_matches_material
    ON material_question_matches(material_id);

CREATE INDEX IF NOT EXISTS idx_material_matches_master
    ON material_question_matches(master_question_id);

CREATE INDEX IF NOT EXISTS idx_material_matches_type
    ON material_question_matches(match_type);

COMMIT;
