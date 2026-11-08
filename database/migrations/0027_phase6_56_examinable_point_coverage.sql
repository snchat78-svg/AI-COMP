-- Phase 6.56: independently reviewable examinable points, dimensions and One-Liner links.
BEGIN;

ALTER TABLE exam_syllabus_review_audit
    DROP CONSTRAINT IF EXISTS exam_syllabus_review_audit_entity_type_check;
ALTER TABLE exam_syllabus_review_audit
    ADD CONSTRAINT exam_syllabus_review_audit_entity_type_check
    CHECK (entity_type IN (
        'SOURCE', 'CONCEPT_MAPPING', 'SYLLABUS_UNIT', 'SOURCE_FETCH',
        'EXAMINABLE_POINT', 'POINT_CONCEPT', 'POINT_DIMENSION', 'POINT_LEARNING_ITEM'
    ));

ALTER TABLE exam_syllabus_documents
    ADD COLUMN IF NOT EXISTS examinable_points_inventory_complete BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS examinable_points_reviewed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS examinable_points_reviewed_by TEXT,
    ADD COLUMN IF NOT EXISTS examinable_points_review_note TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS exam_syllabus_examinable_points (
    syllabus_id TEXT NOT NULL REFERENCES exam_syllabus_documents(syllabus_id) ON DELETE RESTRICT,
    point_id TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    point_type TEXT NOT NULL CHECK (point_type IN (
        'FACT', 'DEFINITION', 'FORMULA', 'PROCESS', 'COMPARISON',
        'CLASSIFICATION', 'LOCATION', 'DIAGRAM', 'EXCEPTION',
        'NUMERICAL_SKILL', 'OTHER'
    )),
    point_statement TEXT NOT NULL CHECK (btrim(point_statement) <> ''),
    page_number INTEGER CHECK (page_number IS NULL OR page_number BETWEEN 1 AND 10000),
    source_locator TEXT NOT NULL CHECK (btrim(source_locator) <> ''),
    source_evidence TEXT NOT NULL CHECK (btrim(source_evidence) <> ''),
    mapping_status TEXT NOT NULL DEFAULT 'NEEDS_REVIEW'
        CHECK (mapping_status IN ('NEEDS_REVIEW', 'MAPPED', 'MAPPING_GAP')),
    mapping_gap_reason TEXT NOT NULL DEFAULT '',
    review_status TEXT NOT NULL DEFAULT 'NEEDS_REVIEW'
        CHECK (review_status IN ('NEEDS_REVIEW', 'VERIFIED', 'REJECTED')),
    created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,
    review_note TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (syllabus_id, point_id),
    FOREIGN KEY (syllabus_id, unit_id)
        REFERENCES exam_syllabus_units(syllabus_id, unit_id) ON DELETE RESTRICT,
    CHECK (mapping_status <> 'MAPPING_GAP' OR btrim(mapping_gap_reason) <> ''),
    CHECK (
        review_status <> 'VERIFIED'
        OR (reviewed_at IS NOT NULL AND reviewed_by IS NOT NULL
            AND btrim(reviewed_by) <> '' AND btrim(review_note) <> '')
    )
);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_points_unit_review
    ON exam_syllabus_examinable_points (syllabus_id, unit_id, review_status, point_id);

CREATE TABLE IF NOT EXISTS exam_syllabus_point_concepts (
    syllabus_id TEXT NOT NULL,
    point_id TEXT NOT NULL,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE RESTRICT,
    created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    review_status TEXT NOT NULL DEFAULT 'NEEDS_REVIEW'
        CHECK (review_status IN ('NEEDS_REVIEW', 'VERIFIED', 'REJECTED')),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,
    review_note TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (syllabus_id, point_id, concept_id),
    FOREIGN KEY (syllabus_id, point_id)
        REFERENCES exam_syllabus_examinable_points(syllabus_id, point_id) ON DELETE RESTRICT,
    CHECK (
        review_status <> 'VERIFIED'
        OR (reviewed_at IS NOT NULL AND reviewed_by IS NOT NULL
            AND btrim(reviewed_by) <> '' AND btrim(review_note) <> '')
    )
);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_point_concepts_review
    ON exam_syllabus_point_concepts (syllabus_id, point_id, review_status);

