-- Phase 5.2 controlled master maintenance audit.

BEGIN;

CREATE TABLE IF NOT EXISTS master_merge_events (
    merge_event_id BIGSERIAL PRIMARY KEY,
    source_master_id TEXT NOT NULL REFERENCES master_questions(master_question_id),
    target_master_id TEXT NOT NULL REFERENCES master_questions(master_question_id),
    reason TEXT NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (source_master_id <> target_master_id)
);

CREATE TABLE IF NOT EXISTS master_repair_events (
    repair_event_id BIGSERIAL PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(question_id),
    source_master_id TEXT NOT NULL REFERENCES master_questions(master_question_id),
    target_master_id TEXT NOT NULL REFERENCES master_questions(master_question_id),
    previous_relationship TEXT NOT NULL CHECK (
        previous_relationship IN ('CANONICAL', 'EXACT', 'REPHRASED')
    ),
    new_relationship TEXT NOT NULL CHECK (
        new_relationship IN ('EXACT', 'REPHRASED')
    ),
    previous_confidence DOUBLE PRECISION NOT NULL CHECK (
        previous_confidence BETWEEN 0.0 AND 1.0
    ),
    new_confidence DOUBLE PRECISION NOT NULL CHECK (
        new_confidence BETWEEN 0.0 AND 1.0
    ),
    reason TEXT NOT NULL,
    repaired_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (source_master_id <> target_master_id)
);

CREATE INDEX IF NOT EXISTS idx_master_merge_source
    ON master_merge_events(source_master_id);

CREATE INDEX IF NOT EXISTS idx_master_merge_target
    ON master_merge_events(target_master_id);

CREATE INDEX IF NOT EXISTS idx_master_repair_question
    ON master_repair_events(question_id);

COMMIT;