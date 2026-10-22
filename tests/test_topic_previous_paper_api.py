from __future__ import annotations

from fastapi.testclient import TestClient

from ai_comp.api.app import create_app


class _Cursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []
        self.closed = False

    def execute(self, query, params):
        self.calls.append((query, params))
        return _Cursor(self.rows)

    def close(self):
        self.closed = True


def _history_row(*, total_count=3):
    return (
        "question-history-1",
        "राजस्थान की पश्चिमवाहिनी नदी कौनसी है?",
        [
            {"key": "A", "text": "लूणी"},
            {"key": "B", "text": "बनास"},
            {"key": "C", "text": "चंबल"},
            {"key": "D", "text": "माही"},
        ],
        "A",
        "RAJ_EXAM",
        "Rajasthan recruitment exam",
        2024,
        "MORNING",
        12,
        "https://official.example/paper.pdf",
        "https://official.example/answer-key.pdf",
        ["catalog.rajasthan-geography.rivers"],
        2,
        total_count,
    )


def _client(connection, identity="learner-1"):
    app = create_app(learner_identity_provider=lambda _request: identity)
    app.state.question_bank_connection_factory = lambda: connection
    return TestClient(app)


def test_previous_paper_api_filters_exam_year_shift_and_reports_topic_count():
    connection = _Connection([_history_row(total_count=3)])
    client = _client(connection)

    response = client.get(
        "/api/v1/learners/learner-1/question-bank/previous-papers",
        params={
            "concept_id": "catalog.rajasthan-geography.rivers",
            "subject_id": "Rajasthan Geography",
            "exam_id": "RAJ_EXAM",
            "exam_year": 2024,
            "exam_shift": "MORNING",
            "limit": 1,
            "offset": 0,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["exam_year"] == 2024
    assert item["exam_shift"] == "MORNING"
    assert item["correct_option_key"] == "A"
    assert item["source_url"] == "https://official.example/paper.pdf"
    assert item["answer_key_source_url"] == "https://official.example/answer-key.pdf"
    assert item["verified_appearance_count"] == 2
    assert payload["pagination"] == {
        "limit": 1,
        "offset": 0,
        "returned": 1,
        "total_count": 3,
        "has_more": True,
    }
    query, params = connection.calls[0]
    assert "pair.pair_status = 'MATCHED'" in query
    assert "qv.evidence_type = 'OFFICIAL_PAPER'" in query
    assert "kv.evidence_type = 'OFFICIAL_ANSWER_KEY'" in query
    assert params == (
        "Rajasthan Geography", "Rajasthan Geography",
        "RAJ_EXAM", "RAJ_EXAM",
        2024, 2024,
        "MORNING", "MORNING",
        ["catalog.rajasthan-geography.rivers"],
        ["catalog.rajasthan-geography.rivers"],
        1, 0,
    )
    assert connection.closed


def test_previous_paper_api_rejects_invalid_year_before_database_access():
    connection = _Connection([])
    client = _client(connection)

    response = client.get(
        "/api/v1/learners/learner-1/question-bank/previous-papers",
        params={"concept_id": "topic-1", "exam_year": 1800},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_EXAM_YEAR"
    assert connection.calls == []
    assert not connection.closed


def test_previous_paper_api_enforces_learner_scope_before_database_access():
    connection = _Connection([])
    client = _client(connection, identity="learner-2")

    response = client.get(
        "/api/v1/learners/learner-1/question-bank/previous-papers",
        params={"concept_id": "topic-1"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "LEARNER_SCOPE_MISMATCH"
    assert connection.calls == []
