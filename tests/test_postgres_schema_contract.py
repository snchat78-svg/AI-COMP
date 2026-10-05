from pathlib import Path


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "database"
    / "migrations"
    / "0001_phase4_core.sql"
)


def schema_text() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


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
