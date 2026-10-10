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


def accepted_question(
    question_id: str, concept_id: str, additional_concept_ids: tuple[str, ...] = ()
) -> GeneratedMCQ:
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
        concept_ids=(concept_id, *additional_concept_ids),
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
    strong_concept_id = f"phase634-strong-{suffix}"
    weak_concept_id = f"phase634-weak-{suffix}"
    question_ids = [f"phase634-question-{suffix}-{index}" for index in range(1, 4)]
    client = TestClient(create_postgres_app(
        dsn=dsn,
        learner_identity_provider=lambda _request: learner_id,
    ))
    request_url = f"/api/v1/learners/{learner_id}/preparation-requests"
    sessions_url = f"/api/v1/learners/{learner_id}/preparation-sessions"

    with connect_postgres(dsn) as connection:
        question_repo = PostgresGeneratedQuestionRepository(connection)
        for index, question_id in enumerate(question_ids):
            additional_concepts = (
                (strong_concept_id,) if index == 0
                else (weak_concept_id,) if index == 1
                else ()
            )
            question_repo.save(
                accepted_question(question_id, concept_id, additional_concepts)
            )

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

        analytics = client.get(
            f"/api/v1/learners/{learner_id}/preparation-results/analytics"
        )
        assert analytics.status_code == 200, analytics.text
        analytics_payload = analytics.json()
        assert analytics_payload["schema_version"] == "1.0"
        assert analytics_payload["summary"]["completed_test_count"] == 1
        assert analytics_payload["summary"]["question_outcome_count"] == 2
        assert analytics_payload["summary"]["weak_topic_count"] == 1
        weak_topic = next(
            item for item in analytics_payload["weak_topics"]
            if item["concept_id"] == weak_concept_id
        )
        assert weak_topic["performance"] == "WEAK"
        assert weak_topic["accuracy_percentage"] == 0.0
        assert weak_topic["recommended_action"] == "REMEDIATE_AND_PRACTICE"
        assert any(
            item["concept_id"] == strong_concept_id and item["performance"] == "STRONG"
            for item in analytics_payload["topic_performance"]
        )
        assert analytics_payload["revision_candidates"]
        assert analytics_payload["revision_candidates"][0]["mistake_count"] >= 1

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
        forbidden_analytics = other_client.get(
            f"/api/v1/learners/{learner_id}/preparation-results/analytics"
        )
        assert forbidden_analytics.status_code == 403
        assert forbidden_analytics.json()["error"]["code"] == "LEARNER_SCOPE_MISMATCH"
    finally:
        with connect_postgres(dsn) as connection:
            connection.execute("DELETE FROM learner_test_attempts WHERE learner_id = %s", (learner_id,))
            connection.execute("DELETE FROM preparation_test_sessions WHERE learner_id = %s", (learner_id,))
            connection.execute("DELETE FROM preparation_test_requests WHERE learner_id = %s", (learner_id,))
            connection.execute("DELETE FROM generated_questions WHERE generated_question_id = ANY(%s)", (question_ids,))



