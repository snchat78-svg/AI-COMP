CREATE TABLE IF NOT EXISTS study_schedule_task_events (
    event_id TEXT PRIMARY KEY,
    schedule_id CHAR(64) NOT NULL,
    learner_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('COMPLETED', 'PARTIAL', 'SKIPPED', 'POSTPONED')),
    occurred_at TIMESTAMPTZ NOT NULL,
    actual_minutes INTEGER NOT NULL DEFAULT 0 CHECK (actual_minutes >= 0),
    remaining_minutes INTEGER,
    postponed_until DATE,
    completed_question_ids TEXT[] NOT NULL DEFAULT '{}',
    note TEXT,
    CONSTRAINT study_schedule_partial_remaining CHECK (
        (status = 'PARTIAL' AND remaining_minutes IS NOT NULL AND remaining_minutes > 0)
        OR (status <> 'PARTIAL' AND remaining_minutes IS NULL)
    ),
    CONSTRAINT study_schedule_postponed_date CHECK (
        (status = 'POSTPONED' AND postponed_until IS NOT NULL)
        OR (status <> 'POSTPONED' AND postponed_until IS NULL)
    ),
    CONSTRAINT study_schedule_partial_questions CHECK (
        status = 'PARTIAL' OR cardinality(completed_question_ids) = 0
    )
);

CREATE INDEX IF NOT EXISTS idx_study_schedule_events_scope
    ON study_schedule_task_events (schedule_id, learner_id, occurred_at, event_id);

CREATE INDEX IF NOT EXISTS idx_study_schedule_events_learner
    ON study_schedule_task_events (learner_id, occurred_at);
