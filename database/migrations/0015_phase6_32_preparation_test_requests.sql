CREATE TABLE IF NOT EXISTS preparation_test_requests (
    request_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    question_count INTEGER NOT NULL CHECK (question_count BETWEEN 1 AND 500),
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds BETWEEN 1 AND 86400),
    correct_marks DOUBLE PRECISION NOT NULL CHECK (correct_marks > 0),
    incorrect_marks DOUBLE PRECISION NOT NULL CHECK (incorrect_marks <= 0),
    unattempted_marks DOUBLE PRECISION NOT NULL CHECK (unattempted_marks <= 0),
    mode TEXT NOT NULL CHECK (
        mode IN ('ADAPTIVE', 'REVISION', 'WEAK_TOPICS', 'MIXED')
    ),
    concept_ids TEXT[] NOT NULL DEFAULT '{}',
    exclude_question_ids TEXT[] NOT NULL DEFAULT '{}',
    shuffle_questions BOOLEAN NOT NULL DEFAULT FALSE,
    shuffle_seed INTEGER,
    exam_id TEXT,
    subject_id TEXT,
    as_of TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (
        status IN ('ACTIVE', 'SUPERSEDED', 'CANCELLED')
    ),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CHECK (updated_at >= created_at),
    CHECK (NOT shuffle_questions OR shuffle_seed IS NOT NULL),
    CHECK (array_position(concept_ids, NULL) IS NULL),
    CHECK (array_position(exclude_question_ids, NULL) IS NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_preparation_test_requests_one_active_per_learner
    ON preparation_test_requests (learner_id)
    WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_preparation_test_requests_learner_history
    ON preparation_test_requests (learner_id, created_at DESC, request_id DESC);

CREATE INDEX IF NOT EXISTS idx_preparation_test_requests_concepts
    ON preparation_test_requests USING GIN (concept_ids);
