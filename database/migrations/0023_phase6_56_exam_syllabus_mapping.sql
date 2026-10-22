-- Phase 6.56: persist exam-specific official syllabus evidence and concept applicability.
-- New profiles deliberately remain unverified until the official document is checked.
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

-- Seed only the discovered profile and source pointer. The notification's official
-- PDF contents/hash have not yet been checked by an independent reviewer, so no
-- concept is marked IN_SCOPE and no topic is selectable for this profile.
INSERT INTO conducting_bodies (
    body_id, name, level, country, state, official_domains
)
VALUES (
    'RSSB',
    'Rajasthan Staff Selection Board',
    'STATE',
    'IN',
    'Rajasthan',
    '["rssb.rajasthan.gov.in","rsmssb.rajasthan.gov.in"]'::jsonb
)
ON CONFLICT (body_id) DO NOTHING;

INSERT INTO sources (
    source_id, name, base_url, source_type, priority,
    conducting_body_id, allowed_paths, notes
)
VALUES (
    'RSSB_CET_GRADUATION_2026_NOTICE',
    'RSSB CET Graduation Level 2026 advertisement / syllabus',
    'https://rssb.rajasthan.gov.in',
    'OFFICIAL_WEBSITE',
    'OFFICIAL',
    'RSSB',
    '["/storage/advertisement_item/1782966142.pdf"]'::jsonb,
    'PDF location discovered for Advertisement 09/2026. Keep syllabus status REVIEW_PENDING until the official document is fetched, its content and SHA-256 are checked, and an independent reviewer records evidence.'
)
ON CONFLICT (source_id) DO NOTHING;

INSERT INTO exams (
    exam_id, name, conducting_body_id, level, state, categories, active
)
VALUES (
    'RSSB_CET_GRADUATION_2026',
    'Rajasthan Common Eligibility Test (Graduation Level) 2026',
    'RSSB',
    'STATE',
    'Rajasthan',
    '["CET_GRADUATION"]'::jsonb,
    TRUE
)
ON CONFLICT (exam_id) DO NOTHING;

INSERT INTO exam_syllabus_documents (
    syllabus_id, exam_id, source_id, source_title, source_url,
    notification_number, version_label, source_status, source_evidence,
    is_current, published_on
)
VALUES (
    'RSSB_CET_GRADUATION_2026_ADVT_09_2026',
    'RSSB_CET_GRADUATION_2026',
    'RSSB_CET_GRADUATION_2026_NOTICE',
    'Common Eligibility Test (Graduation Level) 2026 — Advertisement 09/2026, syllabus clause',
    'https://rssb.rajasthan.gov.in/storage/advertisement_item/1782966142.pdf',
    'Advertisement No. 09/2026',
    'Advt 09/2026 — syllabus document review pending',
    'REVIEW_PENDING',
    'The official-host PDF URL is identified, but its content and SHA-256 have not yet been independently checked in this phase. Do not infer applicability from the URL or secondary summaries.',
    TRUE,
    NULL
)
ON CONFLICT (exam_id, source_url) DO NOTHING;

COMMIT;
