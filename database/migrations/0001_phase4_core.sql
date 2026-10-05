-- Phase 4 PostgreSQL persistence foundation.
-- Requires PostgreSQL with the pgvector extension available.
-- IDs remain text so existing domain IDs can be persisted without re-keying.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS conducting_bodies (
    body_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('STATE', 'NATIONAL')),
    country TEXT NOT NULL DEFAULT 'IN',
    state TEXT,
    official_domains JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS exams (
    exam_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    conducting_body_id TEXT NOT NULL REFERENCES conducting_bodies(body_id),
    level TEXT NOT NULL CHECK (level IN ('STATE', 'NATIONAL')),
    state TEXT,
    categories JSONB NOT NULL DEFAULT '[]'::jsonb,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS paper_categories (
    category_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    exam_id TEXT NOT NULL REFERENCES exams(exam_id),
    description TEXT NOT NULL DEFAULT '',
    allowed_formats JSONB NOT NULL DEFAULT '["pdf","html"]'::jsonb
);

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (
        source_type IN (
            'OFFICIAL_WEBSITE',
            'OFFICIAL_PAPER',
            'OFFICIAL_ANSWER_KEY',
            'TRUSTED_SECONDARY',
            'UNVERIFIED'
        )
    ),
    priority TEXT NOT NULL CHECK (
        priority IN ('OFFICIAL', 'SECONDARY', 'UNVERIFIED')
    ),
    conducting_body_id TEXT REFERENCES conducting_bodies(body_id),
    allowed_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS source_verifications (
    verification_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    source_url TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('VERIFIED', 'SECONDARY_LIKELY', 'UNVERIFIED')
    ),
    evidence_type TEXT NOT NULL CHECK (
        evidence_type IN (
            'OFFICIAL_PAPER',
            'OFFICIAL_ANSWER_KEY',
            'OFFICIAL_ARCHIVE',
            'TRUSTED_SECONDARY',
            'OTHER'
        )
    ),
    checked_at TIMESTAMPTZ NOT NULL,
    confidence DOUBLE PRECISION CHECK (
        confidence IS NULL OR confidence BETWEEN 0.0 AND 1.0
    ),
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS paper_candidates (
    candidate_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    format TEXT NOT NULL DEFAULT 'unknown' CHECK (
        format IN ('pdf', 'html', 'image', 'text', 'unknown')
    ),
    category_id TEXT REFERENCES paper_categories(category_id),
    discovered_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'DISCOVERED' CHECK (
        status IN ('DISCOVERED', 'REJECTED', 'FETCHED', 'FAILED')
    )
);

CREATE TABLE IF NOT EXISTS papers (
    paper_id TEXT PRIMARY KEY,
    candidate_id TEXT UNIQUE REFERENCES paper_candidates(candidate_id),
    title TEXT,
    exam_id TEXT REFERENCES exams(exam_id),
    category_id TEXT REFERENCES paper_categories(category_id),
    source_id TEXT REFERENCES sources(source_id),
    canonical_url TEXT,
    year INTEGER CHECK (year IS NULL OR year >= 1900),
    shift TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    candidate_id TEXT REFERENCES paper_candidates(candidate_id),
    source_url TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT '',
    sha256 CHAR(64) NOT NULL UNIQUE,
    size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
    storage_key TEXT NOT NULL,
    declared_format TEXT NOT NULL DEFAULT 'unknown' CHECK (
        declared_format IN ('pdf', 'html', 'image', 'text', 'unknown')
    ),
    detected_format TEXT NOT NULL DEFAULT 'unknown' CHECK (
        detected_format IN ('pdf', 'html', 'image', 'text', 'unknown')
    ),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS normalized_documents (
    document_id TEXT PRIMARY KEY REFERENCES documents(document_id) ON DELETE CASCADE,
    normalization_version TEXT NOT NULL,
    extraction_method TEXT NOT NULL CHECK (
        extraction_method IN ('DIRECT_TEXT', 'HTML_TEXT', 'PDF_TEXT', 'OCR', 'EMPTY')
    ),
    normalized_text TEXT NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    document_sha256 CHAR(64) NOT NULL,
    question_number INTEGER NOT NULL CHECK (question_number > 0),
    stem TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (
        kind IN ('MCQ', 'TRUE_FALSE', 'UNKNOWN')
    ),
    raw_text TEXT NOT NULL,
    start_line INTEGER NOT NULL CHECK (start_line > 0),
    end_line INTEGER NOT NULL CHECK (end_line >= start_line),
    duplicate_key CHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS question_options (
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    option_key TEXT NOT NULL,
    option_text TEXT NOT NULL,
    option_order INTEGER NOT NULL CHECK (option_order > 0),
    PRIMARY KEY (question_id, option_key),
    UNIQUE (question_id, option_order)
);

CREATE TABLE IF NOT EXISTS concepts (
    concept_id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    subject TEXT,
    topic TEXT,
    subtopic TEXT
);

CREATE TABLE IF NOT EXISTS question_concepts (
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id),
    PRIMARY KEY (question_id, concept_id)
);

CREATE TABLE IF NOT EXISTS question_matches (
    match_id BIGSERIAL PRIMARY KEY,
    left_question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    right_question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    match_type TEXT NOT NULL CHECK (
        match_type IN ('EXACT', 'REPHRASED', 'SAME_CONCEPT', 'RELATED_TOPIC', 'NO_MATCH')
    ),
    confidence DOUBLE PRECISION NOT NULL CHECK (
        confidence BETWEEN 0.0 AND 1.0
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (left_question_id <> right_question_id),
    UNIQUE (left_question_id, right_question_id)
);

CREATE TABLE IF NOT EXISTS match_evidence (
    match_id BIGINT NOT NULL REFERENCES question_matches(match_id) ON DELETE CASCADE,
    evidence_order INTEGER NOT NULL CHECK (evidence_order > 0),
    method TEXT NOT NULL,
    score DOUBLE PRECISION CHECK (
        score IS NULL OR score BETWEEN 0.0 AND 1.0
    ),
    notes TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (match_id, evidence_order)
);

CREATE TABLE IF NOT EXISTS exam_appearances (
    appearance_id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(question_id),
    exam_id TEXT NOT NULL REFERENCES exams(exam_id),
    conducting_body_id TEXT REFERENCES conducting_bodies(body_id),
    year INTEGER NOT NULL CHECK (year >= 1900),
    exam_date DATE,
    shift TEXT,
    question_number INTEGER NOT NULL CHECK (question_number > 0),
    original_question TEXT NOT NULL,
    options JSONB NOT NULL DEFAULT '[]'::jsonb,
    correct_answer TEXT,
    source_url TEXT NOT NULL,
    paper_id TEXT NOT NULL REFERENCES papers(paper_id),
    verification_id TEXT NOT NULL REFERENCES source_verifications(verification_id),
    match_type TEXT NOT NULL DEFAULT 'EXACT' CHECK (
        match_type IN ('EXACT', 'REPHRASED', 'SAME_CONCEPT', 'RELATED_TOPIC', 'NO_MATCH')
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One real exam occurrence must not be counted multiple times because copies
-- were found on different websites. Additional provenance belongs in
-- appearance_sources rather than extra appearance rows.
CREATE UNIQUE INDEX IF NOT EXISTS uq_exam_appearance_identity
    ON exam_appearances (
        exam_id,
        year,
        COALESCE(shift, ''),
        question_number
    );

CREATE TABLE IF NOT EXISTS appearance_sources (
    appearance_id TEXT NOT NULL REFERENCES exam_appearances(appearance_id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    paper_id TEXT REFERENCES papers(paper_id),
    verification_id TEXT REFERENCES source_verifications(verification_id),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (appearance_id, source_url)
);

CREATE TABLE IF NOT EXISTS embedding_models (
    model_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    dimensions INTEGER NOT NULL CHECK (dimensions > 0),
    version TEXT NOT NULL DEFAULT '',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (provider, model_name, version)
);

CREATE TABLE IF NOT EXISTS question_embeddings (
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    model_id TEXT NOT NULL REFERENCES embedding_models(model_id),
    embedding vector NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (question_id, model_id)
);

CREATE INDEX IF NOT EXISTS idx_questions_document
    ON questions(document_id);

CREATE INDEX IF NOT EXISTS idx_questions_duplicate_key
    ON questions(duplicate_key);

CREATE INDEX IF NOT EXISTS idx_question_matches_left
    ON question_matches(left_question_id);

CREATE INDEX IF NOT EXISTS idx_question_matches_right
    ON question_matches(right_question_id);

CREATE INDEX IF NOT EXISTS idx_appearances_question
    ON exam_appearances(question_id);

CREATE INDEX IF NOT EXISTS idx_appearances_exam_year
    ON exam_appearances(exam_id, year);

CREATE INDEX IF NOT EXISTS idx_appearances_verification
    ON exam_appearances(verification_id);

CREATE INDEX IF NOT EXISTS idx_question_embeddings_model
    ON question_embeddings(model_id);

COMMIT;
