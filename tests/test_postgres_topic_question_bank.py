from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime, timezone

from ai_comp.database.postgres_topic_question_bank import PostgresTopicQuestionBankRepository
from ai_comp.domain.topic_question_bank import OneLinerVerificationStatus, TopicOneLinerQA


class _Cursor:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _RejectedDuplicateConnection:
    def __init__(self, item: TopicOneLinerQA):
        now = datetime.now(timezone.utc)
        self.item = item
        self.calls = []
        self.row = (
            "existing-rejected-id",
            item.concept_id,
            item.question_text,
            item.answer_text,
            item.language_code,
            item.source_url,
            item.source_evidence,
            "NEEDS_REVIEW",
            item.importance_score,
            None,
            now,
            now,
        )

    def transaction(self):
        return nullcontext(self)

    def execute(self, query, params):
        self.calls.append((query, params))
        return _Cursor(self.row)


def test_resubmitting_rejected_duplicate_updates_evidence_and_returns_to_review() -> None:
    item = TopicOneLinerQA(
        one_liner_id="new-id-is-canonicalized",
        concept_id="catalog.rajasthan_geography_rivers_and_drainage_luni_river",
        question_text="लूणी नदी किस दिशा में बहती है?",
        answer_text="दक्षिण-पश्चिम दिशा में।",
        language_code="hi",
        source_url="https://environment.rajasthan.gov.in/updated-source.html",
        source_evidence="Updated official source, relevant river paragraph.",
        verification_status=OneLinerVerificationStatus.NEEDS_REVIEW,
        importance_score=0.8,
    )
    connection = _RejectedDuplicateConnection(item)

    saved = PostgresTopicQuestionBankRepository(connection).save_one_liner(item)

    assert saved.one_liner_id == "existing-rejected-id"
    assert saved.verification_status is OneLinerVerificationStatus.NEEDS_REVIEW
    assert saved.source_url == item.source_url
    assert saved.source_evidence == item.source_evidence
    assert saved.reviewed_at is None
    query, params = connection.calls[0]
    assert "ON CONFLICT (concept_id, language_code, content_hash) DO UPDATE" in query
    assert "existing.verification_status = 'REJECTED'" in query
    assert "reviewed_by = CASE" in query
    assert "review_note = CASE" in query
    assert "source_checked_at = CASE" in query
    assert params[0] == "new-id-is-canonicalized"
    assert params[7] == "NEEDS_REVIEW"
