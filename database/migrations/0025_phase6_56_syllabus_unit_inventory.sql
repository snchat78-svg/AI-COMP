-- Phase 6.56: persist a reviewable, hierarchical inventory of every official syllabus unit/topic/subtopic.
BEGIN;

ALTER TABLE exam_syllabus_review_audit
    DROP CONSTRAINT IF EXISTS exam_syllabus_review_audit_entity_type_check;
ALTER TABLE exam_syllabus_review_audit
    ADD CONSTRAINT exam_syllabus_review_audit_entity_type_check
    CHECK (entity_type IN ('SOURCE', 'CONCEPT_MAPPING', 'SYLLABUS_UNIT'));

CREATE TABLE IF NOT EXISTS exam_syllabus_units (
    syllabus_id TEXT NOT NULL REFERENCES exam_syllabus_documents(syllabus_id) ON DELETE RESTRICT,
    unit_id TEXT NOT NULL,
    parent_unit_id TEXT,
    unit_kind TEXT NOT NULL CHECK (unit_kind IN ('UNIT', 'TOPIC', 'SUBTOPIC')),
    official_label TEXT NOT NULL CHECK (btrim(official_label) <> ''),
    page_number INTEGER CHECK (page_number IS NULL OR page_number BETWEEN 1 AND 10000),
    source_locator TEXT NOT NULL CHECK (btrim(source_locator) <> ''),
    source_evidence TEXT NOT NULL CHECK (btrim(source_evidence) <> ''),
    review_status TEXT NOT NULL DEFAULT 'NEEDS_REVIEW'
        CHECK (review_status IN ('NEEDS_REVIEW', 'VERIFIED', 'REJECTED')),
    created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,
    review_note TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (syllabus_id, unit_id),
    FOREIGN KEY (syllabus_id, parent_unit_id)
        REFERENCES exam_syllabus_units(syllabus_id, unit_id) ON DELETE RESTRICT,
    CHECK (parent_unit_id IS NULL OR parent_unit_id <> unit_id),
    CHECK (
        review_status <> 'VERIFIED'
        OR (
            reviewed_at IS NOT NULL
            AND reviewed_by IS NOT NULL
            AND btrim(reviewed_by) <> ''
            AND btrim(review_note) <> ''
        )
    ),
    CHECK (
        (unit_kind = 'UNIT' AND parent_unit_id IS NULL)
        OR (unit_kind IN ('TOPIC', 'SUBTOPIC') AND parent_unit_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_units_review
    ON exam_syllabus_units (syllabus_id, review_status, unit_kind, unit_id);

-- A complete inventory is an attestation backed by concrete reviewed rows, not a free-form checkbox.
CREATE OR REPLACE FUNCTION enforce_exam_syllabus_inventory_rows()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    target_syllabus_id TEXT;
    unit_total BIGINT;
    pending_total BIGINT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        target_syllabus_id := OLD.syllabus_id;
    ELSE
        target_syllabus_id := NEW.syllabus_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM exam_syllabus_documents AS d
        WHERE d.syllabus_id = target_syllabus_id
          AND d.syllabus_inventory_complete = TRUE
    ) THEN
        RAISE EXCEPTION 'syllabus inventory is locked while marked complete; reopen source review first';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_units_inventory_lock ON exam_syllabus_units;
CREATE TRIGGER trg_exam_syllabus_units_inventory_lock
BEFORE INSERT OR UPDATE OR DELETE ON exam_syllabus_units
FOR EACH ROW EXECUTE FUNCTION enforce_exam_syllabus_inventory_rows();

CREATE OR REPLACE FUNCTION enforce_exam_syllabus_inventory_attestation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    unit_total BIGINT;
    pending_total BIGINT;
BEGIN
    IF NEW.syllabus_inventory_complete = TRUE THEN
        SELECT COUNT(*), COUNT(*) FILTER (WHERE review_status <> 'VERIFIED')
          INTO unit_total, pending_total
        FROM exam_syllabus_units
        WHERE syllabus_id = NEW.syllabus_id;

        IF unit_total = 0 OR pending_total <> 0 THEN
            RAISE EXCEPTION 'syllabus inventory cannot be complete until at least one unit exists and every unit is VERIFIED';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_inventory_attestation ON exam_syllabus_documents;
CREATE TRIGGER trg_exam_syllabus_inventory_attestation
BEFORE INSERT OR UPDATE OF syllabus_inventory_complete ON exam_syllabus_documents
FOR EACH ROW EXECUTE FUNCTION enforce_exam_syllabus_inventory_attestation();

COMMIT;
