from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.preparation_request import (
    PreparationRequestStatus,
    PreparationTestRequest,
    PreparationTestRequestRecord,
)
from ai_comp.domain.test_engine import TestSpecification


class InMemoryPreparationRequestRepository:
    """Small deterministic fake for testing HTTP lifecycle behavior without PostgreSQL."""

    def __init__(self):
        self.records = {}

    def save_active(self, request_id, request, *, now=None):
        timestamp = now or datetime.now(timezone.utc)
        for key, record in tuple(self.records.items()):
            if record.request.learner_id == request.learner_id and record.status is PreparationRequestStatus.ACTIVE:
                self.records[key] = replace(
                    record, status=PreparationRequestStatus.SUPERSEDED, updated_at=timestamp
                )
        record = PreparationTestRequestRecord(
            request_id=request_id,
            request=request,
            status=PreparationRequestStatus.ACTIVE,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.records[(request.learner_id, request_id)] = record
        return record

    def get_active_for_learner(self, learner_id):
        values = [
            record for (owner, _), record in self.records.items()
            if owner == learner_id and record.status is PreparationRequestStatus.ACTIVE
        ]
        return max(values, key=lambda item: (item.created_at, item.request_id), default=None)

    def list_for_learner(self, learner_id, *, limit=50, offset=0, status=None):
        values = [
            record for (owner, _), record in self.records.items()
            if owner == learner_id and (status is None or record.status is status)
        ]
        values.sort(key=lambda item: (item.created_at, item.request_id), reverse=True)
        return tuple(values[offset:offset + limit])

    def activate_for_learner(self, learner_id, request_id, *, now=None):
        key = (learner_id, request_id)
        record = self.records.get(key)
        if record is None or record.status is PreparationRequestStatus.CANCELLED:
            return record
        if record.status is PreparationRequestStatus.ACTIVE:
            return record
        timestamp = now or datetime.now(timezone.utc)
        for other_key, other in tuple(self.records.items()):
            if other.request.learner_id == learner_id and other.status is PreparationRequestStatus.ACTIVE:
                self.records[other_key] = replace(
                    other, status=PreparationRequestStatus.SUPERSEDED, updated_at=timestamp
                )
        changed = replace(record, status=PreparationRequestStatus.ACTIVE, updated_at=timestamp)
        self.records[key] = changed
        return changed

    def cancel_for_learner(self, learner_id, request_id, *, now=None):
        key = (learner_id, request_id)
        record = self.records.get(key)
        if record is None:
            return None
        if record.status is PreparationRequestStatus.CANCELLED:
            return record
        timestamp = now or datetime.now(timezone.utc)
        changed = replace(record, status=PreparationRequestStatus.CANCELLED, updated_at=timestamp)
        self.records[key] = changed
        return changed


def make_client(learner_id="learner-1", repository=None):
    repository = repository or InMemoryPreparationRequestRepository()
    app = create_app(
        learner_identity_provider=lambda _request: learner_id,
        preparation_test_request_repository=repository,
    )
    return TestClient(app), repository


def create_request(client, *, title):
    return client.post(
        "/api/v1/learners/learner-1/preparation-requests",
        json={"title": title, "question_count": 5, "duration_seconds": 600},
    )


def test_history_filters_and_pagination_are_bounded_and_learner_scoped():
    client, _ = make_client()
    first = create_request(client, title="First")
    second = create_request(client, title="Second")
    assert first.status_code == 201
    assert second.status_code == 201

    history = client.get("/api/v1/learners/learner-1/preparation-requests?limit=1&offset=0")
    assert history.status_code == 200
    assert history.json()["pagination"] == {
        "limit": 1, "offset": 0, "returned": 1, "has_more": True,
    }
    assert history.json()["items"][0]["request_id"] == second.json()["request_id"]

    old = client.get(
        "/api/v1/learners/learner-1/preparation-requests?status=SUPERSEDED"
    )
    assert old.status_code == 200
    assert [item["request_id"] for item in old.json()["items"]] == [first.json()["request_id"]]

    wrong_owner = client.get("/api/v1/learners/learner-2/preparation-requests")
    assert wrong_owner.status_code == 403
    invalid = client.get("/api/v1/learners/learner-1/preparation-requests?limit=101")
    assert invalid.status_code == 400
    invalid_status = client.get("/api/v1/learners/learner-1/preparation-requests?status=UNKNOWN")
    assert invalid_status.status_code == 400


def test_activation_supersedes_current_request_and_cancelled_request_is_terminal():
    client, _ = make_client()
    first = create_request(client, title="First")
    second = create_request(client, title="Second")
    first_id = first.json()["request_id"]
    second_id = second.json()["request_id"]
    prefix = "/api/v1/learners/learner-1/preparation-requests"

    activated = client.post(f"{prefix}/{first_id}/activate")
    assert activated.status_code == 200
    assert activated.json()["status"] == "ACTIVE"
    assert client.get(f"{prefix}/active").json()["request_id"] == first_id
    assert client.get(f"{prefix}?status=SUPERSEDED").json()["items"][0]["request_id"] == second_id

    cancelled = client.post(f"{prefix}/{first_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"
    repeated = client.post(f"{prefix}/{first_id}/cancel")
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "CANCELLED"
    refused = client.post(f"{prefix}/{first_id}/activate")
    assert refused.status_code == 409
    missing = client.post(f"{prefix}/missing-request/activate")
    assert missing.status_code == 404
