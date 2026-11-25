from __future__ import annotations

import base64
import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []
        self.closed = False

    def execute(self, query, params=()):
        self.calls.append((query, params))
        return _Result(self.rows)

    def close(self):
        self.closed = True


def _client(connection=None, identity="learner-1"):
    app = create_app(learner_identity_provider=lambda _request: identity)
    if connection is not None:
        app.state.question_bank_connection_factory = lambda: connection
    return TestClient(app)


def _row(
    one_liner_id="q-1",
    *,
    status="VERIFIED",
    updated_at=None,
):
    return (
        one_liner_id,
        "concept.river",
        "नदी किस दिशा में बहती है?",
        "दक्षिण-पश्चिम दिशा में।",
        "hi",
        "https://example.gov.in/source",
        "नदी अनुभाग, अनुच्छेद 2",
        status,
        0.9,
        updated_at or datetime(2026, 11, 23, 10, 0, tzinfo=timezone.utc),
    )


def test_content_delta_requires_authenticated_learner_before_database_access():
    response = TestClient(create_app()).get(
        "/api/v1/learners/learner-1/question-bank/content-delta"
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_content_delta_rejects_learner_scope_mismatch():
    connection = _Connection([_row()])
    response = _client(connection, identity="learner-2").get(
        "/api/v1/learners/learner-1/question-bank/content-delta"
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "LEARNER_SCOPE_MISMATCH"
    assert connection.calls == []
    assert connection.closed is False


def test_content_delta_validates_page_limit_and_cursor():
    client = _client(_Connection([]))

    too_large = client.get(
        "/api/v1/learners/learner-1/question-bank/content-delta?limit=101"
    )
    malformed = client.get(
        "/api/v1/learners/learner-1/question-bank/content-delta?cursor=not-a-cursor"
    )

    assert too_large.status_code == 400
    assert too_large.json()["error"]["code"] == "INVALID_LIMIT"
    assert malformed.status_code == 400
    assert malformed.json()["error"]["code"] == "INVALID_CONTENT_DELTA_CURSOR"


def test_content_delta_returns_bounded_records_with_status_and_timestamp():
    timestamp = datetime(2026, 11, 23, 10, 0, tzinfo=timezone.utc)
    connection = _Connection([
        _row("q-1", status="VERIFIED", updated_at=timestamp),
        _row("q-2", status="NEEDS_REVIEW", updated_at=timestamp),
        _row("q-3", status="REJECTED", updated_at=timestamp),
    ])
    response = _client(connection).get(
        "/api/v1/learners/learner-1/question-bank/content-delta?limit=2"
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["schema_version"] == 1
    assert payload["pagination"] == {
        "limit": 2,
        "returned": 2,
        "has_more": True,
        "next_cursor": payload["pagination"]["next_cursor"],
    }
    assert [item["one_liner_id"] for item in payload["items"]] == ["q-1", "q-2"]
    assert [item["verification_status"] for item in payload["items"]] == [
        "VERIFIED", "NEEDS_REVIEW"
    ]
    assert payload["items"][0]["updated_at"] == timestamp.isoformat()
    assert connection.closed is True

    query, params = connection.calls[0]
    assert "ORDER BY updated_at, one_liner_id" in query
    assert "verification_status" not in query
    assert params == (None, None, "", 3)


def test_content_delta_cursor_is_opaque_and_keyset_parameters_are_validated():
    source_timestamp = "2026-11-23T10:00:00+00:00"
    encoded = base64.urlsafe_b64encode(json.dumps({
        "v": 1,
        "updated_at": source_timestamp,
        "one_liner_id": "q-42",
    }).encode()).decode().rstrip("=")
    connection = _Connection([])
    response = _client(connection).get(
        "/api/v1/learners/learner-1/question-bank/content-delta",
        params={"cursor": encoded, "limit": 50},
    )

    assert response.status_code == 200, response.text
    assert response.json()["pagination"]["has_more"] is False
    assert connection.calls[0][1] == (
        source_timestamp,
        source_timestamp,
        "q-42",
        51,
    )
    assert connection.closed is True


def test_content_delta_overlaps_last_timestamp_on_final_page():
    timestamp = datetime(2026, 11, 23, 10, 0, tzinfo=timezone.utc)
    connection = _Connection([_row("q-9", updated_at=timestamp)])
    payload = _client(connection).get(
        "/api/v1/learners/learner-1/question-bank/content-delta"
    ).json()

    encoded = payload["pagination"]["next_cursor"]
    padded = encoded + ("=" * (-len(encoded) % 4))
    cursor = json.loads(base64.urlsafe_b64decode(padded))
    assert cursor["updated_at"] == "2026-11-23T09:59:59.999999+00:00"
    assert cursor["one_liner_id"] == ""


def test_content_delta_fails_closed_when_database_is_not_configured():
    response = _client().get(
        "/api/v1/learners/learner-1/question-bank/content-delta"
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUESTION_BANK_NOT_CONFIGURED"


def test_content_delta_invalid_database_timestamp_returns_safe_error_and_closes():
    invalid_row = list(_row())
    invalid_row[-1] = "2026-11-23T10:00:00"
    connection = _Connection([tuple(invalid_row)])
    response = _client(connection).get(
        "/api/v1/learners/learner-1/question-bank/content-delta"
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUESTION_BANK_CONTENT_DELTA_UNAVAILABLE"
    assert connection.closed is True
