from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OneLinerVerificationStatus(str, Enum):
    DRAFT = "DRAFT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class QuestionBankTopic:
    """One existing canonical concept shown as a browsable topic/subtopic."""

    concept_id: str
    label: str
    subject: str
    topic: str | None
    subtopic: str | None
    verified_one_liner_count: int = 0

    def __post_init__(self) -> None:
        if not self.concept_id.strip() or not self.label.strip() or not self.subject.strip():
            raise ValueError("topic identity, label, and subject are required")
        if self.verified_one_liner_count < 0:
            raise ValueError("verified_one_liner_count must be non-negative")


@dataclass(frozen=True)
class TopicOneLinerQA:
    """Short topic-linked question and direct answer, not necessarily an MCQ."""

    one_liner_id: str
    concept_id: str
    question_text: str
    answer_text: str
    language_code: str = "hi"
    source_url: str | None = None
    source_evidence: str = ""
    verification_status: OneLinerVerificationStatus = OneLinerVerificationStatus.NEEDS_REVIEW
    importance_score: float = 0.5
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        for name in ("one_liner_id", "concept_id", "question_text", "answer_text", "language_code"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be a non-empty trimmed string")
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError("importance_score must be between 0 and 1")
        if self.source_url is not None and not self.source_url.startswith("https://"):
            raise ValueError("source_url must use HTTPS when supplied")
        if self.verification_status is OneLinerVerificationStatus.VERIFIED:
            if self.source_url is None or not self.source_evidence.strip() or self.reviewed_at is None:
                raise ValueError("verified one-liners require HTTPS source, evidence, and review time")
        for name in ("reviewed_at", "created_at", "updated_at"):
            value = getattr(self, name)
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError(f"{name} must be timezone-aware when supplied")

    @property
    def content_hash(self) -> str:
        normalized = " ".join(self.question_text.casefold().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


__all__ = [
    "OneLinerVerificationStatus",
    "QuestionBankTopic",
    "TopicOneLinerQA",
]
