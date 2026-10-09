CREATE TABLE IF NOT EXISTS adaptive_study_strategy_audits (
    audit_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    source_schedule_id CHAR(64) NOT NULL,
    resulting_schedule_id CHAR(64) NOT NULL,
    assessment_session_id TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    payload_sha256 CHAR(64) NOT NULL,
    source_schedule_snapshot JSONB NOT NULL
        CHECK (jsonb_typeof(source_schedule_snapshot) = 'object'),
    strategy_report_snapshot JSONB NOT NULL
        CHECK (jsonb_typeof(strategy_report_snapshot) = 'object'),
    resulting_schedule_snapshot JSONB NOT NULL
        CHECK (jsonb_typeof(resulting_schedule_snapshot) = 'object'),
    CONSTRAINT adaptive_strategy_audit_source_fingerprint
        CHECK (source_schedule_id ~ '^[0-9a-f]{64}$'),
    CONSTRAINT adaptive_strategy_audit_result_fingerprint
        CHECK (resulting_schedule_id ~ '^[0-9a-f]{64}$'),
    CONSTRAINT adaptive_strategy_audit_payload_hash
        CHECK (payload_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE INDEX IF NOT EXISTS idx_adaptive_strategy_audit_learner_history
    ON adaptive_study_strategy_audits (learner_id, recorded_at DESC, audit_id);

CREATE INDEX IF NOT EXISTS idx_adaptive_strategy_audit_assessment
    ON adaptive_study_strategy_audits (learner_id, assessment_session_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS adaptive_study_strategy_audit_adjustments (
    audit_id TEXT NOT NULL REFERENCES adaptive_study_strategy_audits(audit_id)
        ON DELETE RESTRICT,
    task_id TEXT NOT NULL,
    task_kind TEXT NOT NULL CHECK (
        task_kind IN ('REVIEW_DUE_REVISION', 'REVIEW_PREVIOUS_MISTAKES',
                      'STUDY_WEAK_TOPIC', 'PRACTICE_QUESTIONS')
    ),
    execution_status TEXT NOT NULL CHECK (
        execution_status IN ('COMPLETED', 'PARTIAL', 'SKIPPED', 'POSTPONED')
    ),
    evidence_kind TEXT NOT NULL CHECK (
        evidence_kind IN ('DIRECT_QUESTION_MATCH', 'CONCEPT_OVERLAP', 'NO_RELATED_EVIDENCE')
    ),
    source_trend TEXT NOT NULL CHECK (
        source_trend IN ('IMPROVING', 'DECLINING', 'STABLE', 'INSUFFICIENT_DATA')
    ),
    action TEXT NOT NULL CHECK (
        action IN ('REINFORCE_WEAK_AREA', 'CONTINUE_TARGETED_PRACTICE',
                   'MAINTAIN_AND_RETEST', 'SPACE_REVISION', 'COLLECT_MORE_EVIDENCE')
    ),
    previous_priority_score DOUBLE PRECISION NOT NULL
        CHECK (previous_priority_score >= 0 AND previous_priority_score <= 1),
    recommended_priority_score DOUBLE PRECISION NOT NULL
        CHECK (recommended_priority_score >= 0 AND recommended_priority_score <= 1),
    applied_priority_score DOUBLE PRECISION
        CHECK (applied_priority_score IS NULL OR
               (applied_priority_score >= 0 AND applied_priority_score <= 1)),
    suggested_revision_interval_days INTEGER
        CHECK (suggested_revision_interval_days IS NULL OR suggested_revision_interval_days > 0),
    baseline_attempted_count INTEGER NOT NULL CHECK (baseline_attempted_count >= 0),
    follow_up_attempted_count INTEGER NOT NULL CHECK (follow_up_attempted_count >= 0),
    baseline_accuracy_percentage DOUBLE PRECISION
        CHECK (baseline_accuracy_percentage IS NULL OR
               (baseline_accuracy_percentage >= 0 AND baseline_accuracy_percentage <= 100)),
    follow_up_accuracy_percentage DOUBLE PRECISION
        CHECK (follow_up_accuracy_percentage IS NULL OR
               (follow_up_accuracy_percentage >= 0 AND follow_up_accuracy_percentage <= 100)),
    delta_percentage_points DOUBLE PRECISION,
    reason TEXT NOT NULL,
    PRIMARY KEY (audit_id, task_id)
);

CREATE INDEX IF NOT EXISTS idx_adaptive_strategy_audit_adjustments_action
    ON adaptive_study_strategy_audit_adjustments (action, audit_id);
