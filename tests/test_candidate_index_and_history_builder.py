from datetime import datetime, timezone

from ai_comp.domain.questions import QuestionCandidate, QuestionKind, QuestionOption
from ai_comp.domain.verification import EvidenceType, SourceVerification, VerificationStatus
from ai_comp.history.builder import ExamAppearanceBuilder
from ai_comp.matching.index import CandidatePairIndex
from ai_comp.matching.service import MatchingService
from ai_comp.matching.engine import MatchEngine
from ai_comp.matching.semantic import SemanticMatcher


def q(qid, stem, options=("Jaipur", "Jaisalmer")):
    return QuestionCandidate(
        question_id=qid,
        document_id="doc",
        document_sha256="hash",
        question_number=1,
        stem=stem,
        options=tuple(
            QuestionOption(key=chr(65+i), text=value)
            for i, value in enumerate(options)
        ),
        kind=QuestionKind.MCQ,
        raw_text=stem,
        start_line=1,
        end_line=3,
    )


def verification():
    return SourceVerification(
        verification_id="v1",
        source_id="rssb",
        source_url="https://example.gov/paper.pdf",
        status=VerificationStatus.VERIFIED,
        evidence_type=EvidenceType.OFFICIAL_PAPER,
        checked_at=datetime.now(timezone.utc),
    )


def test_exact_key_index_returns_only_same_key_candidates():
    left = q("q1", "राजस्थान का सबसे बड़ा जिला?")
    same = q("q2", "राजस्थान का सबसे बड़ा जिला?")
    other = q("q3", "राजस्थान की राजधानी?")
    index = CandidatePairIndex((left, same, other))
    result = index.exact_candidates(left)
    assert [item.question_id for item in result] == ["q2"]


def test_semantic_candidates_exclude_exact_duplicates():
    left = q("q1", "राजस्थान का सबसे बड़ा जिला?")
    same = q("q2", "राजस्थान का सबसे बड़ा जिला?")
    rephrased = q("q3", "राजस्थान में सबसे अधिक क्षेत्रफल वाला जिला?")
    index = CandidatePairIndex((left, same, rephrased))
    result = index.potential_semantic_candidates(left)
    assert [item.question_id for item in result] == ["q3"]


def test_matching_service_uses_engine():
    index = CandidatePairIndex((q("q1", "राजस्थान का सबसे बड़ा जिला?"), q("q2", "राजस्थान में सबसे अधिक क्षेत्रफल वाला जिला?")))
    engine = MatchEngine(
        semantic=SemanticMatcher(lambda _: (1.0, 0.0), threshold=0.9)
    )
    result = MatchingService(index, engine).match_question(q("q1", "राजस्थान का सबसे बड़ा जिला?"))
    assert any(item.match_type.value == "REPHRASED" for item in result.matches)


def test_appearance_builder_preserves_phase3_question_metadata():
    question = q("q1", "Example question?", ("A", "B"))
    appearance = ExamAppearanceBuilder().build(
        appearance_id="appearance-1",
        question=question,
        exam_id="cet_2024",
        conducting_body_id="rssb",
        year=2024,
        exam_date="2024-01-01",
        shift="Shift 1",
        paper_id="paper-1",
        source_url="https://example.gov/paper.pdf",
        verification=verification(),
        correct_answer="A",
    )
    assert appearance.question_id == "q1"
    assert appearance.question_number == 1
    assert appearance.paper_id == "paper-1"
    assert appearance.verification.status is VerificationStatus.VERIFIED
