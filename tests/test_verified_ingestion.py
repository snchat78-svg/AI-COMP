from datetime import datetime, timezone

from ai_comp.domain.answers import AnswerResolutionStatus
from ai_comp.domain.matching import MatchType
from ai_comp.domain.questions import QuestionKind, QuestionOption
from ai_comp.domain.sources import SourcePriority
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
)
from ai_comp.ingestion.orchestrator import (
    VerifiedIngestionOrchestrator,
    VerifiedIngestionRequest,
)
from ai_comp.master.repository import InMemoryMasterQuestionRepository
from ai_comp.master.batch import MasterQuestionBatchService
from ai_comp.matching.engine import MatchEngine
from ai_comp.matching.index import CandidatePairIndex
from ai_comp.matching.service import MatchingService


class MemoryQuestions:
    def __init__(self):
        self.items = {}

    def save(self, question):
        self.items[question.question_id] = question

    def get(self, question_id):
        return self.items.get(question_id)

    def get_for_document(self, document_id):
        return tuple(
            q for q in self.items.values() if q.document_id == document_id
        )


class MemoryAnswerKeys:
    def __init__(self):
        self.items = {}

    def save_many(self, document_id, entries):
        self.items[document_id] = tuple(entries)

    def get_for_document(self, document_id):
        return self.items.get(document_id, ())


class MemoryResolutions:
    def __init__(self):
        self.items = []

    def save(self, resolution):
        self.items.append(resolution)

    def get_for_question(self, question_id):
        return tuple(
            r for r in self.items if r.question_id == question_id
        )


class MemoryMatches:
    def __init__(self):
        self.items = []

    def save(self, match):
        self.items.append(match)

    def get_for_question(self, question_id):
        return tuple(
            m for m in self.items
            if question_id in (m.left_question_id, m.right_question_id)
        )


class MemoryAppearances:
    def __init__(self):
        self.items = []

    def save(self, appearance):
        self.items.append(appearance)


class MemoryExtractor:
    def __init__(self, result):
        self.result = result

    def extract(self, document):
        return self.result


def verification(status):
    return SourceVerification(
        verification_id=f"v-{status.value}",
        source_id="official",
        source_url="https://example.gov/paper.pdf",
        status=status,
        evidence_type=EvidenceType.OFFICIAL_PAPER,
        checked_at=datetime.now(timezone.utc),
        confidence=1.0,
    )


def build_document():
    from ai_comp.research.metadata import StoredDocumentMetadata
    from ai_comp.research.paper import DocumentFormat, FetchedDocument
    from ai_comp.research.processing import ExtractionMethod, NormalizedDocument

    fetched = FetchedDocument(
        document_id="doc-1",
        candidate_id="candidate-1",
        source_url="https://example.gov/paper.pdf",
        content_type="application/pdf",
        sha256="a" * 64,
        size_bytes=3,
        storage_key="a" * 64,
        format=DocumentFormat.PDF,
    )
    metadata = StoredDocumentMetadata(
        document_id="doc-1",
        candidate_id="candidate-1",
        source_url="https://example.gov/paper.pdf",
        content_type="application/pdf",
        sha256="a" * 64,
        size_bytes=3,
        storage_key="a" * 64,
        declared_format=DocumentFormat.PDF,
        detected_format=DocumentFormat.PDF,
    )
    return NormalizedDocument(
        document=fetched,
        metadata=metadata,
        text="1. भारत की राजधानी क्या है?\nA. दिल्ली\nB. मुंबई",
        extraction_method=ExtractionMethod.DIRECT_TEXT,
    )