def test_adaptive_preparation_loop_uses_completed_result_to_build_next_session():
    """Prove submitted outcomes drive the next saved adaptive test using PostgreSQL."""
    dsn = database_url()
    apply_migrations(dsn)
    suffix = uuid4().hex
    learner_id = f"phase639-learner-{suffix}"
    concept_id = f"phase639-weak-topic-{suffix}"
    question_ids = [f"phase639-question-{suffix}-{index}" for index in range(1, 4)]
    client = TestClient(create_postgres_app(
        dsn=dsn,
        learner_identity_provider=lambda _request: learner_id,
    ))
    requests_url = f"/api/v1/learners/{learner_id}/preparation-requests"
    recommendations_url = f"/api/v1/learners/{learner_id}/preparation-recommendations"
    sessions_url = f"/api/v1/learners/{learner_id}/preparation-sessions"
    analytics_url = f"/api/v1/learners/{learner_id}/preparation-results/analytics"

    with connect_postgres(dsn) as connection:
        question_repo = PostgresGeneratedQuestionRepository(connection)
        for question_id in question_ids:
            question_repo.save(accepted_question(question_id, concept_id))

    try:
        # Create and submit a baseline test with two verified wrong answers.
        saved_request = client.post(requests_url, json={
            "title": "Phase 6.39 baseline diagnostic",
            "question_count": 2,
            "duration_seconds": 900,
            "mode": "MIXED",
            "concept_ids": [concept_id],
        })
        assert saved_request.status_code == 201, saved_request.text

        baseline_session = client.post(sessions_url)
        assert baseline_session.status_code == 201, baseline_session.text
        baseline_session_id = baseline_session.json()["session_id"]
        started = client.post(f"{sessions_url}/{baseline_session_id}/start")
        assert started.status_code == 200, started.text

        for question_number in range(2):
            current = client.get(f"{sessions_url}/{baseline_session_id}/current-question")
            assert current.status_code == 200, current.text
            answered = client.post(
                f"{sessions_url}/{baseline_session_id}/answer",
                json={"option_key": "B"},
            )
            assert answered.status_code == 200, answered.text
            if question_number == 0:
                moved = client.post(f"{sessions_url}/{baseline_session_id}/next")
                assert moved.status_code == 200, moved.text

        baseline_result = client.post(f"{sessions_url}/{baseline_session_id}/submit")
        assert baseline_result.status_code == 200, baseline_result.text
        assert baseline_result.json()["result"]["incorrect_answers"] == 2

        before = client.get(analytics_url)
        assert before.status_code == 200, before.text
        before_analytics = before.json()
        assert before_analytics["summary"]["completed_test_count"] == 1
        assert before_analytics["summary"]["question_outcome_count"] == 2
        assert any(
            topic["concept_id"] == concept_id and topic["performance"] == "WEAK"
            for topic in before_analytics["weak_topics"]
        )
        assert before_analytics["revision_candidates"]

        # The recommendation must be derived from that persisted history, then
        # become the active request used by the ordinary session-creation route.
        recommendation_response = client.post(recommendations_url, json={
            "question_count": 1,
            "duration_seconds": 300,
            "max_concepts": 4,
        })
        assert recommendation_response.status_code == 201, recommendation_response.text
        recommendation = recommendation_response.json()
        assert recommendation["status"] == "ACTIVE"
        assert recommendation["mode"] == "ADAPTIVE"
        assert recommendation["question_count"] == 1
        assert concept_id in recommendation["recommendation"]["focus_concept_ids"]
        assert recommendation["recommendation"]["revision_question_ids"]
        assert recommendation["recommendation"]["source"] == "PERSISTED_LEARNER_TEST_HISTORY"

        active_request = client.get(
            f"/api/v1/learners/{learner_id}/preparation-requests/active"
        )
        assert active_request.status_code == 200, active_request.text
        assert active_request.json()["request_id"] == recommendation["request_id"]
        assert active_request.json()["mode"] == "ADAPTIVE"

        next_session = client.post(sessions_url)
        assert next_session.status_code == 201, next_session.text
        next_session_payload = next_session.json()
        next_session_id = next_session_payload["session_id"]
        assert next_session_payload["preparation_request_id"] == recommendation["request_id"]
        # The stored request remains ADAPTIVE; the canonical composer reports
        # MIXED for this session because it selected both mistake revision and
        # weak-topic focus from the persisted learner history.
        assert next_session_payload["mode"] == "MIXED"
        assert next_session_payload["focus_concept_ids"] == [concept_id]
        assert next_session_payload["revision_question_ids"]
        assert next_session_payload["question_count"] == 1

        started_next = client.post(f"{sessions_url}/{next_session_id}/start")
        assert started_next.status_code == 200, started_next.text
        next_question = client.get(f"{sessions_url}/{next_session_id}/current-question")
        assert next_question.status_code == 200, next_question.text
        # Option A is the verified correct answer for these integration fixtures.
        next_answer = client.post(
            f"{sessions_url}/{next_session_id}/answer",
            json={"option_key": "A"},
        )
        assert next_answer.status_code == 200, next_answer.text
        next_result = client.post(f"{sessions_url}/{next_session_id}/submit")
        assert next_result.status_code == 200, next_result.text
        assert next_result.json()["result"]["correct_answers"] == 1
        assert next_result.json()["result"]["attempted_questions"] == 1

        after = client.get(analytics_url)
        assert after.status_code == 200, after.text
        after_analytics = after.json()
        assert after_analytics["summary"]["completed_test_count"] == 2
        assert after_analytics["summary"]["question_outcome_count"] == 3

        with connect_postgres(dsn) as connection:
            attempts = connection.execute(
                "SELECT COUNT(*) FROM learner_test_attempts WHERE learner_id = %s",
                (learner_id,),
            ).fetchone()[0]
            outcomes = connection.execute(
                "SELECT COUNT(*) FROM learner_question_attempts WHERE learner_id = %s",
                (learner_id,),
            ).fetchone()[0]
        assert attempts == 2
        assert outcomes == 3

        # A different authenticated learner cannot request recommendations
        # against this learner's saved analytics.
        other_client = TestClient(create_postgres_app(
            dsn=dsn,
            learner_identity_provider=lambda _request: "phase639-other",
        ))
        forbidden = other_client.post(recommendations_url, json={})
        assert forbidden.status_code == 403
        assert forbidden.json()["error"]["code"] == "LEARNER_SCOPE_MISMATCH"
    finally:
        with connect_postgres(dsn) as connection:
            connection.execute(
                "DELETE FROM learner_test_attempts WHERE learner_id = %s",
                (learner_id,),
            )
            connection.execute(
                "DELETE FROM preparation_test_sessions WHERE learner_id = %s",
                (learner_id,),
            )
            connection.execute(
                "DELETE FROM preparation_test_requests WHERE learner_id = %s",
                (learner_id,),
            )
            connection.execute(
                "DELETE FROM generated_questions WHERE generated_question_id = ANY(%s)",
                (question_ids,),
            )

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