CREATE TABLE IF NOT EXISTS exam_syllabus_point_dimensions (
    syllabus_id TEXT NOT NULL,
    point_id TEXT NOT NULL,
    dimension_key TEXT NOT NULL CHECK (dimension_key IN (
        'PRESENCE', 'CORRECTNESS', 'ATOMICITY', 'RECALL_DEPTH',
        'APPLICATION', 'DISCRIMINATION', 'LANGUAGE', 'PROVENANCE', 'DUPLICATION'
    )),
    assessment TEXT NOT NULL CHECK (assessment IN ('APPLICABLE', 'NOT_APPLICABLE', 'GAP')),
    assessment_reason TEXT NOT NULL DEFAULT '',
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assessed_by TEXT NOT NULL CHECK (btrim(assessed_by) <> ''),
    PRIMARY KEY (syllabus_id, point_id, dimension_key),
    FOREIGN KEY (syllabus_id, point_id)
        REFERENCES exam_syllabus_examinable_points(syllabus_id, point_id) ON DELETE RESTRICT,
    CHECK (assessment <> 'NOT_APPLICABLE' OR btrim(assessment_reason) <> ''),
    CHECK (assessment <> 'GAP' OR btrim(assessment_reason) <> ''),
    CHECK (dimension_key <> 'PRESENCE' OR assessment <> 'NOT_APPLICABLE')
);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_point_dimensions_assessment
    ON exam_syllabus_point_dimensions (syllabus_id, assessment, dimension_key);

