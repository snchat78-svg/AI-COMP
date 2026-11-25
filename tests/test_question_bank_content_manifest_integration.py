from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_comp.api.app import create_postgres_app
from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner


pytestmark = pytest.mark.integration


def test_question_bank_content_manifest_executes_against_postgres():
    dsn = os.getenv("AI_COMP_DATABASE_URL", "").strip()
    if not dsn:
        pytest.skip("AI_COMP_DATABASE_URL is not configured")

    migrations_dir = Path(__file__).resolve().parents[1] / "database" / "migrations"
    with connect_postgres(dsn) as connection:
        MigrationRunner(migrations_dir).apply(connection)

    app = create_postgres_app(
        dsn=dsn,
        learner_identity_provider=lambda _request: "manifest-integration-learner",
    )
    client = TestClient(app)
    response = client.get(
        "/api/v1/learners/manifest-integration-learner/question-bank/content-manifest"
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["schema_version"] == 1
    assert len(payload["revision"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["revision"])
    assert payload["topic_count"] >= 0
    assert payload["verified_one_liner_count"] >= 0
    assert payload["review_pending_one_liner_count"] >= 0


def test_question_bank_content_delta_executes_against_postgres():
    dsn = os.getenv("AI_COMP_DATABASE_URL", "").strip()
    if not dsn:
        pytest.skip("AI_COMP_DATABASE_URL is not configured")

    migrations_dir = Path(__file__).resolve().parents[1] / "database" / "migrations"
    with connect_postgres(dsn) as connection:
        MigrationRunner(migrations_dir).apply(connection)

    app = create_postgres_app(
        dsn=dsn,
        learner_identity_provider=lambda _request: "delta-integration-learner",
    )
    client = TestClient(app)
    response = client.get(
        "/api/v1/learners/delta-integration-learner/question-bank/content-delta",
        params={"limit": 1},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["schema_version"] == 1
    assert isinstance(payload["items"], list)
    assert len(payload["items"]) <= 1
    assert payload["pagination"]["limit"] == 1
    assert payload["pagination"]["returned"] == len(payload["items"])
    assert isinstance(payload["pagination"]["has_more"], bool)
    if payload["items"]:
        item = payload["items"][0]
        assert item["one_liner_id"]
        assert item["verification_status"]
        assert item["updated_at"]
        if item["verification_status"] == "VERIFIED":
            assert item["question_text"]
            assert item["answer_text"]
        else:
            assert "question_text" not in item
            assert "answer_text" not in item
