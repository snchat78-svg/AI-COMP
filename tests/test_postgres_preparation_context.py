from __future__ import annotations

import json
import os
from hashlib import sha256
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ai_comp.api.app import create_postgres_app
from ai_comp.api.postgres_preparation_context import (
    PostgresPreparationContextProvider,
    PreparationTestRequest,
)
from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner
from ai_comp.database.postgres_generated_question import PostgresGeneratedQuestionRepository
from ai_comp.database.postgres_verified_history_question import (
    PostgresVerifiedHistoryQuestionRepository,
)
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
    QuestionSourceKind,
)
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.test_engine import TestSpecification as PreparationSpecification
from starlette.requests import Request


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


def test_verified_exam_history_enters_mixed_pool_with_provenance_and_stem_deduplication():
    dsn = database_url()
    apply_migrations(dsn)
    suffix = uuid4().hex
    body_id = f"pool-body-{suffix}"
    exam_id = f"pool-exam-{suffix}"
    category_id = f"pool-category-{suffix}"
    source_id = f"pool-official-source-{suffix}"
    question_candidate_id = f"pool-question-candidate-{suffix}"
    key_candidate_id = f"pool-key-candidate-{suffix}"
    question_document_id = f"pool-question-document-{suffix}"
    key_document_id = f"pool-key-document-{suffix}"
    question_id = f"pool-question-{suffix}"
    question_paper_id = f"pool-question-paper-{suffix}"
    key_paper_id = f"pool-key-paper-{suffix}"
    question_verification_id = f"pool-paper-verification-{suffix}"
    key_verification_id = f"pool-key-verification-{suffix}"
    appearance_id = f"pool-appearance-{suffix}"
    pair_id = f"pool-pair-{suffix}"
    learner_id = f"pool-learner-{suffix}"
    generated_id = f"pool-generated-{suffix}"
    host = "https://fixture-official.example.test/"
    question_url = f"{host}papers/{suffix}.pdf"
    key_url = f"{host}answer-keys/{suffix}.pdf"
    question_sha = sha256(f"question-{suffix}".encode()).hexdigest()
    key_sha = sha256(f"answer-key-{suffix}".encode()).hexdigest()
    question_stem = "राजस्थान के क्षेत्रफल से संबंधित सही कथन कौन सा है?"
    option_rows = (
        ("A", "विकल्प एक"),
        ("B", "सही विकल्प"),
        ("C", "विकल्प तीन"),
        ("D", "विकल्प चार"),
    )

    test_request = PreparationTestRequest(
        learner_id=learner_id,
        specification=PreparationSpecification(
            test_id=f"pool-test-{suffix}",
            title="Official history pool regression",
            question_count=1,
            duration_seconds=600,
        ),
        mode=PersonalizedPreparationMode.MIXED,
        concept_ids=(),
    )
    provider = PostgresPreparationContextProvider(
        lambda: connect_postgres(dsn),
        FixedTestRequestProvider(test_request),
        question_pool_limit=25,
    )
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
    })

    with connect_postgres(dsn) as connection:
        with connection.transaction():
            connection.execute(
                "INSERT INTO conducting_bodies (body_id, name, level, state) "
                "VALUES (%s, %s, 'STATE', 'Rajasthan')",
                (body_id, f"Test body {suffix}"),
            )
            connection.execute(
                "INSERT INTO exams (exam_id, name, conducting_body_id, level, state) "
                "VALUES (%s, %s, %s, 'STATE', 'Rajasthan')",
                (exam_id, f"Test recruitment exam {suffix}", body_id),
            )
            connection.execute(
                "INSERT INTO paper_categories (category_id, name, exam_id) "
                "VALUES (%s, 'Test paper category', %s)",
                (category_id, exam_id),
            )
            connection.execute(
                "INSERT INTO sources "
                "(source_id, name, base_url, source_type, priority, conducting_body_id) "
                "VALUES (%s, 'Fixture official source', %s, 'OFFICIAL_WEBSITE', 'OFFICIAL', %s)",
                (source_id, host, body_id),
            )
            connection.execute(
                "INSERT INTO paper_candidates "
                "(candidate_id, source_id, url, title, format, category_id, status) "
                "VALUES (%s, %s, %s, 'Fixture question paper', 'pdf', %s, 'FETCHED'), "
                "(%s, %s, %s, 'Fixture official answer key', 'pdf', %s, 'FETCHED')",
                (
                    question_candidate_id, source_id, question_url, category_id,
                    key_candidate_id, source_id, key_url, category_id,
                ),
            )
            connection.execute(
                "INSERT INTO documents "
                "(document_id, candidate_id, source_url, content_type, sha256, size_bytes, "
                "storage_key, declared_format, detected_format) "
                "VALUES (%s, %s, %s, 'application/pdf', %s, 100, %s, 'pdf', 'pdf'), "
                "(%s, %s, %s, 'application/pdf', %s, 100, %s, 'pdf', 'pdf')",
                (
                    question_document_id, question_candidate_id, question_url, question_sha,
                    f"fixture/{question_sha}",
                    key_document_id, key_candidate_id, key_url, key_sha,
                    f"fixture/{key_sha}",
                ),
            )
            connection.execute(
                "INSERT INTO questions "
                "(question_id, document_id, document_sha256, question_number, stem, kind, "
                "raw_text, start_line, end_line) "
                "VALUES (%s, %s, %s, 7, %s, 'MCQ', %s, 1, 8)",
                (question_id, question_document_id, question_sha, question_stem, question_stem),
            )
            for order, (key, option_text) in enumerate(option_rows, start=1):
                connection.execute(
                    "INSERT INTO question_options (question_id, option_key, option_text, option_order) "
                    "VALUES (%s, %s, %s, %s)",
                    (question_id, key, option_text, order),
                )
            connection.execute(
                "INSERT INTO papers "
                "(paper_id, candidate_id, title, exam_id, category_id, source_id, canonical_url, year, shift) "
                "VALUES (%s, %s, 'Fixture question paper', %s, %s, %s, %s, 2024, 'MORNING'), "
                "(%s, %s, 'Fixture answer key', %s, %s, %s, %s, 2024, 'MORNING')",
                (
                    question_paper_id, question_candidate_id, exam_id, category_id,
                    source_id, question_url,
                    key_paper_id, key_candidate_id, exam_id, category_id, source_id, key_url,
                ),
            )
            connection.execute(
                "INSERT INTO source_verifications "
                "(verification_id, source_id, source_url, status, evidence_type, checked_at, confidence, notes) "
                "VALUES (%s, %s, %s, 'VERIFIED', 'OFFICIAL_PAPER', NOW(), 1.0, 'fixture paper proof'), "
                "(%s, %s, %s, 'VERIFIED', 'OFFICIAL_ANSWER_KEY', NOW(), 1.0, 'fixture key proof')",
                (
                    question_verification_id, source_id, question_url,
                    key_verification_id, source_id, key_url,
                ),
            )
            connection.execute(
                "INSERT INTO paper_answer_key_pairs "
                "(pair_id, question_paper_id, answer_key_paper_id, question_candidate_id, "
                "answer_key_candidate_id, question_document_id, answer_key_document_id, "
                "exam_id, year, shift, pair_status, match_reason) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 2024, 'MORNING', 'MATCHED', 'fixture match')",
                (
                    pair_id, question_paper_id, key_paper_id, question_candidate_id,
                    key_candidate_id, question_document_id, key_document_id, exam_id,
                ),
            )
            connection.execute(
                "INSERT INTO question_answer_records "
                "(question_id, document_id, question_number, answer_key, selected_option_key, "
                "status, method, source_line, notes, source_answer_key_document_id) "
                "VALUES (%s, %s, 7, 'B', 'B', 'RESOLVED', 'DIRECT_OPTION_KEY', 1, 'fixture key', %s)",
                (question_id, question_document_id, key_document_id),
            )
            connection.execute(
                "INSERT INTO exam_appearances "
                "(appearance_id, question_id, exam_id, conducting_body_id, year, shift, question_number, "
                "original_question, options, correct_answer, source_url, paper_id, verification_id, match_type) "
                "VALUES (%s, %s, %s, %s, 2024, 'MORNING', 7, %s, %s::jsonb, 'B', %s, %s, %s, 'EXACT')",
                (
                    appearance_id, question_id, exam_id, body_id, question_stem,
                    json.dumps([[key, text] for key, text in option_rows]),
                    question_url, question_paper_id, question_verification_id,
                ),
            )
            connection.execute(
                "INSERT INTO appearance_sources (appearance_id, source_url, paper_id, verification_id) "
                "VALUES (%s, %s, %s, %s), (%s, %s, %s, %s)",
                (
                    appearance_id, question_url, question_paper_id, question_verification_id,
                    appearance_id, key_url, key_paper_id, key_verification_id,
                ),
            )
            # Deliberately store an accepted generated duplicate. The official
            # source-backed historical row must win the exact-stem deduplication.
            generated = replace(
                accepted_question(generated_id, f"unused-concept-{suffix}"),
                stem=question_stem,
            )
            PostgresGeneratedQuestionRepository(connection).save(generated)

    try:
        context = provider.load_context(learner_id, request=request)

        assert context["available_question_count"] == 1
        assert len(context["questions"]) == 1
        question = context["questions"][0]
        assert question.source_kind is QuestionSourceKind.VERIFIED_EXAM_HISTORY
        assert question.exam_name == f"Test recruitment exam {suffix}"
        assert question.exam_year == 2024
        assert question.exam_shift == "MORNING"
        assert question.exam_question_number == 7
        assert question.verified_appearance_count == 1
        assert question.correct_option_key == "B"
        assert question.source_url == question_url
        assert question.answer_key_source_url == key_url

        readiness = provider.get_question_bank_readiness()
        assert readiness["eligible_question_count"] == 1
        assert readiness["verified_history_question_count"] == 1
        assert readiness["accepted_generated_question_count"] == 0
        assert readiness["practice_test_available"] is True
    finally:
        with connect_postgres(dsn) as connection:
            with connection.transaction():
                connection.execute(
                    "DELETE FROM generated_questions WHERE generated_question_id = %s",
                    (generated_id,),
                )
                connection.execute(
                    "DELETE FROM exam_appearances WHERE appearance_id = %s",
                    (appearance_id,),
                )
                connection.execute(
                    "DELETE FROM paper_answer_key_pairs WHERE pair_id = %s",
                    (pair_id,),
                )
                connection.execute(
                    "DELETE FROM questions WHERE question_id = %s",
                    (question_id,),
                )
                connection.execute(
                    "DELETE FROM papers WHERE paper_id = ANY(%s)",
                    ([question_paper_id, key_paper_id],),
                )
                connection.execute(
                    "DELETE FROM documents WHERE document_id = ANY(%s)",
                    ([question_document_id, key_document_id],),
                )
                connection.execute(
                    "DELETE FROM source_verifications WHERE verification_id = ANY(%s)",
                    ([question_verification_id, key_verification_id],),
                )
                connection.execute(
                    "DELETE FROM paper_candidates WHERE candidate_id = ANY(%s)",
                    ([question_candidate_id, key_candidate_id],),
                )
                connection.execute(
                    "DELETE FROM paper_categories WHERE category_id = %s",
                    (category_id,),
                )
                connection.execute("DELETE FROM exams WHERE exam_id = %s", (exam_id,))
                connection.execute("DELETE FROM sources WHERE source_id = %s", (source_id,))
                connection.execute(
                    "DELETE FROM conducting_bodies WHERE body_id = %s",
                    (body_id,),
                )
