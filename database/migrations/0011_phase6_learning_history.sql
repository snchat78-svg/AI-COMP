CREATE TABLE IF NOT EXISTS learner_test_attempts (
    attempt_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    total_questions INTEGER NOT NULL CHECK (total_questions > 0),
    attempted_questions INTEGER NOT NULL CHECK (attempted_questions >= 0),
    correct_answers INTEGER NOT NULL CHECK (correct_answers >= 0),
    incorrect_answers INTEGER NOT NULL CHECK (incorrect_answers >= 0),
    unattempted_questions INTEGER NOT NULL CHECK (unattempted_questions >= 0),
    raw_score DOUBLE PRECISION NOT NULL,
    percentage DOUBLE PRECISION NOT NULL CHECK (percentage BETWEEN -100.0 AND 100.0),
    accuracy DOUBLE PRECISION NOT NULL CHECK (accuracy BETWEEN 0.0 AND 1.0),
    completed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT learner_attempt_counts_reconcile CHECK (
        attempted_questions = correct_answers + incorrect_answers
        AND total_questions = attempted_questions + unattempted_questions
    ),
    CONSTRAINT uq_learner_session UNIQUE (learner_id, session_id)
);

CREATE TABLE IF NOT EXISTS learner_topic_attempts (
    attempt_id TEXT NOT NULL
        REFERENCES learner_test_attempts(attempt_id)
        ON DELETE CASCADE,
    learner_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    question_count INTEGER NOT NULL CHECK (question_count > 0),
    attempted_count INTEGER NOT NULL CHECK (attempted_count >= 0),
    correct_count INTEGER NOT NULL CHECK (correct_count >= 0),
    incorrect_count INTEGER NOT NULL CHECK (incorrect_count >= 0),
    unattempted_count INTEGER NOT NULL CHECK (unattempted_count >= 0),
    accuracy DOUBLE PRECISION NOT NULL CHECK (accuracy BETWEEN 0.0 AND 1.0),
    performance TEXT NOT NULL CHECK (performance IN ('STRONG', 'AVERAGE', 'WEAK')),
    CONSTRAINT learner_topic_counts_reconcile CHECK (
        attempted_count = correct_count + incorrect_count
        AND question_count = attempted_count + unattempted_count
    ),
    PRIMARY KEY (attempt_id, concept_id)
);

CREATE INDEX IF NOT EXISTS idx_learner_attempts_learner_completed
    ON learner_test_attempts(learner_id, completed_at, session_id);

CREATE INDEX IF NOT EXISTS idx_learner_topics_learner_concept
    ON learner_topic_attempts(learner_id, concept_id, attempt_id);
