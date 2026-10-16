"""Bounded end-to-end processing for discovered official paper candidates.

This stage fetches original bytes, stores them privately, persists document
metadata/text, and extracts source-observed question and answer-key candidates.
It does not mark answers verified or create exam appearances.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import tempfile
from pathlib import Path
from typing import Any, Protocol

from ai_comp.database.postgres_answer_key import PostgresAnswerKeyRepository
from ai_comp.database.postgres_question import PostgresQuestionRepository
from ai_comp.database.postgres_research import PostgresResearchRepository
from ai_comp.domain.sources import CrawlPolicy
from ai_comp.extraction.question_extractor import QuestionExtractor
from ai_comp.research.paper import DiscoveryStatus, FetchedDocument
from ai_comp.research.processing import DocumentProcessor, OCRAdapter
from ai_comp.research.safe_downloader import SafePaperDownloader
from ai_comp.research.storage import DocumentStorage
from ai_comp.research.policy import ResearchPolicyError


class PrivateObjectStorage(Protocol):
    bucket: str

    def ensure_private_bucket(self) -> None: ...
    def upload(self, digest: str, payload: bytes, content_type: str): ...


@dataclass(frozen=True)
class PaperProcessingResult:
    candidate_id: str
    source_id: str
    status: str
    question_count: int = 0
    answer_key_entry_count: int = 0
    extraction_method: str | None = None
    error_type: str | None = None


@dataclass(frozen=True)
class PaperProcessingSummary:
    selected: int
    processed: int
    duplicate_documents: int
    question_candidates: int
    answer_key_entries: int
    empty_extractions: int
    failed: int
    rejected: int
    results: tuple[PaperProcessingResult, ...]


def process_pending_candidates(
    connection: Any,
    object_storage: PrivateObjectStorage,
    *,
    source_id: str = "all",
    limit: int = 10,
    retry_failed: bool = False,
    downloader: SafePaperDownloader | None = None,
    ocr: OCRAdapter | None = None,
    storage_root: str | Path | None = None,
    policy: CrawlPolicy | None = None,
) -> PaperProcessingSummary:
    """Fetch and extract a bounded set of pending official-source candidates."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")

    active_policy = policy or CrawlPolicy(
        allowed=True,
        respect_robots=True,
        respect_terms=True,
        rate_limit_seconds=1.0,
        max_depth=2,
    )
    if not active_policy.allowed or not active_policy.respect_robots or not active_policy.respect_terms:
        raise ValueError("official paper processing requires robots and terms compliance")

    repository = PostgresResearchRepository(connection)
    pending = repository.list_pending_candidates(
        limit=limit,
        source_id=source_id,
        retry_failed=retry_failed,
    )
    if not pending:
        return PaperProcessingSummary(0, 0, 0, 0, 0, 0, 0, 0, ())

    object_storage.ensure_private_bucket()
    active_downloader = downloader or SafePaperDownloader()
    question_repository = PostgresQuestionRepository(connection)
    answer_repository = PostgresAnswerKeyRepository(connection)
    extractor = QuestionExtractor()

    with tempfile.TemporaryDirectory(prefix="ai-comp-paper-processing-") as temp_dir:
        stage_root = Path(storage_root) if storage_root is not None else Path(temp_dir) / "stage"
        stage_root.mkdir(parents=True, exist_ok=True)
        local_storage = DocumentStorage(stage_root)
        processor = DocumentProcessor(local_storage, ocr=ocr)

        results: list[PaperProcessingResult] = []
        duplicate_count = question_count = answer_count = empty_count = 0
        failed_count = rejected_count = processed_count = 0

        for record in pending:
            candidate = record.candidate
            try:
                downloaded = active_downloader.download(
                    record.source,
                    candidate.url,
                    active_policy,
                )
                digest = sha256(downloaded.payload).hexdigest()

                if repository.has_document_hash(digest):
                    repository.mark_candidate_status(
                        candidate.candidate_id,
                        DiscoveryStatus.FETCHED,
                    )
                    duplicate_count += 1
                    results.append(PaperProcessingResult(
                        candidate_id=candidate.candidate_id,
                        source_id=candidate.source_id,
                        status="DUPLICATE_CONTENT",
                    ))
                    continue

                stored_object = object_storage.upload(
                    digest,
                    downloaded.payload,
                    downloaded.content_type,
                )
                document = FetchedDocument(
                    document_id=digest,
                    candidate_id=candidate.candidate_id,
                    source_url=downloaded.final_url,
                    content_type=downloaded.content_type,
                    sha256=digest,
                    size_bytes=len(downloaded.payload),
                    storage_key=stored_object.storage_uri,
                    format=downloaded.detected_format,
                )
                local_storage.write(document, downloaded.payload)
                normalized = processor.process(document)
                repository.save_normalized_document(normalized)

                extraction = extractor.extract(normalized)
                for question in extraction.questions:
                    question_repository.save(question)
                answer_repository.save_many(
                    document.document_id,
                    extraction.answer_key_entries,
                )
                repository.mark_candidate_status(
                    candidate.candidate_id,
                    DiscoveryStatus.FETCHED,
                )
                processed_count += 1
                question_count += len(extraction.questions)
                answer_count += len(extraction.answer_key_entries)
                if not normalized.text.strip():
                    empty_count += 1
                results.append(PaperProcessingResult(
                    candidate_id=candidate.candidate_id,
                    source_id=candidate.source_id,
                    status="PROCESSED",
                    question_count=len(extraction.questions),
                    answer_key_entry_count=len(extraction.answer_key_entries),
                    extraction_method=normalized.extraction_method.value,
                ))
            except ResearchPolicyError as exc:
                # Fail closed on policy violations; transient HTTP failures remain retryable.
                reason = str(exc)
                rejected = (
                    "disallowed" in reason
                    or "outside_registered" in reason
                    or "unsupported_document" in reason
                    or "robots_unavailable" in reason
                    or "robots_too_large" in reason
                )
                status = DiscoveryStatus.REJECTED if rejected else DiscoveryStatus.FAILED
                try:
                    repository.mark_candidate_status(candidate.candidate_id, status)
                except Exception:
                    pass
                if rejected:
                    rejected_count += 1
                else:
                    failed_count += 1
                results.append(PaperProcessingResult(
                    candidate_id=candidate.candidate_id,
                    source_id=candidate.source_id,
                    status="REJECTED" if rejected else "FAILED",
                    error_type=type(exc).__name__,
                ))
            except Exception as exc:
                try:
                    repository.mark_candidate_status(
                        candidate.candidate_id,
                        DiscoveryStatus.FAILED,
                    )
                except Exception:
                    pass
                failed_count += 1
                results.append(PaperProcessingResult(
                    candidate_id=candidate.candidate_id,
                    source_id=candidate.source_id,
                    status="FAILED",
                    error_type=type(exc).__name__,
                ))

    return PaperProcessingSummary(
        selected=len(pending),
        processed=processed_count,
        duplicate_documents=duplicate_count,
        question_candidates=question_count,
        answer_key_entries=answer_count,
        empty_extractions=empty_count,
        failed=failed_count,
        rejected=rejected_count,
        results=tuple(results),
    )


__all__ = [
    "PaperProcessingResult",
    "PaperProcessingSummary",
    "process_pending_candidates",
]