def test_verified_ingestion_creates_history_and_master_assignment():
    from ai_comp.domain.questions import AnswerKeyEntry, QuestionCandidate
    from ai_comp.domain.questions import QuestionExtractionResult

    q = QuestionCandidate(
        question_id="q1",
        document_id="doc-1",
        document_sha256="a" * 64,
        question_number=1,
        stem="भारत की राजधानी क्या है?",
        options=(
            QuestionOption("A", "दिल्ली"),
            QuestionOption("B", "मुंबई"),
        ),
        kind=QuestionKind.MCQ,
        raw_text="question",
        start_line=1,
        end_line=3,
    )
    extraction = QuestionExtractionResult(
        document_id="doc-1",
        questions=(q,),
        answer_key_entries=(
            AnswerKeyEntry(1, "A", "1-A", 10),
        ),
    )
    questions = MemoryQuestions()
    answers = MemoryAnswerKeys()
    resolutions = MemoryResolutions()
    matches = MemoryMatches()
    appearances = MemoryAppearances()
    master_repo = InMemoryMasterQuestionRepository()
    orchestrator = VerifiedIngestionOrchestrator(
        question_repository=questions,
        answer_key_repository=answers,
        answer_resolution_repository=resolutions,
        match_repository=matches,
        appearance_repository=appearances,
        master_service=MasterQuestionBatchService(master_repo),
        matching_service=MatchingService(
            CandidatePairIndex(),
            MatchEngine(),
        ),
        question_extractor=MemoryExtractor(extraction),
    )

    result = orchestrator.ingest(
        VerifiedIngestionRequest(
            document=build_document(),
            exam_id="exam-1",
            conducting_body_id="body-1",
            year=2025,
            exam_date=None,
            shift="1",
            paper_id="paper-1",
            source_url="https://example.gov/paper.pdf",
            verification=verification(VerificationStatus.VERIFIED),
        )
    )

    assert result.question_count == 1
    assert result.answer_resolution_count == 1
    assert result.unresolved_answer_count == 0
    assert result.appearance_count == 1
    assert len(appearances.items) == 1
    assert appearances.items[0].correct_answer == "A"
    assert appearances.items[0].verification.status is VerificationStatus.VERIFIED
    assert result.master_assignments[0].status.value == "CREATED"


def test_unverified_source_never_creates_historical_appearance():
    from ai_comp.domain.questions import AnswerKeyEntry, QuestionCandidate
    from ai_comp.domain.questions import QuestionExtractionResult

    q = QuestionCandidate(
        question_id="q1",
        document_id="doc-1",
        document_sha256="a" * 64,
        question_number=1,
        stem="प्रश्न?",
        options=(QuestionOption("A", "एक"), QuestionOption("B", "दो")),
        kind=QuestionKind.MCQ,
        raw_text="question",
        start_line=1,
        end_line=3,
    )
    extraction = QuestionExtractionResult(
        document_id="doc-1",
        questions=(q,),
        answer_key_entries=(AnswerKeyEntry(1, "Z", "1-Z", 10),),
    )
    appearances = MemoryAppearances()
    orchestrator = VerifiedIngestionOrchestrator(
        question_repository=MemoryQuestions(),
        answer_key_repository=MemoryAnswerKeys(),
        answer_resolution_repository=MemoryResolutions(),
        match_repository=MemoryMatches(),
        appearance_repository=appearances,
        master_service=MasterQuestionBatchService(
            InMemoryMasterQuestionRepository()
        ),
        matching_service=MatchingService(
            CandidatePairIndex(),
            MatchEngine(),
        ),
        question_extractor=MemoryExtractor(extraction),
    )

    result = orchestrator.ingest(
        VerifiedIngestionRequest(
            document=build_document(),
            exam_id="exam-1",
            conducting_body_id="body-1",
            year=2025,
            exam_date=None,
            shift="1",
            paper_id="paper-1",
            source_url="https://example.gov/paper.pdf",
            verification=verification(VerificationStatus.UNVERIFIED),
        )
    )

    assert result.historical_ingestion_allowed is False
    assert result.appearance_count == 0
    assert result.unresolved_answer_count == 1
    assert appearances.items == []
