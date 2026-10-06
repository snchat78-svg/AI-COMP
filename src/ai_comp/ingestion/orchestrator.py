from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping

from ai_comp.database.repository import (
    AnswerKeyRepository,
    AnswerResolutionRepository,
    MatchRepository,
    QuestionRepository,
)
from ai_comp.domain.answers import AnswerKeyResolver, AnswerResolution
from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.ingestion import IngestionJobStatus
from ai_comp.domain.master_questions import (
    MasterAssignmentResult,
    MasterAssignmentStatus,
    MasterMembershipType,
)
from ai_comp.domain.matching import QuestionMatch
from ai_comp.domain.questions import QuestionCandidate
from ai_comp.domain.verification import (
    SourceVerification,
    is_historical_evidence_allowed,
)
from ai_comp.extraction.question_extractor import QuestionExtractor
from ai_comp.history.builder import ExamAppearanceBuilder
from ai_comp.master.batch import MasterQuestionBatchService
from ai_comp.matching.index import CandidatePairIndex
from ai_comp.matching.service import MatchingService
from ai_comp.research.processing import NormalizedDocument


@dataclass(frozen=True)
class VerifiedIngestionRequest:
    document: NormalizedDocument
    exam_id: str
    conducting_body_id: str | None
    year: int
    exam_date: str | None
    shift: str | None
    paper_id: str
    source_url: str
    verification: SourceVerification


@dataclass(frozen=True)
class IngestionResult:
    document_id: str
    question_count: int
    answer_resolution_count: int
    unresolved_answer_count: int
    match_count: int
    appearance_count: int
    master_assignment_count: int
    historical_ingestion_allowed: bool
    history_skip_reason: str | None
    master_assignments: tuple[MasterAssignmentResult, ...]
    unresolved_answers: tuple[AnswerResolution, ...]


