-- Phase 6.56 follow-up: protected author/reviewer workflow and append-only audit.
BEGIN;

CREATE TABLE IF NOT EXISTS exam_syllabus_review_audit (
    audit_id TEXT PRIMARY KEY,
    syllabus_id TEXT NOT NULL REFERENCES exam_syllabus_documents(syllabus_id) ON DELETE RESTRICT,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('SOURCE', 'CONCEPT_MAPPING')),
    entity_id TEXT NOT NULL,
    actor_role TEXT NOT NULL CHECK (actor_role IN ('AUTHOR', 'REVIEWER')),
    actor_id TEXT NOT NULL CHECK (btrim(actor_id) <> ''),
    decision TEXT NOT NULL,
    review_note TEXT NOT NULL CHECK (btrim(review_note) <> ''),
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_review_audit_entity
    ON exam_syllabus_review_audit (syllabus_id, entity_type, entity_id, created_at);

-- Audit events are append-only at the database permission/trigger layer.
CREATE OR REPLACE FUNCTION prevent_exam_syllabus_audit_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'exam syllabus review audit is append-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_audit_no_update ON exam_syllabus_review_audit;
CREATE TRIGGER trg_exam_syllabus_audit_no_update
BEFORE UPDATE OR DELETE ON exam_syllabus_review_audit
FOR EACH ROW EXECUTE FUNCTION prevent_exam_syllabus_audit_mutation();

COMMIT;
