from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ai_comp.api.app import create_postgres_app
from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner
from ai_comp.database.postgres_generated_question import PostgresGeneratedQuestionRepository
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)


pytestmark = pytest.mark.integration


def database_url() -> str:
    value = os.getenv("AI_COMP_DATABASE_URL", "").strip()
    if not value:
        pytest.skip("AI_COMP_DATABASE_URL is not configured")
    return value


def apply_migrations(dsn: str) -> None:
    migrations_dir = Path(__file__).resolve().parents[1] / "database" / "migrations"
    with connect_postgres(dsn) as connection:
        MigrationRunner(migrations_dir).apply(connection)


def accepted_question(question_id: str, concept_id: str) -> GeneratedMCQ:
    return GeneratedMCQ(
        generated_question_id=question_id,
        generation_id=f"generation-{question_id}",
        material_id=f"material-{question_id}",
        stem="राजस्थान की भौगोलिक विशेषता से संबंधित सही कथन कौन सा है?",
        options=(
            GeneratedOption("A", "विकल्प A"),
            GeneratedOption("B", "विकल्प B"),
            GeneratedOption("C", "विकल्प C"),
            GeneratedOption("D", "विकल्प D"),
        ),
        correct_option_key="A",
        explanation="Stored verified explanation.",
        fact_ids=(f"fact-{question_id}",),
        concept_ids=(concept_id,),
        difficulty="MEDIUM",
        importance_score=1.0,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("Persisted verification evidence.",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.99,
    )


def test_post_creates_persistent_request_and_guidance_uses_saved_settings():
    dsn = database_url()
    apply_migrations(dsn)
    suffix = uuid4().hex
    learner_id = f"phase632-{suffix}"
    question_id = f"phase632-question-{suffix}"
    concept_id = f"phase632-concept-{suffix}"
    client = TestClient(create_postgres_app(
        dsn=dsn,
        learner_identity_provider=lambda _request: learner_id,
    ))
    payload = {
        "title": "Rajasthan geography practice",
        "question_count": 1,
        "duration_seconds": 900,
        "correct_marks": 2.0,
        "incorrect_marks": -0.5,
        "unattempted_marks": 0.0,
        "mode": "ADAPTIVE",
        "concept_ids": [concept_id],
        "exam_id": "RSSB_CET",
        "subject_id": "RAJASTHAN_GEOGRAPHY",
    }

    with connect_postgres(dsn) as connection:
        PostgresGeneratedQuestionRepository(connection).save(
            accepted_question(question_id, concept_id)
        )
    try:
        created = client.post(
            f"/api/v1/learners/{learner_id}/preparation-requests",
            json=payload,
        )
        assert created.status_code == 201, created.text
        created_payload = created.json()
        assert created_payload["status"] == "ACTIVE"
        assert created_payload["learner_id"] == learner_id
        assert created_payload["question_count"] == 1
        assert created_payload["duration_seconds"] == 900
        assert created_payload["scoring"] == {
            "correct_marks": 2.0,
            "incorrect_marks": -0.5,
            "unattempted_marks": 0.0,
        }
        assert created_payload["concept_ids"] == [concept_id]

        active = client.get(
            f"/api/v1/learners/{learner_id}/preparation-requests/active"
        )
        assert active.status_code == 200
        assert active.json()["request_id"] == created_payload["request_id"]
        assert active.json()["exam_id"] == "RSSB_CET"

        guidance = client.get(
            f"/api/v1/learners/{learner_id}/preparation-guidance?history_limit=25"
        )
        assert guidance.status_code == 200, guidance.text
        plan = guidance.json()["guidance"]["preparation_plan"]
        assert plan["test_specification"]["test_id"] == created_payload["test_id"]
        assert plan["test_specification"]["title"] == payload["title"]
        assert plan["test_specification"]["duration_seconds"] == 900
        assert plan["test_specification"]["scoring"]["incorrect_marks"] == -0.5
        assert plan["question_ids"] == [question_id]

        replacement = client.post(
            f"/api/v1/learners/{learner_id}/preparation-requests",
            json={**payload, "title": "Replacement test", "duration_seconds": 1200},
        )
        assert replacement.status_code == 201, replacement.text
        assert replacement.json()["request_id"] != created_payload["request_id"]
        next_active = client.get(
            f"/api/v1/learners/{learner_id}/preparation-requests/active"
        )
        assert next_active.json()["request_id"] == replacement.json()["request_id"]
        next_guidance = client.get(
            f"/api/v1/learners/{learner_id}/preparation-guidance"
        )
        assert next_guidance.status_code == 200, next_guidance.text
        assert next_guidance.json()["guidance"]["preparation_plan"]["test_specification"]["duration_seconds"] == 1200
    finally:
        with connect_postgres(dsn) as connection:
            connection.execute(
                "DELETE FROM preparation_test_requests WHERE learner_id = %s",
                (learner_id,),
            )
            connection.execute(
                "DELETE FROM generated_questions WHERE generated_question_id = %s",
                (question_id,),
            )


def test_preparation_request_validation_and_learner_scope_fail_closed():
    dsn = database_url()
    apply_migrations(dsn)
    authenticated = "phase632-owner"
    other = "phase632-other"
    client = TestClient(create_postgres_app(
        dsn=dsn,
        learner_identity_provider=lambda _request: authenticated,
    ))

    mismatch = client.post(
        f"/api/v1/learners/{other}/preparation-requests",
        json={"title": "Not allowed", "question_count": 10, "duration_seconds": 600},
    )
    invalid = client.post(
        f"/api/v1/learners/{authenticated}/preparation-requests",
        json={"title": "Bad settings", "question_count": 0, "duration_seconds": 600},
    )
    duplicate_concepts = client.post(
        f"/api/v1/learners/{authenticated}/preparation-requests",
        json={
            "title": "Bad concept set",
            "question_count": 1,
            "duration_seconds": 600,
            "concept_ids": ["c1", "c1"],
        },
    )
    assert mismatch.status_code == 403
    assert invalid.status_code == 422
    assert duplicate_concepts.status_code == 422


def test_active_request_is_404_until_learner_has_saved_settings():
    dsn = database_url()
    apply_migrations(dsn)
    learner_id = f"phase632-empty-{uuid4().hex}"
    client = TestClient(create_postgres_app(
        dsn=dsn,
        learner_identity_provider=lambda _request: learner_id,
    ))

    active = client.get(
        f"/api/v1/learners/{learner_id}/preparation-requests/active"
    )
    guidance = client.get(
        f"/api/v1/learners/{learner_id}/preparation-guidance"
    )
    assert active.status_code == 404
    assert guidance.status_code == 503