class VerifiedIngestionOrchestrator:
    """Runs one auditable extracted-paper lifecycle with resumable checkpoints."""

    _CHECKPOINT_ORDER = {
        IngestionJobStatus.PROCESSING: 0,
        IngestionJobStatus.EXTRACTED: 1,
        IngestionJobStatus.MATCHED: 2,
        IngestionJobStatus.MASTERED: 3,
        IngestionJobStatus.HISTORICAL_RECORDED: 4,
    }

    def __init__(
        self,
        *,
        question_repository: QuestionRepository,
        answer_key_repository: AnswerKeyRepository,
        answer_resolution_repository: AnswerResolutionRepository,
        match_repository: MatchRepository,
        appearance_repository,
        master_service: MasterQuestionBatchService,
        matching_service: MatchingService,
        question_extractor: QuestionExtractor | None = None,
        answer_resolver: AnswerKeyResolver | None = None,
        appearance_builder: ExamAppearanceBuilder | None = None,
        candidate_questions: Iterable[QuestionCandidate] = (),
    ) -> None:
        self.question_repository = question_repository
        self.answer_key_repository = answer_key_repository
        self.answer_resolution_repository = answer_resolution_repository
        self.match_repository = match_repository
        self.appearance_repository = appearance_repository
        self.master_service = master_service
        self.matching_service = matching_service
        self.question_extractor = question_extractor or QuestionExtractor()
        self.answer_resolver = answer_resolver or AnswerKeyResolver()
        self.appearance_builder = appearance_builder or ExamAppearanceBuilder()
        self.candidate_index = CandidatePairIndex(candidate_questions)

    def ingest(
        self,
        request: VerifiedIngestionRequest,
        *,
        resume_after: IngestionJobStatus | None = None,
        progress_callback: Callable[
            [IngestionJobStatus, Mapping[str, object]], None
        ] | None = None,
    ) -> IngestionResult:
        if self._at_least(resume_after, IngestionJobStatus.EXTRACTED):
            questions = self.question_repository.get_for_document(
                request.document.document_id
            )
            entries = self.answer_key_repository.get_for_document(
                request.document.document_id
            )
            if not questions:
                raise ValueError(
                    "cannot resume after EXTRACTED: no persisted questions"
                )
            for question in questions:
                self.candidate_index.add(question)
        else:
            extraction = self.question_extractor.extract(request.document)
            questions = extraction.questions
            entries = extraction.answer_key_entries

            self.answer_key_repository.save_many(
                request.document.document_id,
                entries,
            )
            for question in questions:
                self.question_repository.save(question)
                self.candidate_index.add(question)

            self._progress(
                progress_callback,
                IngestionJobStatus.EXTRACTED,
                {
                    "question_count": len(questions),
                    "answer_key_count": len(entries),
                },
            )

        resolved, unresolved = self._resolve_answers(questions, entries)

        if self._at_least(resume_after, IngestionJobStatus.MATCHED):
            matches = self._load_matches(questions)
        else:
            matches = self._match_and_persist(questions)
            self._progress(
                progress_callback,
                IngestionJobStatus.MATCHED,
                {"match_count": len(matches)},
            )

        if self._at_least(resume_after, IngestionJobStatus.MASTERED):
            assignments = self._load_assignments(questions)
        else:
            assignments = self.master_service.assign_many(
                questions,
                matches,
            )
            self._progress(
                progress_callback,
                IngestionJobStatus.MASTERED,
                {"master_assignment_count": len(assignments)},
            )

        allowed = is_historical_evidence_allowed(
            request.verification.status
        )
        appearances = ()
        skip_reason = None

        if allowed:
            appearances = self._build_appearances(
                request=request,
                questions=questions,
                resolutions=resolved,
                assignments=assignments,
            )
            for appearance in appearances:
                self.appearance_repository.save(appearance)
            self._progress(
                progress_callback,
                IngestionJobStatus.HISTORICAL_RECORDED,
                {"appearance_count": len(appearances)},
            )
        else:
            skip_reason = (
                "source verification is not VERIFIED; "
                "question and matching data were retained, "
                "but no historical appearance was created"
            )

        return IngestionResult(
            document_id=request.document.document_id,
            question_count=len(questions),
            answer_resolution_count=len(resolved),
            unresolved_answer_count=len(unresolved),
            match_count=len(matches),
            appearance_count=len(appearances),
            master_assignment_count=len(assignments),
            historical_ingestion_allowed=allowed,
            history_skip_reason=skip_reason,
            master_assignments=assignments,
            unresolved_answers=unresolved,
        )

    def _resolve_answers(
        self,
        questions: tuple[QuestionCandidate, ...],
        entries,
    ) -> tuple[tuple[AnswerResolution, ...], tuple[AnswerResolution, ...]]:
        resolutions = self.answer_resolver.resolve_many(questions, entries)
        for resolution in resolutions:
            if resolution.question_id:
                self.answer_resolution_repository.save(resolution)

        resolved = tuple(
            resolution
            for resolution in resolutions
            if resolution.question_id
            and resolution.selected_option_key is not None
        )
        unresolved = tuple(
            resolution
            for resolution in resolutions
            if not resolution.question_id
            or resolution.selected_option_key is None
        )
        return resolved, unresolved

    def _match_and_persist(
        self,
        questions: tuple[QuestionCandidate, ...],
    ) -> tuple[QuestionMatch, ...]:
        result: list[QuestionMatch] = []
        seen: set[tuple[str, str, str]] = set()
        for question in questions:
            batch = self.matching_service.match_question(question)
            for match in batch.matches:
                key = (
                    min(match.left_question_id, match.right_question_id),
                    max(match.left_question_id, match.right_question_id),
                    match.match_type.value,
                )
                if key in seen:
                    continue
                seen.add(key)
                self.match_repository.save(match)
                result.append(match)
        return tuple(result)

    def _load_matches(
        self,
        questions: tuple[QuestionCandidate, ...],
    ) -> tuple[QuestionMatch, ...]:
        result: list[QuestionMatch] = []
        seen: set[tuple[str, str]] = set()
        for question in questions:
            for match in self.match_repository.get_for_question(
                question.question_id
            ):
                key = tuple(
                    sorted(
                        (match.left_question_id, match.right_question_id)
                    )
                )
                if key in seen:
                    continue
                seen.add(key)
                result.append(match)
        return tuple(result)

    def _load_assignments(
        self,
        questions: tuple[QuestionCandidate, ...],
    ) -> tuple[MasterAssignmentResult, ...]:
        results = []
        for question in questions:
            membership = (
                self.master_service.repository.get_membership_for_question(
                    question.question_id
                )
            )
            if membership is None:
                raise ValueError(
                    "cannot resume after MASTERED: missing master membership "
                    f"for {question.question_id}"
                )
            results.append(
                MasterAssignmentResult(
                    question_id=question.question_id,
                    status=MasterAssignmentStatus.ALREADY_ASSIGNED,
                    master_question_id=membership.master_question_id,
                    relationship=membership.relationship,
                    reason="restored from durable master membership",
                )
            )
        return tuple(results)

    @classmethod
    def _at_least(
        cls,
        completed: IngestionJobStatus | None,
        target: IngestionJobStatus,
    ) -> bool:
        if completed is None:
            return False
        return (
            completed in cls._CHECKPOINT_ORDER
            and target in cls._CHECKPOINT_ORDER
            and cls._CHECKPOINT_ORDER[completed]
            >= cls._CHECKPOINT_ORDER[target]
        )

    @staticmethod
    def _progress(
        callback: Callable[
            [IngestionJobStatus, Mapping[str, object]], None
        ] | None,
        status: IngestionJobStatus,
        checkpoint: Mapping[str, object],
    ) -> None:
        if callback is not None:
            callback(status, checkpoint)

    def _build_appearances(
        self,
        *,
        request: VerifiedIngestionRequest,
        questions: tuple[QuestionCandidate, ...],
        resolutions: tuple[AnswerResolution, ...],
        assignments: tuple[MasterAssignmentResult, ...],
    ) -> tuple[ExamAppearance, ...]:
        by_question = {item.question_id: item for item in resolutions}
        by_assignment = {item.question_id: item for item in assignments}
        appearances = []

        for question in questions:
            assignment = by_assignment.get(question.question_id)
            match_type = "EXACT"
            if (
                assignment is not None
                and assignment.relationship is MasterMembershipType.REPHRASED
            ):
                match_type = "REPHRASED"

            resolution = by_question.get(question.question_id)
            appearances.append(
                self.appearance_builder.build(
                    appearance_id=self._appearance_id(
                        request,
                        question,
                    ),
                    question=question,
                    exam_id=request.exam_id,
                    conducting_body_id=request.conducting_body_id,
                    year=request.year,
                    exam_date=request.exam_date,
                    shift=request.shift,
                    paper_id=request.paper_id,
                    source_url=request.source_url,
                    verification=request.verification,
                    answer_resolution=resolution,
                    match_type=match_type,
                )
            )

        return tuple(appearances)

    @staticmethod
    def _appearance_id(
        request: VerifiedIngestionRequest,
        question: QuestionCandidate,
    ) -> str:
        identity = "|".join(
            (
                request.exam_id,
                str(request.year),
                request.shift or "",
                str(question.question_number),
            )
        )
        digest = sha256(identity.encode("utf-8")).hexdigest()[:24]
        return f"appearance:{digest}"
