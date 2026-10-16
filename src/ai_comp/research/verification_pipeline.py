"""Source-backed paper/key reconciliation and historical question ingestion.

Only official registered-host documents with explicit registered exam and year
metadata may create historical appearances. Pairing separate keys is conservative:
exact exam/year plus unambiguous candidate counts and compatible shifts are required.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from urllib.parse import urlparse

from ai_comp.database.models import PaperRecord
from ai_comp.database.postgres_answer_key import PostgresAnswerKeyRepository
from ai_comp.database.postgres_answer_resolution import PostgresAnswerResolutionRepository
from ai_comp.database.postgres_appearance import PostgresAppearanceRepository
from ai_comp.database.postgres_master_question import PostgresMasterQuestionRepository
from ai_comp.database.postgres_match import PostgresMatchRepository
from ai_comp.database.postgres_paper import PostgresPaperRepository
from ai_comp.database.postgres_question import PostgresQuestionRepository
from ai_comp.database.postgres_registry import PostgresRegistryRepository
from ai_comp.database.postgres_research import (
    PostgresResearchRepository,
    ProcessedPaperCandidate,
)
from ai_comp.domain.questions import AnswerKeyEntry
from ai_comp.domain.ingestion import IngestionJobStatus
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
)
from ai_comp.ingestion.orchestrator import (
    VerifiedIngestionOrchestrator,
    VerifiedIngestionRequest,
)
from ai_comp.master.batch import MasterQuestionBatchService
from ai_comp.matching.engine import MatchEngine
from ai_comp.matching.index import CandidatePairIndex
from ai_comp.matching.service import MatchingService
from ai_comp.research.paper_metadata import (
    PaperArtifactRole,
    PaperMetadataResolver,
    ResolvedPaperMetadata,
)
from ai_comp.research.registry_sync import sync_source_registry
from ai_comp.research.seed_registry import build_initial_registry


@dataclass(frozen=True)
class PairDecision:
    question_candidate_id: str
    answer_key_candidate_id: str
    status: str
    reason: str


@dataclass(frozen=True)
class VerificationItemResult:
    candidate_id: str
    role: str
    exam_id: str | None
    year: int | None
    state: str
    reason: str
    question_count: int = 0
    answer_key_entry_count: int = 0
    appearance_count: int = 0
    unresolved_answer_count: int = 0


@dataclass(frozen=True)
class VerificationPipelineSummary:
    selected_candidates: int
    metadata_ready: int
    needs_review: int
    pairs_matched: int
    pairs_needs_review: int
    history_records_written: int
    extracted_questions_seen: int
    answer_key_entries_seen: int
    failed: int
    items: tuple[VerificationItemResult, ...]


def decide_answer_key_pairs(
    metadata: tuple[ResolvedPaperMetadata, ...],
) -> tuple[PairDecision, ...]:
    """Pure pairing rules for explicit exam/year candidates; never fuzzy-pair."""
    groups: dict[tuple[str, int], list[ResolvedPaperMetadata]] = defaultdict(list)
    for item in metadata:
        if not item.ready_for_pairing or item.exam_id is None or item.year is None:
            continue
        if item.role is PaperArtifactRole.QUESTION_PAPER and item.question_count <= 0:
            continue
        if item.role is PaperArtifactRole.ANSWER_KEY and item.answer_key_entry_count <= 0:
            continue
        if item.role in {PaperArtifactRole.QUESTION_PAPER, PaperArtifactRole.ANSWER_KEY}:
            groups[(item.exam_id, item.year)].append(item)

    decisions: list[PairDecision] = []
    for (exam_id, year), group in sorted(groups.items()):
        questions = sorted(
            (item for item in group if item.role is PaperArtifactRole.QUESTION_PAPER),
            key=lambda item: item.candidate_id,
        )
        keys = sorted(
            (item for item in group if item.role is PaperArtifactRole.ANSWER_KEY),
            key=lambda item: item.candidate_id,
        )
        if not questions or not keys:
            continue
        if len(questions) == 1 and len(keys) == 1:
            question = questions[0]
            answer_key = keys[0]
            if question.shift == answer_key.shift:
                decisions.append(PairDecision(
                    question.candidate_id,
                    answer_key.candidate_id,
                    "MATCHED",
                    "one explicit question paper and one explicit answer key share exam, year and shift",
                ))
            else:
                decisions.append(PairDecision(
                    question.candidate_id,
                    answer_key.candidate_id,
                    "NEEDS_REVIEW",
                    "exam/year match, but shift is not an exact match; automatic answer-key pairing blocked",
                ))
            continue
        for question in questions:
            for answer_key in keys:
                decisions.append(PairDecision(
                    question.candidate_id,
                    answer_key.candidate_id,
                    "NEEDS_REVIEW",
                    "multiple question papers or answer keys share this exam/year; manual pairing required",
                ))
    return tuple(decisions)


def _stable_id(prefix: str, *parts: str) -> str:
    raw = "|".join(parts).encode("utf-8")
    return f"{prefix}:{sha256(raw).hexdigest()[:32]}"


def _paper_id(candidate_id: str) -> str:
    return _stable_id("paper", candidate_id)


def _verification_id(source_id: str, source_url: str, evidence_type: EvidenceType) -> str:
    return _stable_id("verify", source_id, source_url, evidence_type.value)


def _trusted_official_source(record: ProcessedPaperCandidate) -> bool:
    candidate, source = record.candidate, record.source
    parsed = urlparse(candidate.url)
    base = urlparse(source.base_url)
    return (
        source.priority.value == "OFFICIAL"
        and source.source_type.value in {"OFFICIAL_WEBSITE", "OFFICIAL_PAPER", "OFFICIAL_ANSWER_KEY"}
        and parsed.scheme == "https"
        and parsed.netloc == base.netloc
    )


def _verification_for(
    record: ProcessedPaperCandidate,
    metadata: ResolvedPaperMetadata,
) -> SourceVerification | None:
    if not _trusted_official_source(record):
        return None
    if metadata.role is PaperArtifactRole.QUESTION_PAPER:
        evidence = EvidenceType.OFFICIAL_PAPER
    elif metadata.role is PaperArtifactRole.ANSWER_KEY:
        evidence = EvidenceType.OFFICIAL_ANSWER_KEY
    else:
        # Archive membership alone proves where the file was found, not that
        # it is a paper or official key of a specific exam.
        evidence = EvidenceType.OFFICIAL_ARCHIVE
    return SourceVerification(
        verification_id=_verification_id(
            record.source.source_id, record.candidate.url, evidence
        ),
        source_id=record.source.source_id,
        source_url=record.candidate.url,
        status=VerificationStatus.VERIFIED,
        evidence_type=evidence,
        checked_at=datetime.now(timezone.utc),
        confidence=0.95 if evidence is not EvidenceType.OFFICIAL_ARCHIVE else 0.8,
        notes=(
            "Fetched from a registered official source after robots/access checks. "
            "Verification of source origin does not imply all exam metadata or answer content is verified."
        ),
    )


def _state_upsert(
    connection: Any,
    *,
    candidate_id: str,
    metadata: ResolvedPaperMetadata,
    state: str,
    reason: str,
    paired_candidate_id: str | None = None,
    answer_key_sha256: str | None = None,
    history_recorded: bool = False,
) -> None:
    connection.execute(
        """
        INSERT INTO paper_verification_state (
            candidate_id, exam_id, year, shift, artifact_role, state,
            paired_answer_key_candidate_id, paired_answer_key_sha256,
            reason, last_processed_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                CASE WHEN %s THEN NOW() ELSE NULL END, NOW())
        ON CONFLICT (candidate_id) DO UPDATE SET
            exam_id = EXCLUDED.exam_id,
            year = EXCLUDED.year,
            shift = EXCLUDED.shift,
            artifact_role = EXCLUDED.artifact_role,
            state = EXCLUDED.state,
            paired_answer_key_candidate_id = EXCLUDED.paired_answer_key_candidate_id,
            paired_answer_key_sha256 = EXCLUDED.paired_answer_key_sha256,
            reason = EXCLUDED.reason,
            last_processed_at = CASE
                WHEN %s THEN NOW()
                ELSE paper_verification_state.last_processed_at
            END,
            updated_at = NOW()
        """,
        (
            candidate_id, metadata.exam_id, metadata.year, metadata.shift,
            metadata.role.value, state, paired_candidate_id, answer_key_sha256,
            reason, history_recorded, history_recorded,
        ),
    )


def run_verification_pipeline(
    connection: Any,
    *,
    source_id: str = "all",
    limit: int = 500,
) -> VerificationPipelineSummary:
    """Persist conservative metadata/pairs and record verified official history."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 5000:
        raise ValueError("limit must be between 1 and 5000")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string")

    registry = build_initial_registry()
    source_map = {source.source_id: source for source in registry.sources()}
    if source_id != "all" and source_id not in source_map:
        raise ValueError("source_id is not present in the registered source list")
    sync_source_registry(connection, registry)

    research_repository = PostgresResearchRepository(connection)
    records = research_repository.list_processed_candidates(
        limit=limit,
        source_id=source_id,
    )
    question_repository = PostgresQuestionRepository(connection)
    answer_repository = PostgresAnswerKeyRepository(connection)
    paper_repository = PostgresPaperRepository(connection)
    registry_repository = PostgresRegistryRepository(connection)
    resolver = PaperMetadataResolver(registry)

    metadata_by_id: dict[str, ResolvedPaperMetadata] = {}
    record_by_id = {record.candidate.candidate_id: record for record in records}
    questions_by_id = {}
    entries_by_id = {}
    verification_by_id = {}
    eligible: set[str] = set()
    item_reasons: dict[str, str] = {}

    # Metadata is sourced only from official source links, the archive's visible
    # labels/URL, and deterministic extraction counts; no guessed year/exam.
    for record in records:
        candidate_id = record.candidate.candidate_id
        questions = question_repository.get_for_document(record.document.document_id)
        entries = answer_repository.get_for_document(record.document.document_id)
        questions_by_id[candidate_id] = questions
        entries_by_id[candidate_id] = entries
        meta = resolver.resolve(
            record.candidate,
            record.source,
            question_count=len(questions),
            answer_key_entry_count=len(entries),
        )
        metadata_by_id[candidate_id] = meta
        verification = _verification_for(record, meta)
        if verification is not None:
            registry_repository.save_verification(verification)
            verification_by_id[candidate_id] = verification

        paper_repository.save(PaperRecord(
            paper_id=_paper_id(candidate_id),
            candidate_id=candidate_id,
            title=record.candidate.title,
            exam_id=meta.exam_id,
            category_id=meta.category_id,
            source_id=record.source.source_id,
            canonical_url=record.candidate.url,
            year=meta.year,
            shift=meta.shift,
        ))
        if meta.ready_for_pairing and verification is not None:
            eligible.add(candidate_id)
            item_reasons[candidate_id] = "explicit registered exam/year metadata; official HTTPS source"
        else:
            item_reasons[candidate_id] = meta.reason
            with connection.transaction():
                _state_upsert(
                    connection,
                    candidate_id=candidate_id,
                    metadata=meta,
                    state="NEEDS_REVIEW",
                    reason=meta.reason if verification is not None else (
                        meta.reason + "; source is not accepted as registered official HTTPS evidence"
                    ),
                )

    # Do not pair or claim verification for a candidate unless its source URL
    # passed the registered official HTTPS source gate above.
    pairable_metadata = tuple(
        meta for candidate_id, meta in metadata_by_id.items()
        if candidate_id in verification_by_id
    )
    decisions = decide_answer_key_pairs(pairable_metadata)
    by_pair: dict[tuple[str, str], PairDecision] = {
        (decision.question_candidate_id, decision.answer_key_candidate_id): decision
        for decision in decisions
    }
    pair_by_question: dict[str, list[PairDecision]] = defaultdict(list)
    for decision in decisions:
        pair_by_question[decision.question_candidate_id].append(decision)

    # Reconcile only candidates in this fetched batch. Old rows remain available;
    # matched rows are re-derived from this run's deterministic pair decisions.
    if records:
        candidate_ids = tuple(record_by_id)
        with connection.transaction():
            connection.execute(
                """
                UPDATE paper_answer_key_pairs
                SET pair_status = 'NEEDS_REVIEW',
                    match_reason = 'pair recomputed by a later verification run',
                    updated_at = NOW()
                WHERE question_candidate_id = ANY(%s)
                   OR answer_key_candidate_id = ANY(%s)
                """,
                (list(candidate_ids), list(candidate_ids)),
            )
            for decision in decisions:
                q_record = record_by_id.get(decision.question_candidate_id)
                k_record = record_by_id.get(decision.answer_key_candidate_id)
                q_meta = metadata_by_id.get(decision.question_candidate_id)
                if q_record is None or k_record is None or q_meta is None:
                    continue
                k_meta = metadata_by_id[decision.answer_key_candidate_id]
                pair_id = _stable_id(
                    "pair", decision.question_candidate_id, decision.answer_key_candidate_id
                )
                connection.execute(
                    """
                    INSERT INTO paper_answer_key_pairs (
                        pair_id, question_paper_id, answer_key_paper_id,
                        question_candidate_id, answer_key_candidate_id,
                        question_document_id, answer_key_document_id,
                        exam_id, year, shift, pair_status, match_reason,
                        updated_at
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                    ON CONFLICT (question_candidate_id, answer_key_candidate_id)
                    DO UPDATE SET
                        pair_status = EXCLUDED.pair_status,
                        match_reason = EXCLUDED.match_reason,
                        exam_id = EXCLUDED.exam_id,
                        year = EXCLUDED.year,
                        shift = EXCLUDED.shift,
                        updated_at = NOW()
                    """,
                    (
                        pair_id,
                        _paper_id(decision.question_candidate_id),
                        _paper_id(decision.answer_key_candidate_id),
                        decision.question_candidate_id,
                        decision.answer_key_candidate_id,
                        q_record.document.document_id,
                        k_record.document.document_id,
                        q_meta.exam_id,
                        q_meta.year,
                        q_meta.shift,
                        decision.status,
                        decision.reason,
                    ),
                )

    # Build exactly one orchestrator with a bounded historical candidate index.
    # It writes appearances only when the question paper itself has official
    # verified evidence and explicit exam/year metadata.
    pool = question_repository.list_recent(limit=min(5000, max(1, limit)))
    master_repository = PostgresMasterQuestionRepository(connection)
    orchestrator = VerifiedIngestionOrchestrator(
        question_repository=question_repository,
        answer_key_repository=answer_repository,
        answer_resolution_repository=PostgresAnswerResolutionRepository(connection),
        match_repository=PostgresMatchRepository(connection),
        appearance_repository=PostgresAppearanceRepository(connection),
        master_service=MasterQuestionBatchService(master_repository),
        matching_service=MatchingService(CandidatePairIndex(pool), MatchEngine()),
        candidate_questions=pool,
    )

    results_by_id: dict[str, VerificationItemResult] = {}
    history_count = failed_count = needs_review_count = question_total = key_total = 0
    matched_count = sum(item.status == "MATCHED" for item in decisions)
    needs_pair_review_count = sum(item.status == "NEEDS_REVIEW" for item in decisions)

    matched_key_by_question: dict[str, str] = {}
    for decision in decisions:
        if decision.status == "MATCHED":
            matched_key_by_question[decision.question_candidate_id] = decision.answer_key_candidate_id

    for record in records:
        candidate_id = record.candidate.candidate_id
        meta = metadata_by_id[candidate_id]
        questions = questions_by_id[candidate_id]
        entries = entries_by_id[candidate_id]
        question_total += len(questions)
        key_total += len(entries)
        verification = verification_by_id.get(candidate_id)
        state = "NEEDS_REVIEW"
        reason = item_reasons[candidate_id]
        appearance_count = 0
        unresolved_count = len(entries)

        if (
            candidate_id in eligible
            and meta.role is PaperArtifactRole.QUESTION_PAPER
            and questions
            and verification is not None
        ):
            paired_key_id = matched_key_by_question.get(candidate_id)
            key_record = record_by_id.get(paired_key_id) if paired_key_id else None
            key_entries: tuple[AnswerKeyEntry, ...] | None = None
            key_sha: str | None = None
            if key_record is not None and paired_key_id:
                key_entries = entries_by_id[paired_key_id]
                key_sha = key_record.document.sha256

            try:
                output = orchestrator.ingest(
                    VerifiedIngestionRequest(
                        document=record.document,
                        exam_id=meta.exam_id or "",
                        conducting_body_id=record.source.conducting_body_id,
                        year=meta.year or 0,
                        exam_date=None,
                        shift=meta.shift,
                        paper_id=_paper_id(candidate_id),
                        source_url=record.candidate.url,
                        verification=verification,
                        answer_key_entries=key_entries,
                        answer_key_document_id=(
                            key_record.document.document_id
                            if key_record is not None
                            else None
                        ),
                    ),
                    resume_after=IngestionJobStatus.EXTRACTED,
                )
                if output.historical_ingestion_allowed:
                    state = "HISTORY_RECORDED"
                    appearance_count = output.appearance_count
                    unresolved_count = output.unresolved_answer_count
                    history_count += output.appearance_count
                    if output.history_skip_reason:
                        reason = output.history_skip_reason
                    else:
                        reason = (
                            "official question paper history recorded"
                            + (" with uniquely paired official answer key" if key_entries is not None else "; correct answers may be unavailable")
                        )
                    with connection.transaction():
                        _state_upsert(
                            connection,
                            candidate_id=candidate_id,
                            metadata=meta,
                            state=state,
                            reason=reason,
                            paired_candidate_id=paired_key_id,
                            answer_key_sha256=key_sha,
                            history_recorded=True,
                        )
                        if key_record is not None and key_entries:
                            key_verification = verification_by_id.get(paired_key_id)
                            if key_verification is not None:
                                key_paper_id = _paper_id(paired_key_id)
                                questions_by_number = {
                                    question.question_number: question.question_id
                                    for question in questions
                                }
                                for entry in key_entries:
                                    question_id = questions_by_number.get(entry.question_number)
                                    if question_id is None:
                                        continue
                                    # Must match VerifiedIngestionOrchestrator._appearance_id.
                                    identity = "|".join((
                                        meta.exam_id or "",
                                        str(meta.year),
                                        meta.shift or "",
                                        str(entry.question_number),
                                    ))
                                    appearance_id = (
                                        "appearance:"
                                        + sha256(identity.encode("utf-8")).hexdigest()[:24]
                                    )
                                    connection.execute(
                                        """
                                        INSERT INTO appearance_sources (
                                            appearance_id, source_url, paper_id,
                                            verification_id
                                        )
                                        VALUES (%s,%s,%s,%s)
                                        ON CONFLICT DO NOTHING
                                        """,
                                        (
                                            appearance_id,
                                            key_record.candidate.url,
                                            key_paper_id,
                                            key_verification.verification_id,
                                        ),
                                    )
                else:
                    state = "NEEDS_REVIEW"
                    reason = output.history_skip_reason or "history ingestion was not permitted"
                    needs_review_count += 1
            except Exception as exc:
                state = "FAILED"
                reason = "verification ingestion failed: " + type(exc).__name__
                failed_count += 1
                with connection.transaction():
                    _state_upsert(
                        connection,
                        candidate_id=candidate_id,
                        metadata=meta,
                        state=state,
                        reason=reason,
                    )
        elif candidate_id in eligible and meta.role is PaperArtifactRole.ANSWER_KEY:
            state = "READY" if entries else "NEEDS_REVIEW"
            reason = "official answer-key candidate; awaiting a unique matching question paper"
        else:
            needs_review_count += 1

        results_by_id[candidate_id] = VerificationItemResult(
            candidate_id=candidate_id,
            role=meta.role.value,
            exam_id=meta.exam_id,
            year=meta.year,
            state=state,
            reason=reason,
            question_count=len(questions),
            answer_key_entry_count=len(entries),
            appearance_count=appearance_count,
            unresolved_answer_count=unresolved_count,
        )
        # Avoid overwriting HISTORY_RECORDED after successful ingestion.
        if state != "HISTORY_RECORDED":
            with connection.transaction():
                _state_upsert(
                    connection,
                    candidate_id=candidate_id,
                    metadata=meta,
                    state=state,
                    reason=reason,
                    paired_candidate_id=matched_key_by_question.get(candidate_id),
                    answer_key_sha256=(
                        record_by_id[matched_key_by_question[candidate_id]].document.sha256
                        if candidate_id in matched_key_by_question
                        else None
                    ),
                )

    return VerificationPipelineSummary(
        selected_candidates=len(records),
        metadata_ready=len(eligible),
        needs_review=needs_review_count,
        pairs_matched=matched_count,
        pairs_needs_review=needs_pair_review_count,
        history_records_written=history_count,
        extracted_questions_seen=question_total,
        answer_key_entries_seen=key_total,
        failed=failed_count,
        items=tuple(results_by_id[item.candidate.candidate_id] for item in records),
    )


__all__ = [
    "PairDecision",
    "VerificationItemResult",
    "VerificationPipelineSummary",
    "decide_answer_key_pairs",
    "run_verification_pipeline",
]
