from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app
from ai_comp.api.preparation_client_contract import (
    APIErrorResponse,
    AdaptivePreparationRecommendationResponse,
    CurrentQuestionResponse,
    PreparationTestRequestResponse,
    PreparationTestSessionResponse,
)
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.preparation_request import (
    PreparationRequestStatus,
    PreparationTestRequestRecord,
)


def analytics_report(learner_id: str = "client-learner") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "learner_id": learner_id,
        "generated_at": "2026-10-10T00:00:00+00:00",
        "summary": {
            "completed_test_count": 2,
            "total_questions": 4,
            "attempted_questions": 4,
            "correct_answers": 1,
            "incorrect_answers": 3,
            "unattempted_questions": 0,
            "average_percentage": 25.0,
            "latest_percentage": 25.0,
            "overall_accuracy": 0.25,
            "overall_accuracy_percentage": 25.0,
            "concept_count": 1,
            "weak_topic_count": 1,
            "revision_candidate_count": 1,
            "repeated_concept_alert_count": 0,
            "question_outcome_count": 4,
        },
        "topic_performance": [{
            "concept_id": "geography",
            "performance": "WEAK",
            "trend": "DECLINING",
            "priority_score": 0.9,
        }],
        "weak_topics": [{
            "concept_id": "geography",
            "performance": "WEAK",
            "trend": "DECLINING",
            "priority_score": 0.9,
        }],
        "revision_candidates": [{
            "question_id": "question-missed",
            "concept_ids": ["geography"],
            "priority_score": 1.0,
            "mistake_count": 2,
            "mistake_streak": 2,
            "last_incorrect_at": "2026-10-09T00:00:00+00:00",
        }],
        "repeated_concept_alerts": [],
        "limits": {
            "revision_candidates_returned": 1,
            "repeated_concept_alerts_returned": 0,
            "per_list_limit": 50,
        },
    }


class FakeAnalyticsProvider:
    def build_report(self, learner_id: str):
        return analytics_report(learner_id)


class FakeQuestionPool:
    def count_eligible_questions(self, concept_ids):
        assert tuple(concept_ids) == ("geography",)
        return 4


class FakeRequestRepository:
    def __init__(self):
        self.record = None

    def save_active(self, request_id, request):
        now = datetime(2026, 10, 10, tzinfo=timezone.utc)
        self.record = PreparationTestRequestRecord(
            request_id=request_id,
            request=request,
            status=PreparationRequestStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        return self.record

    def get_active_for_learner(self, learner_id):
        if self.record is None or self.record.request.learner_id != learner_id:
            return None
        return self.record


def make_client(identity: str = "client-learner"):
    requests = FakeRequestRepository()
    app = create_app(
        learner_identity_provider=lambda _request: identity,
        completed_test_analytics_provider=FakeAnalyticsProvider(),
        preparation_context_provider=FakeQuestionPool(),
        preparation_test_request_repository=requests,
    )
    return TestClient(app), requests


def test_openapi_publishes_response_schemas_for_adaptive_preparation_journey():
    client = TestClient(create_app())
    openapi = client.get("/openapi.json").json()
    paths = openapi["paths"]

    expected = {
        "/api/v1/learners/{learner_id}/preparation-recommendations": ("post", "201", "AdaptivePreparationRecommendationResponse"),
        "/api/v1/learners/{learner_id}/preparation-requests/active": ("get", "200", "PreparationTestRequestResponse"),
        "/api/v1/learners/{learner_id}/preparation-sessions": ("post", "201", "PreparationTestSessionResponse"),
        "/api/v1/learners/{learner_id}/preparation-sessions/{session_id}/current-question": ("get", "200", "CurrentQuestionResponse"),
        "/api/v1/learners/{learner_id}/preparation-sessions/{session_id}/submit": ("post", "200", "SubmittedTestResponse"),
        "/api/v1/learners/{learner_id}/preparation-sessions/{session_id}/answer-review": ("get", "200", "AnswerReviewResponse"),
        "/api/v1/learners/{learner_id}/preparation-results/analytics": ("get", "200", "CompletedTestAnalyticsResponse"),
    }
    for path, (method, status, schema_name) in expected.items():
        operation = paths[path][method]
        response_schema = operation["responses"][status]["content"]["application/json"]["schema"]
        assert response_schema["$ref"].endswith(f"/{schema_name}")

    assert "APIErrorResponse" in openapi["components"]["schemas"]
    assert "AdaptivePreparationRecommendationResponse" in openapi["components"]["schemas"]


def test_recommendation_and_saved_request_match_documented_client_models():
    client, repository = make_client()
    response = client.post(
        "/api/v1/learners/client-learner/preparation-recommendations",
        json={"question_count": 10, "duration_seconds": 900, "max_concepts": 4},
    )

    assert response.status_code == 201, response.text
    parsed = AdaptivePreparationRecommendationResponse.model_validate(response.json())
    assert parsed.status == "ACTIVE"
    assert parsed.mode == PersonalizedPreparationMode.ADAPTIVE.value
    assert parsed.recommendation.question_count_adjusted is True
    assert parsed.recommendation.effective_question_count == 4
    assert parsed.recommendation.focus_concept_ids == ["geography"]

    active = client.get(
        "/api/v1/learners/client-learner/preparation-requests/active"
    )
    assert active.status_code == 200, active.text
    saved = PreparationTestRequestResponse.model_validate(active.json())
    assert saved.request_id == repository.record.request_id
    assert saved.mode == "ADAPTIVE"


def test_common_error_response_is_stable_and_model_validated():
    client = TestClient(create_app())
    response = client.get(
        "/api/v1/learners/client-learner/preparation-results/analytics"
    )

    assert response.status_code == 401
    error = APIErrorResponse.model_validate(response.json())
    assert error.error.code == "AUTHENTICATION_REQUIRED"
    assert error.error.message


def test_session_contract_can_represent_saved_state_without_answer_key():
    payload = {
        "session_id": "session-1",
        "test_id": "test-1",
        "status": "IN_PROGRESS",
        "question_count": 1,
        "question_ids": ["question-1"],
        "current_question_number": 1,
        "answered_question_count": 0,
        "review_question_count": 0,
        "review_question_ids": [],
        "started_at": 1.0,
        "deadline_at": 301.0,
        "submitted_at": None,
        "result": None,
        "remaining_seconds": 300.0,
        "preparation_request_id": "request-1",
        "mode": "MIXED",
        "focus_concept_ids": ["geography"],
        "revision_question_ids": ["question-old-mistake"],
    }
    parsed = PreparationTestSessionResponse.model_validate(payload)
    assert parsed.mode == "MIXED"
    assert parsed.remaining_seconds == 300.0
    assert not hasattr(parsed, "correct_option_key")

    question = CurrentQuestionResponse.model_validate({
        "session_id": "session-1",
        "question_number": 1,
        "question_count": 1,
        "question_id": "question-1",
        "stem": "Choose the correct option",
        "options": [{"key": "A", "text": "One"}, {"key": "B", "text": "Two"}],
        "selected_option_key": "B",
        "review_marked": False,
        "remaining_seconds": 298.0,
    })
    assert question.options[0].key == "A"
    assert question.selected_option_key == "B"
    assert "correct_option_key" not in question.model_dump()
