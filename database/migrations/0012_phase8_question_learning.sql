CREATE TABLE IF NOT EXISTS learner_question_attempts (
    outcome_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL
        REFERENCES learner_test_attempts(attempt_id)
        ON DELETE CASCADE,
    learner_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    concept_ids TEXT[] NOT NULL,
    difficulty TEXT NOT NULL,
    selected_option_key TEXT,
    correct_option_key TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('CORRECT', 'INCORRECT', 'UNATTEMPTED')),
    completed_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_learner_question_attempt UNIQUE (learner_id, session_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_learner_question_learner_question
    ON learner_question_attempts(learner_id, question_id, completed_at);

CREATE INDEX IF NOT EXISTS idx_learner_question_concepts
    ON learner_question_attempts USING GIN (concept_ids);

CREATE INDEX IF NOT EXISTS idx_learner_question_outcome
    ON learner_question_attempts(learner_id, outcome, completed_at);