CREATE TABLE IF NOT EXISTS exam_syllabus_point_one_liner_links (
    syllabus_id TEXT NOT NULL,
    point_id TEXT NOT NULL,
    one_liner_id TEXT NOT NULL REFERENCES question_bank_one_liners(one_liner_id) ON DELETE RESTRICT,
    created_by TEXT NOT NULL CHECK (btrim(created_by) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    review_status TEXT NOT NULL DEFAULT 'NEEDS_REVIEW'
        CHECK (review_status IN ('NEEDS_REVIEW', 'VERIFIED', 'REJECTED')),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,
    review_note TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (syllabus_id, point_id, one_liner_id),
    FOREIGN KEY (syllabus_id, point_id)
        REFERENCES exam_syllabus_examinable_points(syllabus_id, point_id) ON DELETE RESTRICT,
    CHECK (
        review_status <> 'VERIFIED'
        OR (reviewed_at IS NOT NULL AND reviewed_by IS NOT NULL
            AND btrim(reviewed_by) <> '' AND btrim(review_note) <> '')
    )
);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_point_one_liners_review
    ON exam_syllabus_point_one_liner_links (syllabus_id, point_id, review_status);

CREATE OR REPLACE FUNCTION enforce_exam_syllabus_examinable_point_inventory()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    target_syllabus_id TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        target_syllabus_id := OLD.syllabus_id;
    ELSE
        target_syllabus_id := NEW.syllabus_id;
    END IF;

    IF EXISTS (
        SELECT 1 FROM exam_syllabus_documents
        WHERE syllabus_id = target_syllabus_id
          AND examinable_points_inventory_complete = TRUE
    ) THEN
        RAISE EXCEPTION 'examinable-point inventory is locked while attested complete';
    END IF;

    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_points_inventory_lock ON exam_syllabus_examinable_points;
CREATE TRIGGER trg_exam_syllabus_points_inventory_lock
BEFORE INSERT OR UPDATE OR DELETE ON exam_syllabus_examinable_points
FOR EACH ROW EXECUTE FUNCTION enforce_exam_syllabus_examinable_point_inventory();

CREATE OR REPLACE FUNCTION enforce_exam_syllabus_point_inventory_attestation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    point_total BIGINT;
    unresolved_points BIGINT;
    unresolved_mappings BIGINT;
    incomplete_dimensions BIGINT;
BEGIN
    IF NEW.examinable_points_inventory_complete = TRUE THEN
        IF NEW.source_status <> 'VERIFIED' OR NEW.syllabus_inventory_complete <> TRUE THEN
            RAISE EXCEPTION 'official source and unit/topic/subtopic inventory must be verified first';
        END IF;

        SELECT COUNT(*),
               COUNT(*) FILTER (WHERE review_status <> 'VERIFIED')
          INTO point_total, unresolved_points
        FROM exam_syllabus_examinable_points
        WHERE syllabus_id = NEW.syllabus_id;

        SELECT COUNT(*)
          INTO unresolved_mappings
        FROM exam_syllabus_point_concepts AS pc
        JOIN exam_syllabus_examinable_points AS p
          ON p.syllabus_id = pc.syllabus_id AND p.point_id = pc.point_id
        WHERE p.syllabus_id = NEW.syllabus_id
          AND pc.review_status <> 'VERIFIED';

        IF EXISTS (
            SELECT 1 FROM exam_syllabus_examinable_points
            WHERE syllabus_id = NEW.syllabus_id AND created_by = NEW.examinable_points_reviewed_by
        ) THEN
            RAISE EXCEPTION 'point author cannot attest the examinable-point inventory';
        END IF;

        SELECT COUNT(*)
          INTO incomplete_dimensions
        FROM exam_syllabus_examinable_points AS p
        WHERE p.syllabus_id = NEW.syllabus_id
          AND (
              (SELECT COUNT(*) FROM exam_syllabus_point_dimensions AS d
               WHERE d.syllabus_id = p.syllabus_id AND d.point_id = p.point_id) <> 9
              OR EXISTS (
                  SELECT 1 FROM exam_syllabus_point_dimensions AS d
                  WHERE d.syllabus_id = p.syllabus_id AND d.point_id = p.point_id
                    AND d.assessment = 'GAP'
              )
              OR p.mapping_status <> 'MAPPED'
              OR NOT EXISTS (
                  SELECT 1 FROM exam_syllabus_point_concepts AS pc
                  WHERE pc.syllabus_id = p.syllabus_id AND pc.point_id = p.point_id
                    AND pc.review_status = 'VERIFIED'
              )
          );

        IF point_total = 0 OR unresolved_points <> 0 OR unresolved_mappings <> 0
           OR incomplete_dimensions <> 0 THEN
            RAISE EXCEPTION 'examinable-point inventory cannot be complete with pending points, mapping gaps or missing dimension reviews';
        END IF;
        IF NEW.examinable_points_reviewed_at IS NULL
           OR NEW.examinable_points_reviewed_by IS NULL
           OR btrim(NEW.examinable_points_reviewed_by) = ''
           OR btrim(NEW.examinable_points_review_note) = '' THEN
            RAISE EXCEPTION 'examinable-point inventory attestation requires reviewer identity, timestamp and note';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_point_inventory_attestation ON exam_syllabus_documents;
CREATE TRIGGER trg_exam_syllabus_point_inventory_attestation
BEFORE INSERT OR UPDATE OF examinable_points_inventory_complete ON exam_syllabus_documents
FOR EACH ROW EXECUTE FUNCTION enforce_exam_syllabus_point_inventory_attestation();


CREATE OR REPLACE FUNCTION enforce_exam_syllabus_point_review_separation()
RETURNS TRIGGER LANGUAGE plpgsql AS $
BEGIN
    IF NEW.review_status = 'VERIFIED'
       AND (NEW.reviewed_by IS NULL OR NEW.reviewed_by = NEW.created_by) THEN
        RAISE EXCEPTION 'examinable point author cannot independently verify the point';
    END IF;
    RETURN NEW;
END;
$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_point_review_separation ON exam_syllabus_examinable_points;
CREATE TRIGGER trg_exam_syllabus_point_review_separation
BEFORE INSERT OR UPDATE OF review_status, reviewed_by ON exam_syllabus_examinable_points
FOR EACH ROW EXECUTE FUNCTION enforce_exam_syllabus_point_review_separation();

CREATE OR REPLACE FUNCTION enforce_exam_syllabus_point_concept_review_separation()
RETURNS TRIGGER LANGUAGE plpgsql AS $
DECLARE
    point_author TEXT;
BEGIN
    IF NEW.review_status = 'VERIFIED' THEN
        SELECT created_by INTO point_author
        FROM exam_syllabus_examinable_points
        WHERE syllabus_id = NEW.syllabus_id AND point_id = NEW.point_id;
        IF point_author IS NULL OR NEW.reviewed_by IS NULL
           OR NEW.reviewed_by = NEW.created_by OR NEW.reviewed_by = point_author THEN
            RAISE EXCEPTION 'point and mapping authors cannot independently verify a concept mapping';
        END IF;
    END IF;
    RETURN NEW;
END;
$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_point_concept_review_separation ON exam_syllabus_point_concepts;
CREATE TRIGGER trg_exam_syllabus_point_concept_review_separation
BEFORE INSERT OR UPDATE OF review_status, reviewed_by ON exam_syllabus_point_concepts
FOR EACH ROW EXECUTE FUNCTION enforce_exam_syllabus_point_concept_review_separation();

CREATE OR REPLACE FUNCTION enforce_exam_syllabus_point_dimension_review_separation()
RETURNS TRIGGER LANGUAGE plpgsql AS $
DECLARE
    point_author TEXT;
BEGIN
    SELECT created_by INTO point_author
    FROM exam_syllabus_examinable_points
    WHERE syllabus_id = NEW.syllabus_id AND point_id = NEW.point_id;
    IF point_author IS NULL OR NEW.assessed_by = point_author THEN
        RAISE EXCEPTION 'point author cannot independently assess coverage dimensions';
    END IF;
    RETURN NEW;
END;
$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_point_dimension_review_separation ON exam_syllabus_point_dimensions;
CREATE TRIGGER trg_exam_syllabus_point_dimension_review_separation
BEFORE INSERT OR UPDATE OF assessed_by ON exam_syllabus_point_dimensions
FOR EACH ROW EXECUTE FUNCTION enforce_exam_syllabus_point_dimension_review_separation();

CREATE OR REPLACE FUNCTION enforce_exam_syllabus_point_one_liner_verification()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.review_status = 'VERIFIED' THEN
        IF NEW.reviewed_by IS NULL OR NEW.reviewed_by = NEW.created_by THEN
            RAISE EXCEPTION 'learning-item link author cannot independently verify the link';
        END IF;
        IF NOT EXISTS (
            SELECT 1
            FROM question_bank_one_liners AS ol
            JOIN exam_syllabus_point_concepts AS pc
              ON pc.concept_id = ol.concept_id
             AND pc.syllabus_id = NEW.syllabus_id
             AND pc.point_id = NEW.point_id
             AND pc.review_status = 'VERIFIED'
            WHERE ol.one_liner_id = NEW.one_liner_id
              AND ol.verification_status = 'VERIFIED'
        ) THEN
            RAISE EXCEPTION 'a point learning link requires an independently verified one-liner mapped to the same point';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_point_one_liner_verified ON exam_syllabus_point_one_liner_links;
CREATE TRIGGER trg_exam_syllabus_point_one_liner_verified
BEFORE INSERT OR UPDATE OF review_status ON exam_syllabus_point_one_liner_links
FOR EACH ROW EXECUTE FUNCTION enforce_exam_syllabus_point_one_liner_verification();

CREATE OR REPLACE FUNCTION prevent_exam_syllabus_point_review_audit_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'examinable-point review evidence is append-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_point_audit_no_update ON exam_syllabus_review_audit;
-- The audit table already has append-only UPDATE/DELETE/TRUNCATE guards from 0024.
-- This additional function documents the point-review event policy without replacing those guards.


CREATE OR REPLACE FUNCTION enforce_exam_syllabus_point_child_inventory_lock()
RETURNS TRIGGER LANGUAGE plpgsql AS $
DECLARE
    target_syllabus_id TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN target_syllabus_id := OLD.syllabus_id;
    ELSE target_syllabus_id := NEW.syllabus_id; END IF;
    IF EXISTS (
        SELECT 1 FROM exam_syllabus_documents
        WHERE syllabus_id = target_syllabus_id
          AND examinable_points_inventory_complete = TRUE
    ) THEN
        RAISE EXCEPTION 'examinable-point mappings and dimensions are locked while attested complete';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_point_concepts_inventory_lock ON exam_syllabus_point_concepts;
CREATE TRIGGER trg_exam_syllabus_point_concepts_inventory_lock
BEFORE INSERT OR UPDATE OR DELETE ON exam_syllabus_point_concepts
FOR EACH ROW EXECUTE FUNCTION enforce_exam_syllabus_point_child_inventory_lock();

DROP TRIGGER IF EXISTS trg_exam_syllabus_point_dimensions_inventory_lock ON exam_syllabus_point_dimensions;
CREATE TRIGGER trg_exam_syllabus_point_dimensions_inventory_lock
BEFORE INSERT OR UPDATE OR DELETE ON exam_syllabus_point_dimensions
FOR EACH ROW EXECUTE FUNCTION enforce_exam_syllabus_point_child_inventory_lock();

COMMIT;
