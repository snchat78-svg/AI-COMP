from dataclasses import dataclass
from hashlib import sha256
from collections.abc import Iterable

from ai_comp.database.repository import (
    AnswerKeyRepository,
    AnswerResolutionRepository,
    MatchRepository,
    QuestionRepository,
)
from ai_comp.domain.answers import AnswerKeyResolver, AnswerResolution
from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.master_questions import MasterAssignmentResult
from ai_comp.domain.matching import MatchType, QuestionMatch
from ai_comp.domain.questions import QuestionCandidate
from ai_comp.domain.verification import (
    SourceVerification,
    VerificationStatus,
    is_historical_evidence_allowed,
)
from ai_comp.extraction.question_extractor import QuestionExtractor
from ai_comp.master.batch import MasterQuestionBatchService
from ai_comp.matching.index import CandidatePairIndex
from ai_comp.matching.service import MatchingService
from ai_comp.history.builder import ExamAppearanceBuilder
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
    """Runs one auditable extracted-paper lifecycle."""

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
    ) -> IngestionResult:
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

        resolutions = self.answer_resolver.resolve_many(
            questions,
            entries,
        )
        resolved = tuple(
            item for item in resolutions if item.question_id
        )
        unresolved = tuple(
            item for item in resolutions if not item.question_id
            or item.selected_option_key is None
        )
        for resolution in resolved:
            self.answer_resolution_repository.save(resolution)

        matches = self._match_and_persist(questions)
        assignments = self.master_service.assign_many(
            questions,
            matches,
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

    def _match_and_persist(
        self,
        questions: tuple[QuestionCandidate, ...],
    ) -> tuple[QuestionMatch, ...]:
        result: list[QuestionMatch] = []
        for question in questions:
            batch = self.matching_service.match_question(question)
            for match in batch.matches:
                self.match_repository.save(match)
                result.append(match)
        return tuple(result)

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
            if assignment is not None:
                if assignment.relationship is not None:
                    match_type = assignment.relationship.value

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
