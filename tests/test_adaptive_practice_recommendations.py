from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
import pytest

from ai_comp.api.app import create_app
from ai_comp.application.adaptive_practice_recommendations import (
    AdaptivePracticeRecommendationPlanner,
    NoAdaptivePracticeSignal,
)
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.preparation_request import (
    PreparationRequestStatus,
    PreparationTestRequestRecord,
)
from ai_comp.domain.test_engine import TestSpecification


def analytics_report(learner_id: str = "learner-1") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "learner_id": learner_id,
        "generated_at": "2026-10-10T00:00:00+00:00",
        "summary": {
            "completed_test_count": 4,
            "weak_topic_count": 1,
            "repeated_concept_alert_count": 1,
        },
        "topic_performance": [
            {
                "concept_id": "geography",
                "performance": "WEAK",
                "trend": "DECLINING",
                "priority_score": 0.95,
            },
            {
                "concept_id": "history",
                "performance": "AVERAGE",
                "trend": "STABLE",
                "priority_score": 0.75,
            },
            {
                "concept_id": "polity",
                "performance": "STRONG",
                "trend": "STABLE",
                "priority_score": 0.1,
            },
        ],
        "weak_topics": [
            {
                "concept_id": "geography",
                "performance": "WEAK",
                "trend": "DECLINING",
                "priority_score": 0.95,
            }
        ],
        "repeated_concept_alerts": [
            {"concept_id": "history", "priority_score": 0.75}
        ],
        "revision_candidates": [
            {
                "question_id": "old-geography-mistake",
                "concept_ids": ["geography"],
                "priority_score": 1.0,
                "mistake_count": 3,
                "mistake_streak": 2,
                "last_incorrect_at": "2026-10-09T00:00:00+00:00",
            }
        ],
    }


def test_planner_prioritizes_weak_topics_then_alerts_and_keeps_revision_candidates():
    plan = AdaptivePracticeRecommendationPlanner().plan(
        "learner-1", analytics_report(), max_concepts=3
    )

    assert plan.concept_ids == ("geography", "history")
    reasons = dict(plan.focus_reasons)
    assert reasons["geography"] == ("WEAK_TOPIC", "DECLINING_TREND", "PREVIOUS_MISTAKE")
    assert reasons["history"] == ("REPEATED_CONCEPT", "HIGH_PRIORITY_TOPIC")
    assert plan.revision_question_ids == ("old-geography-mistake",)
    assert plan.completed_test_count == 4


def test_planner_does_not_invent_focus_when_all_topics_are_strong():
    report = analytics_report()
    report["weak_topics"] = []
    report["repeated_concept_alerts"] = []
    report["revision_candidates"] = []
    report["topic_performance"] = [
        {"concept_id": "polity", "performance": "STRONG", "trend": "STABLE", "priority_score": 0.1}
    ]

    with pytest.raises(NoAdaptivePracticeSignal):
        AdaptivePracticeRecommendationPlanner().plan("learner-1", report)


def test_planner_rejects_analytics_for_another_learner():
    with pytest.raises(ValueError, match="belong"):
        AdaptivePracticeRecommendationPlanner().plan(
            "learner-2", analytics_report("learner-1")
        )


class FakeAnalyticsProvider:
    def __init__(self, report=None):
        self.report = analytics_report() if report is None else report
        self.calls = []

    def build_report(self, learner_id):
        self.calls.append(learner_id)
        return self.report


class FakeQuestionPool:
    def __init__(self, available=3):
        self.available = available
        self.calls = []

    def count_eligible_questions(self, concept_ids):
        self.calls.append(tuple(concept_ids))
        return self.available


class FakeRequestRepository:
    def __init__(self):
        self.saved = []

    def save_active(self, request_id, domain_request):
        self.saved.append((request_id, domain_request))
        now = datetime(2026, 10, 10, tzinfo=timezone.utc)
        return PreparationTestRequestRecord(
            request_id=request_id,
            request=domain_request,
            status=PreparationRequestStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )


def make_client(*, identity="learner-1", report=None, available=3):
    analytics = FakeAnalyticsProvider(report)
    pool = FakeQuestionPool(available)
    repository = FakeRequestRepository()
    app = create_app(
        learner_identity_provider=lambda _request: identity,
        completed_test_analytics_provider=analytics,
        preparation_context_provider=pool,
        preparation_test_request_repository=repository,
    )
    return TestClient(app), analytics, pool, repository


def test_recommendation_persists_adaptive_request_after_pool_check_and_caps_count():
    client, analytics, pool, repository = make_client(available=3)
    response = client.post(
        "/api/v1/learners/learner-1/preparation-recommendations",
        json={"question_count": 20, "duration_seconds": 900, "max_concepts": 8},
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["status"] == "ACTIVE"
    assert payload["mode"] == "ADAPTIVE"
    assert payload["question_count"] == 3
    assert payload["concept_ids"] == ["geography", "history"]
    assert payload["recommendation"]["effective_question_count"] == 3
    assert payload["recommendation"]["requested_question_count"] == 20
    assert payload["recommendation"]["question_count_adjusted"] is True
    assert payload["recommendation"]["revision_question_ids"] == ["old-geography-mistake"]
    assert pool.calls == [("geography", "history")]
    assert analytics.calls == ["learner-1"]
    assert len(repository.saved) == 1
    _, saved = repository.saved[0]
    assert saved.mode is PersonalizedPreparationMode.ADAPTIVE
    assert saved.specification.question_count == 3


def test_recommendation_with_no_signal_does_not_replace_existing_active_settings():
    report = analytics_report()
    report["weak_topics"] = []
    report["repeated_concept_alerts"] = []
    report["revision_candidates"] = []
    report["topic_performance"] = [
        {"concept_id": "polity", "performance": "STRONG", "trend": "STABLE", "priority_score": 0.1}
    ]
    client, _, pool, repository = make_client(report=report)

    response = client.post(
        "/api/v1/learners/learner-1/preparation-recommendations", json={}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "NO_ADAPTIVE_PRACTICE_SIGNAL"
    assert pool.calls == []
    assert repository.saved == []


def test_empty_eligible_pool_does_not_replace_existing_active_settings():
    client, _, _, repository = make_client(available=0)

    response = client.post(
        "/api/v1/learners/learner-1/preparation-recommendations", json={}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "NO_ELIGIBLE_ADAPTIVE_QUESTIONS"
    assert repository.saved == []


def test_recommendation_endpoint_enforces_learner_scope_before_reading_history():
    client, analytics, pool, repository = make_client(identity="learner-2")

    response = client.post(
        "/api/v1/learners/learner-1/preparation-recommendations", json={}
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "LEARNER_SCOPE_MISMATCH"
    assert analytics.calls == []
    assert pool.calls == []
    assert repository.saved == []


def test_recommendation_fails_closed_when_provider_wiring_is_missing():
    client = TestClient(create_app(
        learner_identity_provider=lambda _request: "learner-1"
    ))

    response = client.post(
        "/api/v1/learners/learner-1/preparation-recommendations", json={}
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ADAPTIVE_PRACTICE_NOT_CONFIGURED"
