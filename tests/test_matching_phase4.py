from datetime import datetime, timezone

from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.questions import QuestionCandidate, QuestionKind, QuestionOption
from ai_comp.domain.verification import EvidenceType, SourceVerification, VerificationStatus
from ai_comp.history.repository import InMemoryAppearanceRepository
from ai_comp.history.service import HistoryService
from ai_comp.matching.concept import ConceptMatcher
from ai_comp.matching.duplicate import QuestionDuplicateDetector
from ai_comp.matching.engine import MatchEngine
from ai_comp.matching.exact import ExactMatcher
from ai_comp.matching.normalization import normalize_question_text
from ai_comp.matching.semantic import SemanticMatcher


def question(question_id: str, stem: str, options: tuple[str, ...] = ("Jaipur", "Jaisalmer")):
    return QuestionCandidate(
        question_id=question_id,
        document_id="doc",
        document_sha256="hash",
        question_number=1,
        stem=stem,
        options=tuple(QuestionOption(key=chr(65+i), text=value) for i, value in enumerate(options)),
        kind=QuestionKind.MCQ,
        raw_text=stem,
        start_line=1,
        end_line=3,
    )


def verification(status=VerificationStatus.VERIFIED):
    return SourceVerification(
        verification_id="v1",
        source_id="rssb",
        source_url="https://example.gov/paper.pdf",
        status=status,
        evidence_type=EvidenceType.OFFICIAL_PAPER,
        checked_at=datetime.now(timezone.utc),
    )


def test_normalization_supports_exact_text():
    assert normalize_question_text("  राजस्थान—का  ") == "राजस्थान का"


def test_exact_match_requires_options_too():
    left = question("q1", "राजस्थान का सबसे बड़ा जिला?")
    right = question("q2", "राजस्थान का सबसे बड़ा जिला?")
    result = ExactMatcher().match(left, right)
    assert result is not None
    assert result.match_type.value == "EXACT"


def test_semantic_match_is_injected():
    def embed(text):
        return (1.0, 0.0) if "बड़ा" in text else (0.99, 0.01)

    left = question("q1", "राजस्थान का सबसे बड़ा जिला?")
    right = question("q2", "राजस्थान में सबसे अधिक क्षेत्रफल वाला जिला?")
    result = SemanticMatcher(embed, threshold=0.98).match(left, right)
    assert result is not None
    assert result.match_type.value == "REPHRASED"


def test_concept_match_is_explicit():
    concepts = {"q1": "RJ_GEOGRAPHY_00127", "q2": "RJ_GEOGRAPHY_00127"}
    matcher = ConceptMatcher(lambda q: concepts.get(q.question_id))
    result = matcher.match(question("q1", "एक"), question("q2", "दूसरा"))
    assert result is not None
    assert result.match_type.value == "SAME_CONCEPT"


def test_engine_order_is_exact_then_semantic_then_concept():
    engine = MatchEngine(
        semantic=SemanticMatcher(lambda _: (1.0, 0.0)),
        concept=ConceptMatcher(lambda _: "C1"),
    )
    result = engine.match(question("q1", "एक"), question("q2", "दो"))
    assert result is not None
    assert result.match_type.value == "REPHRASED"


def test_website_copy_is_duplicate_but_not_history():
    left = question("site-a:q1", "राजस्थान का सबसे बड़ा जिला?")
    right = question("site-b:q1", "राजस्थान का सबसे बड़ा जिला?")
    assert QuestionDuplicateDetector().are_duplicates(left, right)
    assert left.document_id == right.document_id


def test_verified_history_count_is_bounded_to_verified_records():
    repo = InMemoryAppearanceRepository()
    service = HistoryService(repo)
    verified = ExamAppearance(
        appearance_id="a1",
        question_id="q1",
        exam_id="cet_2024",
        conducting_body_id="rssb",
        year=2024,
        exam_date="2024-01-01",
        shift="Shift 1",
        question_number=12,
        original_question="Example?",
        options=(("A", "one"), ("B", "two")),
        correct_answer="A",
        source_url="https://example.gov/paper.pdf",
        paper_id="paper-1",
        verification=verification(),
    )
    secondary = ExamAppearance(
        appearance_id="a2",
        question_id="q1",
        exam_id="mock_2024",
        conducting_body_id=None,
        year=2024,
        exam_date=None,
        shift=None,
        question_number=2,
        original_question="Example?",
        options=(),
        correct_answer=None,
        source_url="https://example.com/paper",
        paper_id="paper-2",
        verification=verification(VerificationStatus.SECONDARY_LIKELY),
    )
    service.record_many((verified, secondary))
    assert service.verified_count("q1") == 1
