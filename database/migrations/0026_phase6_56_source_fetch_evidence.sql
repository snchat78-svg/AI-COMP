-- Phase 6.56: immutable evidence of the exact official PDF fetched by the server.
BEGIN;

ALTER TABLE exam_syllabus_review_audit
    DROP CONSTRAINT IF EXISTS exam_syllabus_review_audit_entity_type_check;
ALTER TABLE exam_syllabus_review_audit
    ADD CONSTRAINT exam_syllabus_review_audit_entity_type_check
    CHECK (entity_type IN ('SOURCE', 'CONCEPT_MAPPING', 'SYLLABUS_UNIT', 'SOURCE_FETCH'));

CREATE TABLE IF NOT EXISTS exam_syllabus_source_fetches (
    fetch_id TEXT PRIMARY KEY,
    syllabus_id TEXT NOT NULL REFERENCES exam_syllabus_documents(syllabus_id) ON DELETE RESTRICT,
    requested_url TEXT NOT NULL CHECK (requested_url LIKE 'https://%'),
    final_url TEXT CHECK (final_url IS NULL OR final_url LIKE 'https://%'),
    fetch_status TEXT NOT NULL CHECK (fetch_status IN ('FETCHED', 'FAILED')),
    failure_code TEXT NOT NULL DEFAULT '',
    content_type TEXT NOT NULL DEFAULT '',
    byte_length BIGINT,
    page_count INTEGER,
    document_title TEXT NOT NULL DEFAULT '',
    document_sha256 CHAR(64),
    document_bytes BYTEA,
    fetched_by TEXT NOT NULL CHECK (btrim(fetched_by) <> ''),
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
      (fetch_status = 'FETCHED'
       AND final_url IS NOT NULL
       AND byte_length IS NOT NULL AND byte_length > 0
       AND page_count IS NOT NULL AND page_count BETWEEN 1 AND 500
       AND content_type = 'application/pdf'
       AND document_sha256 IS NOT NULL AND document_sha256 ~ '^[0-9a-f]{64}$'
       AND document_bytes IS NOT NULL
       AND octet_length(document_bytes) = byte_length
       AND btrim(failure_code) = '')
      OR
      (fetch_status = 'FAILED'
       AND byte_length IS NULL AND page_count IS NULL
       AND document_sha256 IS NULL AND document_bytes IS NULL
       AND btrim(failure_code) <> '')
    )
);

CREATE INDEX IF NOT EXISTS idx_exam_syllabus_fetch_latest
    ON exam_syllabus_source_fetches (syllabus_id, fetch_status, fetched_at DESC);

CREATE OR REPLACE FUNCTION prevent_exam_syllabus_fetch_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'exam syllabus source fetch evidence is immutable';
END;
$$;

DROP TRIGGER IF EXISTS trg_exam_syllabus_fetch_no_update_delete ON exam_syllabus_source_fetches;
CREATE TRIGGER trg_exam_syllabus_fetch_no_update_delete
BEFORE UPDATE OR DELETE ON exam_syllabus_source_fetches
FOR EACH ROW EXECUTE FUNCTION prevent_exam_syllabus_fetch_mutation();

DROP TRIGGER IF EXISTS trg_exam_syllabus_fetch_no_truncate ON exam_syllabus_source_fetches;
CREATE TRIGGER trg_exam_syllabus_fetch_no_truncate
BEFORE TRUNCATE ON exam_syllabus_source_fetches
FOR EACH STATEMENT EXECUTE FUNCTION prevent_exam_syllabus_fetch_mutation();

COMMIT;
