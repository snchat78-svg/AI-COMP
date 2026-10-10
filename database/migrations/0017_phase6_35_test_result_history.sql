CREATE INDEX IF NOT EXISTS idx_preparation_test_sessions_result_history
    ON preparation_test_sessions (learner_id, updated_at DESC, session_id DESC)
    WHERE session_status IN ('SUBMITTED', 'EXPIRED');
