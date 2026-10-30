from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit
from uuid import uuid4

from ai_comp.domain.topic_question_bank import (
    OneLinerVerificationStatus,
    TopicOneLinerQA,
)


@dataclass(frozen=True)
class OneLinerDraft:
    """Model-proposed direct Q&A plus exact source excerpts for human review."""

    question_text: str
    answer_text: str
    evidence_quote: str
    answer_evidence_quote: str
    importance_score: float

    def __post_init__(self) -> None:
        for name in (
            "question_text",
            "answer_text",
            "evidence_quote",
            "answer_evidence_quote",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be non-empty trimmed text")
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError("importance_score must be between 0 and 1")


class OneLinerCandidateProvider(Protocol):
    def generate(
        self,
        *,
        source_text: str,
        concept_label: str,
        language_code: str,
        requested_count: int,
    ) -> Sequence[OneLinerDraft]: ...


class OneLinerCandidateRepository(Protocol):
    def save_one_liner(self, item: TopicOneLinerQA) -> TopicOneLinerQA: ...


@dataclass(frozen=True)
class OneLinerCandidateGenerationResult:
    saved_items: tuple[TopicOneLinerQA, ...]
    duplicate_count: int
    rejected_count: int
    warnings: tuple[str, ...]

    @property
    def saved_count(self) -> int:
        return len(self.saved_items)


class OneLinerCandidateGenerationService:
    """Create source-grounded Q&A candidates; never self-certify model output."""

    def __init__(
        self,
        provider: OneLinerCandidateProvider,
        repository: OneLinerCandidateRepository,
        *,
        minimum_importance_score: float = 0.60,
        maximum_source_characters: int = 120_000,
    ) -> None:
        if not 0.0 <= minimum_importance_score <= 1.0:
            raise ValueError("minimum_importance_score must be between 0 and 1")
        if maximum_source_characters < 1:
            raise ValueError("maximum_source_characters must be positive")
        self.provider = provider
        self.repository = repository
        self.minimum_importance_score = minimum_importance_score
        self.maximum_source_characters = maximum_source_characters

    def generate(
        self,
        *,
        concept_id: str,
        concept_label: str,
        source_url: str,
        source_locator: str,
        source_text: str,
        language_code: str = "hi",
        requested_count: int = 20,
    ) -> OneLinerCandidateGenerationResult:
        self._validate_request(
            concept_id=concept_id,
            concept_label=concept_label,
            source_url=source_url,
            source_locator=source_locator,
            source_text=source_text,
            language_code=language_code,
            requested_count=requested_count,
        )
        drafts = tuple(
            self.provider.generate(
                source_text=source_text,
                concept_label=concept_label,
                language_code=language_code,
                requested_count=requested_count,
            )
        )
        valid_drafts: list[OneLinerDraft] = []
        invalid_draft_count = 0
        for draft in drafts:
            if isinstance(draft, OneLinerDraft):
                valid_drafts.append(draft)
            else:
                invalid_draft_count += 1

        ordered = sorted(
            valid_drafts,
            key=lambda item: (-item.importance_score, item.question_text.casefold()),
        )

        saved: list[TopicOneLinerQA] = []
        duplicate_count = 0
        rejected_count = invalid_draft_count
        warnings: list[str] = []
        if invalid_draft_count:
            warnings.append("One or more provider items had an invalid structured shape.")
        seen_hashes: set[str] = set()

        for draft in ordered:
            if len(saved) >= requested_count:
                break
            if draft.importance_score < self.minimum_importance_score:
                rejected_count += 1
                continue
            if (
                draft.evidence_quote not in source_text
                or draft.answer_evidence_quote not in source_text
                or draft.answer_evidence_quote not in draft.evidence_quote
            ):
                rejected_count += 1
                warnings.append("A candidate did not include exact, contiguous source evidence.")
                continue

            item = TopicOneLinerQA(
                one_liner_id=f"ai-ol-{uuid4().hex}",
                concept_id=concept_id,
                question_text=draft.question_text,
                answer_text=draft.answer_text,
                language_code=language_code,
                source_url=source_url,
                source_evidence=(
                    f"{source_locator} | supporting passage: {draft.evidence_quote} "
                    f"| answer evidence: {draft.answer_evidence_quote}"
                ),
                verification_status=OneLinerVerificationStatus.NEEDS_REVIEW,
                importance_score=draft.importance_score,
            )
            if item.content_hash in seen_hashes:
                duplicate_count += 1
                continue
            seen_hashes.add(item.content_hash)
            persisted = self.repository.save_one_liner(item)
            if persisted.one_liner_id != item.one_liner_id:
                duplicate_count += 1
                continue
            saved.append(persisted)

        if not saved and rejected_count == 0 and duplicate_count == 0:
            warnings.append("The provider returned no usable candidates.")
        return OneLinerCandidateGenerationResult(
            saved_items=tuple(saved),
            duplicate_count=duplicate_count,
            rejected_count=rejected_count,
            warnings=tuple(warnings),
        )

    def _validate_request(
        self,
        *,
        concept_id: str,
        concept_label: str,
        source_url: str,
        source_locator: str,
        source_text: str,
        language_code: str,
        requested_count: int,
    ) -> None:
        for name, value in (
            ("concept_id", concept_id),
            ("concept_label", concept_label),
            ("source_locator", source_locator),
            ("language_code", language_code),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be non-empty trimmed text")
        parsed = urlsplit(source_url) if isinstance(source_url, str) else None
        if (
            parsed is None
            or parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError("source_url must be an absolute HTTPS URL without embedded credentials")
        if not isinstance(source_text, str) or not source_text.strip():
            raise ValueError("source_text must not be empty")
        if len(source_text) > self.maximum_source_characters:
            raise ValueError("source_text exceeds the configured character limit")
        if not 1 <= requested_count <= 50:
            raise ValueError("requested_count must be between 1 and 50")
