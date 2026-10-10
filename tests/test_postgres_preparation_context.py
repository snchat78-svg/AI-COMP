from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ai_comp.api.app import create_postgres_app
from ai_comp.api.postgres_preparation_context import PreparationTestRequest
from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner
from ai_comp.database.postgres_generated_question import PostgresGeneratedQuestionRepository
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.test_engine import TestSpecification as PreparationSpecification


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


class FixedTestRequestProvider:
    def __init__(self, request_spec: PreparationTestRequest) -> None:
        self.request_spec = request_spec

    def load_request(self, learner_id, *, request):
        return self.request_spec


def accepted_question(question_id: str, concept_id: str) -> GeneratedMCQ:
    return GeneratedMCQ(
        generated_question_id=question_id,
        generation_id=f"generation-{question_id}",
        material_id=f"material-{question_id}",
        stem="राजस्थान के क्षेत्रफल से संबंधित सही कथन कौन सा है?",
        options=(
            GeneratedOption("A", "विकल्प A"),
            GeneratedOption("B", "विकल्प B"),
            GeneratedOption("C", "विकल्प C"),
            GeneratedOption("D", "विकल्प D"),
        ),
        correct_option_key="A",
        explanation="Stored source-verified explanation.",
        fact_ids=(f"fact-{question_id}",),
        concept_ids=(concept_id,),
        difficulty="MEDIUM",
        importance_score=1.0,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("Persisted verification evidence.",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.99,
    )


def make_app(dsn: str, learner_id: str, test_request: PreparationTestRequest, *, pool_limit=5000):
    return create_postgres_app(
        dsn=dsn,
        learner_identity_provider=lambda _request: learner_id,
        preparation_test_request_provider=FixedTestRequestProvider(test_request),
        question_pool_limit=pool_limit,
    )


def test_postgres_context_drives_fastapi_guidance_from_verified_question_store():
    dsn = database_url()
    apply_migrations(dsn)
    suffix = uuid4().hex
    learner_id = f"phase631-{suffix}"
    question_id = f"phase631-question-{suffix}"
    concept_id = f"phase631-concept-{suffix}"
    generated = accepted_question(question_id, concept_id)

    with connect_postgres(dsn) as connection:
        PostgresGeneratedQuestionRepository(connection).save(generated)

    try:
        test_request = PreparationTestRequest(
            learner_id=learner_id,
            specification=PreparationSpecification(
                test_id=f"phase631-test-{suffix}",
                title="Rajasthan practice",
                question_count=1,
                duration_seconds=600,
            ),
            mode=PersonalizedPreparationMode.ADAPTIVE,
            concept_ids=(concept_id,),
        )
        response = TestClient(make_app(dsn, learner_id, test_request)).get(
            f"/api/v1/learners/{learner_id}/preparation-guidance?history_limit=25"
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["learner_id"] == learner_id
        assert payload["schema_version"] == "1.0"
        assert payload["guidance"]["preparation_plan"]["question_ids"] == [question_id]
        assert payload["strategy_history"]["summary"]["audit_count"] == 0
        assert response.headers["cache-control"] == "no-store"
    finally:
        with connect_postgres(dsn) as connection:
            connection.execute(
                "DELETE FROM generated_questions WHERE generated_question_id = %s",
                (question_id,),
            )


def test_postgres_context_returns_unavailable_when_question_pool_is_too_small():
    dsn = database_url()
    apply_migrations(dsn)
    suffix = uuid4().hex
    learner_id = f"phase631-short-{suffix}"
    test_request = PreparationTestRequest(
        learner_id=learner_id,
        specification=PreparationSpecification(
            test_id=f"phase631-large-test-{suffix}",
            title="Pool bound check",
            question_count=2,
            duration_seconds=600,
        ),
    )

    # Limit the request to at most one stored question; two unique accepted
    # questions are required, so the provider must not manufacture substitutes.
    response = TestClient(make_app(dsn, learner_id, test_request, pool_limit=1)).get(
        f"/api/v1/learners/{learner_id}/preparation-guidance"
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PREPARATION_CONTEXT_UNAVAILABLE"


def test_provider_rejects_test_request_for_another_learner_without_database_access():
    request_spec = PreparationTestRequest(
        learner_id="learner-b",
        specification=PreparationSpecification(
            test_id="test-b",
            title="Scoped test",
            question_count=1,
            duration_seconds=60,
        ),
    )
    app = create_postgres_app(
        dsn="postgresql://unused",
        learner_identity_provider=lambda _request: "learner-a",
        preparation_test_request_provider=FixedTestRequestProvider(request_spec),
    )

    response = TestClient(app).get(
        "/api/v1/learners/learner-a/preparation-guidance"
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PREPARATION_CONTEXT_UNAVAILABLE"
