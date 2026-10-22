from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from ai_comp.database.postgres_topic_question_bank import PostgresTopicQuestionBankRepository
from ai_comp.domain.topic_question_bank import (
    OneLinerVerificationStatus,
    QuestionBankTopic,
    TopicOneLinerQA,
)


def test_topic_requires_a_stable_concept_identity() -> None:
    with pytest.raises(ValueError, match="topic identity"):
        QuestionBankTopic(
            concept_id="",
            label="Rivers",
            subject="Rajasthan Geography",
            topic="Rivers",
            subtopic=None,
        )


def test_verified_one_liner_requires_source_evidence_and_review_time() -> None:
    with pytest.raises(ValueError, match="require HTTPS source"):
        TopicOneLinerQA(
            one_liner_id="ol-1",
            concept_id="concept-rivers",
            question_text="Which river is known for flowing west in Rajasthan?",
            answer_text="Luni River",
            verification_status=OneLinerVerificationStatus.VERIFIED,
        )


def test_one_liner_content_hash_normalizes_whitespace_and_case() -> None:
    a = TopicOneLinerQA(
        one_liner_id="ol-1",
        concept_id="concept-rivers",
        question_text="What is the   longest river?",
        answer_text="River A",
    )
    b = TopicOneLinerQA(
        one_liner_id="ol-2",
        concept_id="concept-rivers",
        question_text="what is the longest river?",
        answer_text="River A",
    )
    assert a.content_hash == b.content_hash


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, *results):
        self._results = list(results)
        self.calls = []

    @contextmanager
    def transaction(self):
        yield

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if not self._results:
            raise AssertionError("unexpected database query")
        return _Rows(self._results.pop(0))


def test_subject_list_comes_from_existing_concept_taxonomy() -> None:
    connection = _Connection([("Rajasthan History", 12), ("Science", 8)])
    items = PostgresTopicQuestionBankRepository(connection).list_subjects(limit=50)

    assert items == (("Rajasthan History", 12), ("Science", 8))
    query, params = connection.calls[0]
    assert "FROM concepts" in query
    assert "GROUP BY btrim(subject)" in query
    assert params == (50, 0)


def test_topic_list_includes_verified_one_liner_count() -> None:
    connection = _Connection([
        ("concept-rivers", "Luni River", "Rajasthan Geography", "Rivers", "Luni", 4)
    ])
    items = PostgresTopicQuestionBankRepository(connection).list_topics(
        "Rajasthan Geography",
        limit=20,
        offset=0,
    )

    assert items == (
        QuestionBankTopic(
            concept_id="concept-rivers",
            label="Luni River",
            subject="Rajasthan Geography",
            topic="Rivers",
            subtopic="Luni",
            verified_one_liner_count=4,
        ),
    )
    assert connection.calls[0][1] == ("Rajasthan Geography", 20, 0)


def test_one_liner_read_defaults_to_verified_content_only() -> None:
    reviewed_at = datetime(2026, 10, 22, tzinfo=timezone.utc)
    connection = _Connection([
        (
            "ol-1",
            "concept-rivers",
            "Which river?",
            "Luni",
            "en",
            "https://example.gov.in/river-facts",
            "Official department fact sheet, heading: Rivers",
            "VERIFIED",
            0.9,
            reviewed_at,
            reviewed_at,
            reviewed_at,
        )
    ])
    items = PostgresTopicQuestionBankRepository(connection).list_one_liners(
        "concept-rivers",
        limit=10,
        offset=0,
    )

    assert len(items) == 1
    assert items[0].question_text == "Which river?"
    assert items[0].answer_text == "Luni"
    assert items[0].verification_status is OneLinerVerificationStatus.VERIFIED
    query, params = connection.calls[0]
    assert "verification_status = 'VERIFIED'" in query
    assert params == ("concept-rivers", 10, 0)


def test_invalid_pagination_is_rejected_before_query() -> None:
    connection = _Connection()
    with pytest.raises(ValueError, match="limit"):
        PostgresTopicQuestionBankRepository(connection).list_subjects(limit=0)
    assert connection.calls == []
