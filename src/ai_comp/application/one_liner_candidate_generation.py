from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Protocol
from urllib.parse import urlsplit
from uuid import uuid4

from ai_comp.domain.topic_question_bank import (
    OneLinerVerificationStatus,
    TopicOneLinerQA,
)

MAX_ONE_LINER_TEXT_CHARACTERS = 240


def _is_concise_direct_pair(question_text: str, answer_text: str) -> bool:
    """Accept one short direct question and one short, single-line answer."""
    question = question_text.strip()
    answer = answer_text.strip()
    if not question or not answer:
        return False
    if any(char in question or char in answer for char in ("\n", "\r")):
        return False
    if len(question) > MAX_ONE_LINER_TEXT_CHARACTERS:
        return False
    if len(answer) > MAX_ONE_LINER_TEXT_CHARACTERS:
        return False
    question_marks = question.count("?") + question.count("？")
    if question_marks != 1 or not question.endswith(("?", "？")):
        return False
    if "?" in answer or "？" in answer:
        return False
    normalized_question = " ".join(question.casefold().split())
    normalized_answer = " ".join(answer.casefold().split())
    return normalized_question != normalized_answer

MAX_EXISTING_TOPIC_DUPLICATE_SCAN = 5000
NEAR_DUPLICATE_QUESTION_THRESHOLD = 0.78
NEAR_DUPLICATE_ANSWER_THRESHOLD = 0.90
NEAR_DUPLICATE_PAIR_THRESHOLD = 0.94


def _normalize_for_similarity(value: str) -> str:
    """Normalize punctuation/spacing while retaining Unicode letters and digits."""
    normalized = "".join(char.casefold() if char.isalnum() else " " for char in value)
    return " ".join(normalized.split())


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right, autojunk=False).ratio()


def _token_similarity(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _is_near_duplicate(
    candidate: TopicOneLinerQA,
    existing: TopicOneLinerQA,
) -> bool:
    """Compare Q+A pairs only within the same canonical concept and language."""
    if candidate.concept_id != existing.concept_id:
        return False
    if candidate.language_code != existing.language_code:
        return False
    candidate_question = _normalize_for_similarity(candidate.question_text)
    existing_question = _normalize_for_similarity(existing.question_text)
    candidate_answer = _normalize_for_similarity(candidate.answer_text)
    existing_answer = _normalize_for_similarity(existing.answer_text)
    question_similarity = _token_similarity(candidate_question, existing_question)
    if question_similarity < 0.55:
        return False
    answer_similarity = _similarity(candidate_answer, existing_answer)
    if (
        question_similarity >= NEAR_DUPLICATE_QUESTION_THRESHOLD
        and answer_similarity >= NEAR_DUPLICATE_ANSWER_THRESHOLD
    ):
        return True
    pair_similarity = _similarity(
        f"{candidate_question} | {candidate_answer}",
        f"{existing_question} | {existing_answer}",
    )
    return pair_similarity >= NEAR_DUPLICATE_PAIR_THRESHOLD



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
    def list_one_liners(
        self,
        concept_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        verified_only: bool = True,
        language_code: str | None = None,
    ) -> tuple[TopicOneLinerQA, ...]: ...

    def save_one_liner(self, item: TopicOneLinerQA) -> TopicOneLinerQA: ...


@dataclass(frozen=True)
class OneLinerCandidateGenerationResult:
    saved_items: tuple[TopicOneLinerQA, ...]
    provider_returned_count: int
    duplicate_count: int
    rejected_count: int
    warnings: tuple[str, ...]

    @property
    def generated_count(self) -> int:
        return self.provider_returned_count

    @property
    def saved_count(self) -> int:
        return len(self.saved_items)

    @property
    def pending_review_count(self) -> int:
        return sum(
            item.verification_status is OneLinerVerificationStatus.NEEDS_REVIEW
            for item in self.saved_items
        )

    @property
    def verified_count(self) -> int:
        # Generation is never allowed to verify its own output.
        return sum(
            item.verification_status is OneLinerVerificationStatus.VERIFIED
            for item in self.saved_items
        )


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

    def _load_existing_topic_items(
        self, *, concept_id: str, language_code: str
    ) -> tuple[TopicOneLinerQA, ...]:
        """Load bounded existing Q&A so near-duplicate checks include prior batches."""
        existing_items: list[TopicOneLinerQA] = []
        page_size = 500
        for offset in range(0, MAX_EXISTING_TOPIC_DUPLICATE_SCAN, page_size):
            page = self.repository.list_one_liners(
                concept_id,
                limit=page_size,
                offset=offset,
                verified_only=False,
                language_code=language_code,
            )
            existing_items.extend(page)
            if len(page) < page_size:
                return tuple(existing_items)
        overflow = self.repository.list_one_liners(
            concept_id,
            limit=1,
            offset=MAX_EXISTING_TOPIC_DUPLICATE_SCAN,
            verified_only=False,
            language_code=language_code,
        )
        if overflow:
            raise ValueError(
                "topic has more than the safe duplicate-scan limit; split or review the topic before generation"
            )
        return tuple(existing_items)

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
        existing_topic_items = self._load_existing_topic_items(
            concept_id=concept_id, language_code=language_code
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
        seen_items: list[TopicOneLinerQA] = list(existing_topic_items)

        for draft in ordered:
            if len(saved) >= requested_count:
                break
            if not _is_concise_direct_pair(draft.question_text, draft.answer_text):
                rejected_count += 1
                warnings.append(
                    "A candidate did not meet the single-question, concise one-line Q&A format."
                )
                continue
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
            if item.content_hash in seen_hashes or any(
                _is_near_duplicate(item, existing) for existing in seen_items
            ):
                duplicate_count += 1
                continue
            seen_hashes.add(item.content_hash)
            persisted = self.repository.save_one_liner(item)
            if persisted.one_liner_id != item.one_liner_id:
                duplicate_count += 1
                seen_items.append(persisted)
                continue
            saved.append(persisted)
            seen_items.append(persisted)

        if not saved and rejected_count == 0 and duplicate_count == 0:
            warnings.append("The provider returned no usable candidates.")
        return OneLinerCandidateGenerationResult(
            saved_items=tuple(saved),
            provider_returned_count=len(drafts),
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
