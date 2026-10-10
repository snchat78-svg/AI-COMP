CREATE TABLE IF NOT EXISTS preparation_test_sessions (
    session_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    preparation_request_id TEXT NOT NULL
        REFERENCES preparation_test_requests(request_id) ON DELETE RESTRICT,
    test_id TEXT NOT NULL,
    specification JSONB NOT NULL CHECK (jsonb_typeof(specification) = 'object'),
    question_snapshot JSONB NOT NULL CHECK (jsonb_typeof(question_snapshot) = 'array'),
    session_state JSONB NOT NULL CHECK (jsonb_typeof(session_state) = 'object'),
    session_status TEXT NOT NULL CHECK (
        session_status IN ('CREATED', 'IN_PROGRESS', 'SUBMITTED', 'EXPIRED', 'CANCELLED')
    ),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CHECK (updated_at >= created_at),
    UNIQUE (learner_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_preparation_test_sessions_learner_history
    ON preparation_test_sessions (learner_id, created_at DESC, session_id DESC);

CREATE INDEX IF NOT EXISTS idx_preparation_test_sessions_request_history
    ON preparation_test_sessions (learner_id, preparation_request_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_preparation_test_sessions_status
    ON preparation_test_sessions (learner_id, session_status, updated_at DESC);
