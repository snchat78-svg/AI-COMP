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
        stem=f"Question {question_id}: राजस्थान के बारे में सही कथन चुनें।",
        options=(
            GeneratedOption("A", "सही विकल्प"),
            GeneratedOption("B", "गलत विकल्प"),
            GeneratedOption("C", "अन्य विकल्प"),
            GeneratedOption("D", "अन्य विकल्प"),
        ),
        correct_option_key="A",
        explanation="Saved source-backed explanation.",
        fact_ids=(f"fact-{question_id}",),
        concept_ids=(concept_id,),
        difficulty="MEDIUM",
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("Verified integration fixture",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.98,
    )


def test_saved_request_creates_persistent_session_that_can_be_resumed_and_submitted():
    dsn = database_url()
    apply_migrations(dsn)
    suffix = uuid4().hex
    learner_id = f"phase634-learner-{suffix}"
    concept_id = f"phase634-concept-{suffix}"
    question_ids = [f"phase634-question-{suffix}-{index}" for index in range(1, 4)]
    client = TestClient(create_postgres_app(
        dsn=dsn,
        learner_identity_provider=lambda _request: learner_id,
    ))
    request_url = f"/api/v1/learners/{learner_id}/preparation-requests"
    sessions_url = f"/api/v1/learners/{learner_id}/preparation-sessions"

    with connect_postgres(dsn) as connection:
        question_repo = PostgresGeneratedQuestionRepository(connection)
        for question_id in question_ids:
            question_repo.save(accepted_question(question_id, concept_id))

    try:
        created_request = client.post(request_url, json={
            "title": "Persisted practice session",
            "question_count": 2,
            "duration_seconds": 900,
            "correct_marks": 2.0,
            "incorrect_marks": -0.5,
            "mode": "MIXED",
            "concept_ids": [concept_id],
        })
        assert created_request.status_code == 201, created_request.text

        created_session = client.post(sessions_url)
        assert created_session.status_code == 201, created_session.text
        initial = created_session.json()
        session_id = initial["session_id"]
        assert initial["status"] == "CREATED"
        assert initial["mode"] == "MIXED"
        assert initial["preparation_request_id"] == created_request.json()["request_id"]
        assert initial["question_count"] == 2
        assert len(initial["question_ids"]) == 2
        with connect_postgres(dsn) as connection:
            snapshot_size = connection.execute(
                "SELECT jsonb_array_length(question_snapshot) "
                "FROM preparation_test_sessions WHERE session_id = %s",
                (session_id,),
            ).fetchone()[0]
        assert snapshot_size == 2

        saved = client.get(f"{sessions_url}/{session_id}")
        assert saved.status_code == 200, saved.text
        assert saved.json()["status"] == "CREATED"

        started = client.post(f"{sessions_url}/{session_id}/start")
        assert started.status_code == 200, started.text
        assert started.json()["status"] == "IN_PROGRESS"
        assert started.json()["remaining_seconds"] > 0

        hidden_review = client.get(f"{sessions_url}/{session_id}/answer-review")
        assert hidden_review.status_code == 409, hidden_review.text
        assert hidden_review.json()["error"]["code"] == "ANSWER_REVIEW_NOT_AVAILABLE"
        assert "correct_option_key" not in hidden_review.text

        current = client.get(f"{sessions_url}/{session_id}/current-question")
        assert current.status_code == 200, current.text
        assert len(current.json()["options"]) == 4
        assert "correct_option_key" not in current.json()
        first_answer = client.post(f"{sessions_url}/{session_id}/answer", json={"option_key": "A"})
        assert first_answer.status_code == 200, first_answer.text
        assert first_answer.json()["answered_question_count"] == 1

        moved = client.post(f"{sessions_url}/{session_id}/next")
        assert moved.status_code == 200, moved.text
        assert moved.json()["current_question_number"] == 2
        reviewed = client.post(f"{sessions_url}/{session_id}/review")
        assert reviewed.status_code == 200
        assert reviewed.json()["review_question_count"] == 1
        second_answer = client.post(f"{sessions_url}/{session_id}/answer", json={"option_key": "B"})
        assert second_answer.status_code == 200, second_answer.text

        submitted = client.post(f"{sessions_url}/{session_id}/submit")
        assert submitted.status_code == 200, submitted.text
        result = submitted.json()["result"]
        assert result["status"] == "SUBMITTED"
        assert result["attempted_questions"] == 2
        assert result["correct_answers"] == 1
        assert result["incorrect_answers"] == 1
        assert result["raw_score"] == 1.5
        assert result["max_score"] == 4.0

        answer_review = client.get(f"{sessions_url}/{session_id}/answer-review")
        assert answer_review.status_code == 200, answer_review.text
        review_payload = answer_review.json()
        assert review_payload["status"] == "SUBMITTED"
        assert review_payload["summary"] == {
            "total_questions": 2,
            "correct_answers": 1,
            "incorrect_answers": 1,
            "unattempted_questions": 0,
        }
        assert {item["outcome"] for item in review_payload["questions"]} == {"CORRECT", "INCORRECT"}
        correct_review = next(item for item in review_payload["questions"] if item["outcome"] == "CORRECT")
        incorrect_review = next(item for item in review_payload["questions"] if item["outcome"] == "INCORRECT")
        assert correct_review["selected_option_key"] == correct_review["correct_option_key"] == "A"
        assert incorrect_review["selected_option_key"] == "B"
        assert incorrect_review["correct_option_key"] == "A"
        assert all(item["explanation"] for item in review_payload["questions"])
        assert all(item["answer_verification"] == "VERIFIED" for item in review_payload["questions"])

        history = client.get(f"{sessions_url}?status=SUBMITTED")
        assert history.status_code == 200, history.text
        assert history.json()["pagination"]["returned"] == 1
        history_item = history.json()["items"][0]
        assert history_item["session_id"] == session_id
        assert history_item["mode"] == "MIXED"
        assert history_item["result"]["percentage"] == 37.5

        results = client.get(f"/api/v1/learners/{learner_id}/preparation-results")
        assert results.status_code == 200, results.text
        assert results.json()["pagination"]["returned"] == 1
        assert results.json()["items"][0]["result"]["correct_answers"] == 1

        summary = client.get(f"/api/v1/learners/{learner_id}/preparation-results/summary")
        assert summary.status_code == 200, summary.text
        assert summary.json()["completed_test_count"] == 1
        assert summary.json()["total_session_count"] == 1
        assert summary.json()["average_percentage"] == 37.5
        assert summary.json()["correct_answers"] == 1
        assert summary.json()["incorrect_answers"] == 1

        with connect_postgres(dsn) as connection:
            attempt = connection.execute(
                "SELECT COUNT(*), MAX(percentage) FROM learner_test_attempts WHERE learner_id = %s",
                (learner_id,),
            ).fetchone()
            outcomes = connection.execute(
                "SELECT COUNT(*), COUNT(*) FILTER (WHERE outcome = 'CORRECT') "
                "FROM learner_question_attempts WHERE learner_id = %s",
                (learner_id,),
            ).fetchone()
        assert attempt == (1, 37.5)
        assert outcomes == (2, 1)

        again = client.get(f"/api/v1/learners/{learner_id}/preparation-results")
        assert again.status_code == 200
        with connect_postgres(dsn) as connection:
            assert connection.execute(
                "SELECT COUNT(*) FROM learner_test_attempts WHERE learner_id = %s",
                (learner_id,),
            ).fetchone()[0] == 1
            assert connection.execute(
                "SELECT COUNT(*) FROM learner_question_attempts WHERE learner_id = %s",
                (learner_id,),
            ).fetchone()[0] == 2

        reloaded = client.get(f"{sessions_url}/{session_id}")
        assert reloaded.status_code == 200
        assert reloaded.json()["status"] == "SUBMITTED"
        assert reloaded.json()["answered_question_count"] == 2
        assert reloaded.json()["result"]["percentage"] == 37.5

        repeated_submit = client.post(f"{sessions_url}/{session_id}/submit")
        assert repeated_submit.status_code == 200
        assert repeated_submit.json()["result"] == result

        other_client = TestClient(create_postgres_app(
            dsn=dsn,
            learner_identity_provider=lambda _request: "phase634-other",
        ))
        forbidden = other_client.get(
            f"/api/v1/learners/phase634-other/preparation-sessions/{session_id}"
        )
        assert forbidden.status_code == 404
        forbidden_review = other_client.get(
            f"/api/v1/learners/phase634-other/preparation-sessions/{session_id}/answer-review"
        )
        assert forbidden_review.status_code == 404
    finally:
        with connect_postgres(dsn) as connection:
            connection.execute("DELETE FROM learner_test_attempts WHERE learner_id = %s", (learner_id,))
            connection.execute("DELETE FROM preparation_test_sessions WHERE learner_id = %s", (learner_id,))
            connection.execute("DELETE FROM preparation_test_requests WHERE learner_id = %s", (learner_id,))
            connection.execute("DELETE FROM generated_questions WHERE generated_question_id = ANY(%s)", (question_ids,))


def test_session_creation_requires_active_saved_request():
    dsn = database_url()
    apply_migrations(dsn)
    learner_id = f"phase634-empty-{uuid4().hex}"
    client = TestClient(create_postgres_app(
        dsn=dsn,
        learner_identity_provider=lambda _request: learner_id,
    ))
    response = client.post(f"/api/v1/learners/{learner_id}/preparation-sessions")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "NO_ACTIVE_PREPARATION_REQUEST"
