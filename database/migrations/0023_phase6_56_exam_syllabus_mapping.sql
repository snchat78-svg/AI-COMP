-- Phase 6.56: persist exam-specific official syllabus evidence and concept applicability.
-- No exam profile is seeded until its exact official notification/syllabus is confirmed.
BEGIN;

CREATE TABLE IF NOT EXISTS exam_syllabus_documents (
    syllabus_id TEXT PRIMARY KEY,
    exam_id TEXT NOT NULL REFERENCES exams(exam_id) ON DELETE CASCADE,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    source_title TEXT NOT NULL,
    source_url TEXT NOT NULL CHECK (source_url LIKE 'https://%'),
    notification_number TEXT NOT NULL DEFAULT '',
    version_label TEXT NOT NULL,
    source_status TEXT NOT NULL DEFAULT 'REVIEW_PENDING' CHECK (
        source_status IN ('DISCOVERED', 'REVIEW_PENDING', 'VERIFIED', 'SUPERSEDED', 'REJECTED')
    ),
    source_evidence TEXT NOT NULL DEFAULT '',
    document_sha256 CHAR(64),
    syllabus_inventory_complete BOOLEAN NOT NULL DEFAULT FALSE,
    inventory_reviewed_at TIMESTAMPTZ,
    inventory_reviewed_by TEXT,
    inventory_review_note TEXT NOT NULL DEFAULT '',
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    published_on DATE,
    effective_from DATE,
    effective_to DATE,
    source_checked_at TIMESTAMPTZ,
    source_checked_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (document_sha256 IS NULL OR document_sha256 ~ '^[0-9a-f]{64}$'),
    CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from),
    CHECK (
        source_status <> 'VERIFIED'
        OR (
            source_checked_at IS NOT NULL
            AND source_checked_by IS NOT NULL
            AND btrim(source_checked_by) <> ''
            AND document_sha256 IS NOT NULL
            AND btrim(source_evidence) <> ''
            AND syllabus_inventory_complete = TRUE
            AND inventory_reviewed_at IS NOT NULL
            AND inventory_reviewed_by IS NOT NULL
            AND btrim(inventory_reviewed_by) <> ''
            AND btrim(inventory_review_note) <> ''
        )
    ),
    CHECK (
        NOT syllabus_inventory_complete
        OR (
            source_status = 'VERIFIED'
            AND inventory_reviewed_at IS NOT NULL
            AND inventory_reviewed_by IS NOT NULL
            AND btrim(inventory_reviewed_by) <> ''
            AND btrim(inventory_review_note) <> ''
        )
    ),
    UNIQUE (exam_id, source_url)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_exam_syllabus_current_version
    ON exam_syllabus_documents (exam_id)
    WHERE is_current = TRUE;

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_status
    ON exam_syllabus_documents (exam_id, source_status, is_current);

CREATE TABLE IF NOT EXISTS exam_concept_applicability (
    syllabus_id TEXT NOT NULL REFERENCES exam_syllabus_documents(syllabus_id) ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON DELETE CASCADE,
    applicability_status TEXT NOT NULL DEFAULT 'NEEDS_REVIEW' CHECK (
        applicability_status IN ('IN_SCOPE', 'OUT_OF_SCOPE', 'UNMAPPED', 'NEEDS_REVIEW')
    ),
    official_unit TEXT NOT NULL DEFAULT '',
    source_locator TEXT NOT NULL DEFAULT '',
    source_evidence TEXT NOT NULL DEFAULT '',
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,
    review_note TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (syllabus_id, concept_id),
    CHECK (
        applicability_status NOT IN ('IN_SCOPE', 'OUT_OF_SCOPE')
        OR (
            reviewed_at IS NOT NULL
            AND reviewed_by IS NOT NULL
            AND btrim(reviewed_by) <> ''
            AND btrim(source_locator) <> ''
            AND btrim(source_evidence) <> ''
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_exam_concept_applicability_status
    ON exam_concept_applicability (syllabus_id, applicability_status, concept_id);

-- Deliberately do not seed an exam profile: no current official notification/syllabus version
-- has been independently established for this mapping slice. Add profile/source rows only
-- after confirming the exact official advertisement and source lineage.

COMMIT;
