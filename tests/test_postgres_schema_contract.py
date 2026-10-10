from pathlib import Path


MIGRATIONS_ROOT = Path(__file__).resolve().parents[1] / "database" / "migrations"


def schema_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(MIGRATIONS_ROOT.glob("*.sql"))
    )


def test_phase4_schema_contains_required_core_tables():
    sql = schema_text()
    required_tables = (
        "conducting_bodies",
        "exams",
        "paper_categories",
        "sources",
        "source_verifications",
        "paper_candidates",
        "papers",
        "documents",
        "normalized_documents",
        "questions",
        "question_options",
        "concepts",
        "question_concepts",
        "question_matches",
        "match_evidence",
        "exam_appearances",
        "appearance_sources",
        "embedding_models",
        "question_embeddings",
        "answer_key_entries",
        "question_answer_records",
        "master_questions",
        "master_question_options",
        "master_question_memberships",
        "master_merge_events",
        "master_repair_events",
    )

    for table in required_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql


def test_phase4_schema_enforces_verified_history_and_copy_dedup_boundaries():
    sql = schema_text()

    assert "verification_id TEXT NOT NULL REFERENCES source_verifications" in sql
    assert "uq_exam_appearance_identity" in sql
    assert "COALESCE(shift, '')" in sql
    assert "CREATE TABLE IF NOT EXISTS appearance_sources" in sql
    assert "CREATE EXTENSION IF NOT EXISTS vector;" in sql


def test_phase4_schema_keeps_embedding_provider_and_model_configurable():
    sql = schema_text()

    assert "CREATE TABLE IF NOT EXISTS embedding_models" in sql
    assert "provider TEXT NOT NULL" in sql
    assert "model_name TEXT NOT NULL" in sql
    assert "embedding vector NOT NULL" in sql


def test_phase4_schema_enforces_canonical_match_pair_ordering():
    sql = schema_text()
    assert "question_matches_canonical_order" in sql
    assert "CHECK (left_question_id < right_question_id)" in sql

def test_phase5_schema_enforces_one_master_per_observed_question():
    sql = schema_text()
    assert "UNIQUE (question_id)" in sql
    assert "UNIQUE (canonical_question_id)" in sql
    assert "master_questions_status" in sql


def test_phase5_schema_restricts_master_memberships_to_equivalent_relationships():
    sql = schema_text()
    assert "relationship IN ('CANONICAL', 'EXACT', 'REPHRASED')" in sql


def test_phase625_schema_persists_immutable_strategy_audit_and_task_adjustments():
    sql = schema_text()

    assert "CREATE TABLE IF NOT EXISTS adaptive_study_strategy_audits" in sql
    assert "CREATE TABLE IF NOT EXISTS adaptive_study_strategy_audit_adjustments" in sql
    assert "payload_sha256 CHAR(64) NOT NULL" in sql
    assert "source_schedule_snapshot JSONB NOT NULL" in sql
    assert "strategy_report_snapshot JSONB NOT NULL" in sql
    assert "resulting_schedule_snapshot JSONB NOT NULL" in sql
    assert "previous_priority_score DOUBLE PRECISION NOT NULL" in sql
    assert "recommended_priority_score DOUBLE PRECISION NOT NULL" in sql
    assert "applied_priority_score DOUBLE PRECISION" in sql
    assert "ON DELETE RESTRICT" in sql
    assert "idx_adaptive_strategy_audit_learner_history" in sql

def test_phase634_schema_persists_test_session_state_and_question_snapshots():
    sql = schema_text()
    assert "CREATE TABLE IF NOT EXISTS preparation_test_sessions" in sql
    assert "preparation_request_id TEXT NOT NULL" in sql
    assert "question_snapshot JSONB NOT NULL" in sql
    assert "session_state JSONB NOT NULL" in sql
    assert "idx_preparation_test_sessions_learner_history" in sql
