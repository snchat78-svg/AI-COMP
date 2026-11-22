from __future__ import annotations

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


class _Result:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self, row):
        self.row = row
        self.calls = []
        self.closed = False

    def execute(self, query, params=()):
        self.calls.append((query, params))
        return _Result(self.row)

    def close(self):
        self.closed = True


def _client(connection=None, identity="learner-1"):
    app = create_app(learner_identity_provider=lambda _request: identity)
    if connection is not None:
        app.state.question_bank_connection_factory = lambda: connection
    return TestClient(app)


def _row(*, topic_count=34, verified_count=0, pending_count=368,
         catalogue_revision="a" * 32, published_revision="b" * 32):
    return (
        topic_count,
        verified_count,
        pending_count,
        catalogue_revision,
        published_revision,
    )


def test_manifest_requires_authenticated_learner_before_database_access():
    app = create_app()
    client = TestClient(app)

    response = client.get(
        "/api/v1/learners/learner-1/question-bank/content-manifest"
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_manifest_rejects_learner_scope_mismatch():
    connection = _Connection(_row())
    response = _client(connection, identity="learner-2").get(
        "/api/v1/learners/learner-1/question-bank/content-manifest"
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "LEARNER_SCOPE_MISMATCH"
    assert connection.calls == []
    assert connection.closed is False


def test_manifest_fails_closed_when_question_bank_database_is_not_configured():
    response = _client().get(
        "/api/v1/learners/learner-1/question-bank/content-manifest"
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUESTION_BANK_NOT_CONFIGURED"


def test_manifest_returns_stable_revision_and_separate_status_counts():
    connection = _Connection(_row())
    response = _client(connection).get(
        "/api/v1/learners/learner-1/question-bank/content-manifest"
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["schema_version"] == 1
    assert len(payload["revision"]) == 64
    assert payload["revision"].islower()
    assert payload["catalogue_revision"] == "a" * 32
    assert payload["published_questions_revision"] == "b" * 32
    assert payload["topic_count"] == 34
    assert payload["verified_one_liner_count"] == 0
    assert payload["review_pending_one_liner_count"] == 368
    assert connection.closed is True

    query, params = connection.calls[0]
    assert params == ()
    assert "FROM concepts" in query
    assert "FROM question_bank_one_liners" in query
    assert "verification_status = 'VERIFIED'" in query
    assert "verification_status IN ('DRAFT', 'NEEDS_REVIEW')" in query


def test_manifest_revision_changes_when_published_question_revision_changes():
    first = _client(_Connection(_row(published_revision="b" * 32))).get(
        "/api/v1/learners/learner-1/question-bank/content-manifest"
    ).json()
    second = _client(_Connection(_row(published_revision="c" * 32))).get(
        "/api/v1/learners/learner-1/question-bank/content-manifest"
    ).json()

    assert first["revision"] != second["revision"]


def test_pending_draft_count_does_not_change_published_content_revision():
    with_pending = _client(_Connection(_row(pending_count=368))).get(
        "/api/v1/learners/learner-1/question-bank/content-manifest"
    ).json()
    without_pending = _client(_Connection(_row(pending_count=0))).get(
        "/api/v1/learners/learner-1/question-bank/content-manifest"
    ).json()

    assert with_pending["review_pending_one_liner_count"] == 368
    assert without_pending["review_pending_one_liner_count"] == 0
    assert with_pending["revision"] == without_pending["revision"]


def test_manifest_rejects_invalid_database_digest():
    connection = _Connection(_row(catalogue_revision="not-a-digest"))
    response = _client(connection).get(
        "/api/v1/learners/learner-1/question-bank/content-manifest"
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "QUESTION_BANK_CONTENT_MANIFEST_UNAVAILABLE"
    assert connection.closed is True
