-- Phase 6.56 continuation: durable official-unit inventory and independent-review audit.
-- Author-submitted rows always start pending. Only reviewer-protected endpoints may
-- create review evidence or attest the whole syllabus as complete.
BEGIN;

ALTER TABLE exam_concept_applicability
    ADD COLUMN IF NOT EXISTS proposed_status TEXT
        CHECK (proposed_status IS NULL OR proposed_status IN ('IN_SCOPE', 'OUT_OF_SCOPE')),
    ADD COLUMN IF NOT EXISTS authored_by TEXT;

DO $
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_exam_concept_applicability_independent_review'
    ) THEN
        ALTER TABLE exam_concept_applicability
            ADD CONSTRAINT ck_exam_concept_applicability_independent_review
            CHECK (
                authored_by IS NULL OR reviewed_by IS NULL OR authored_by <> reviewed_by
            ) NOT VALID;
    END IF;
END;
$;

CREATE TABLE IF NOT EXISTS exam_syllabus_inventory_units (
    syllabus_id TEXT NOT NULL
        REFERENCES exam_syllabus_documents(syllabus_id) ON DELETE CASCADE,
    unit_id TEXT NOT NULL,
    parent_unit_id TEXT,
    unit_kind TEXT NOT NULL CHECK (
        unit_kind IN ('UNIT', 'TOPIC', 'SUBTOPIC', 'SECTION', 'ANNEX')
    ),
    official_label TEXT NOT NULL CHECK (length(btrim(official_label)) > 0),
    source_locator TEXT NOT NULL CHECK (length(btrim(source_locator)) > 0),
    source_evidence TEXT NOT NULL CHECK (length(btrim(source_evidence)) > 0),
    order_index INTEGER NOT NULL CHECK (order_index >= 0),
    review_status TEXT NOT NULL DEFAULT 'NEEDS_REVIEW' CHECK (
        review_status IN ('NEEDS_REVIEW', 'VERIFIED', 'REJECTED')
    ),
    authored_by TEXT NOT NULL CHECK (length(btrim(authored_by)) > 0),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,
    review_note TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (syllabus_id, unit_id),
    FOREIGN KEY (syllabus_id, parent_unit_id)
        REFERENCES exam_syllabus_inventory_units(syllabus_id, unit_id)
        DEFERRABLE INITIALLY DEFERRED,
    CHECK (parent_unit_id IS NULL OR parent_unit_id <> unit_id),
    CHECK (
        review_status = 'NEEDS_REVIEW'
        OR (
            reviewed_at IS NOT NULL
            AND reviewed_by IS NOT NULL
            AND length(btrim(reviewed_by)) > 0
            AND length(btrim(review_note)) > 0
        )
    ),
    CHECK (reviewed_by IS NULL OR reviewed_by <> authored_by)
);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_inventory_unit_order
    ON exam_syllabus_inventory_units(syllabus_id, order_index, unit_id);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_inventory_review
    ON exam_syllabus_inventory_units(syllabus_id, review_status, unit_id);

CREATE TABLE IF NOT EXISTS exam_syllabus_unit_concepts (
    syllabus_id TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    source_locator TEXT NOT NULL CHECK (length(btrim(source_locator)) > 0),
    source_evidence TEXT NOT NULL CHECK (length(btrim(source_evidence)) > 0),
    review_status TEXT NOT NULL DEFAULT 'NEEDS_REVIEW' CHECK (
        review_status IN ('NEEDS_REVIEW', 'VERIFIED', 'REJECTED')
    ),
    authored_by TEXT NOT NULL CHECK (length(btrim(authored_by)) > 0),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,
    review_note TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (syllabus_id, unit_id, concept_id),
    FOREIGN KEY (syllabus_id, unit_id)
        REFERENCES exam_syllabus_inventory_units(syllabus_id, unit_id) ON DELETE CASCADE,
    CHECK (
        review_status = 'NEEDS_REVIEW'
        OR (
            reviewed_at IS NOT NULL
            AND reviewed_by IS NOT NULL
            AND length(btrim(reviewed_by)) > 0
            AND length(btrim(review_note)) > 0
        )
    ),
    CHECK (reviewed_by IS NULL OR reviewed_by <> authored_by)
);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_unit_concepts_review
    ON exam_syllabus_unit_concepts(syllabus_id, review_status, unit_id, concept_id);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_unit_concepts_concept
    ON exam_syllabus_unit_concepts(syllabus_id, concept_id, review_status);

CREATE TABLE IF NOT EXISTS exam_syllabus_review_audit (
    audit_id TEXT PRIMARY KEY,
    syllabus_id TEXT NOT NULL
        REFERENCES exam_syllabus_documents(syllabus_id) ON DELETE RESTRICT,
    actor_role TEXT NOT NULL CHECK (actor_role IN ('AUTHOR', 'REVIEWER')),
    actor_id TEXT NOT NULL CHECK (length(btrim(actor_id)) > 0),
    action TEXT NOT NULL CHECK (
        action IN (
            'SOURCE_SUBMITTED',
            'INVENTORY_SUBMITTED',
            'CONCEPT_APPLICABILITY_SUBMITTED',
            'UNIT_CONCEPT_MAPPINGS_SUBMITTED',
            'INVENTORY_UNIT_REVIEWED',
            'CONCEPT_APPLICABILITY_REVIEWED',
            'UNIT_CONCEPT_MAPPING_REVIEWED',
            'SYLLABUS_FINALIZED'
        )
    ),
    entity_type TEXT NOT NULL CHECK (
        entity_type IN (
            'SYLLABUS_DOCUMENT',
            'INVENTORY_UNIT',
            'CONCEPT_APPLICABILITY',
            'UNIT_CONCEPT_MAPPING',
            'SYLLABUS_INVENTORY'
        )
    ),
    entity_id TEXT NOT NULL CHECK (length(btrim(entity_id)) > 0),
    decision TEXT NOT NULL CHECK (
        decision IN ('SUBMITTED', 'VERIFIED', 'REJECTED', 'NEEDS_REVIEW', 'IN_SCOPE', 'OUT_OF_SCOPE', 'UNMAPPED')
    ),
    audit_note TEXT NOT NULL CHECK (length(btrim(audit_note)) > 0),
    evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_review_audit_history
    ON exam_syllabus_review_audit(syllabus_id, created_at DESC, audit_id);

-- Reviewer audit evidence is append-only. A correction must be another audit row.
CREATE OR REPLACE FUNCTION ai_comp_reject_exam_syllabus_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'exam_syllabus_review_audit is append-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_audit_no_update ON exam_syllabus_review_audit;
CREATE TRIGGER trg_exam_syllabus_audit_no_update
    BEFORE UPDATE OR DELETE ON exam_syllabus_review_audit
    FOR EACH ROW EXECUTE FUNCTION ai_comp_reject_exam_syllabus_audit_mutation();

COMMIT;
