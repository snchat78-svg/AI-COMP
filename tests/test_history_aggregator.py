from datetime import datetime, timezone

from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.matching import MatchType, QuestionMatch
from ai_comp.domain.verification import EvidenceType, SourceVerification, VerificationStatus
from ai_comp.history.aggregator import QuestionHistoryAggregator
from ai_comp.history.repository import InMemoryAppearanceRepository
from ai_comp.history.service import HistoryService
from ai_comp.history.view import HistoricalAppearanceView, HistoricalQuestionView


def verification(status=VerificationStatus.VERIFIED):
    return SourceVerification(
        verification_id="v1",
        source_id="rssb",
        source_url="https://example.gov/paper.pdf",
        status=status,
        evidence_type=EvidenceType.OFFICIAL_PAPER,
        checked_at=datetime.now(timezone.utc),
    )


def appearance(
    appearance_id,
    question_id,
    exam_id,
    question_number,
    *,
    match_type="EXACT",
    status=VerificationStatus.VERIFIED,
):
    return ExamAppearance(
        appearance_id=appearance_id,
        question_id=question_id,
        exam_id=exam_id,
        conducting_body_id="rssb",
        year=2024,
        exam_date="2024-01-01",
        shift="Shift 1",
        question_number=question_number,
        original_question="राजस्थान का उदाहरण?",
        options=(("A", "एक"), ("B", "दो")),
        correct_answer="A",
        source_url=f"https://example.gov/{appearance_id}.pdf",
        paper_id=f"paper-{appearance_id}",
        verification=verification(status),
        match_type=match_type,
    )


def test_aggregator_separates_match_types_and_counts_only_verified_historical_equivalents():
    matches = (
        QuestionMatch("q1", "q2", MatchType.EXACT, 1.0),
        QuestionMatch("q1", "q3", MatchType.REPHRASED, 0.96),
        QuestionMatch("q1", "q4", MatchType.SAME_CONCEPT, 0.90),
        QuestionMatch("q1", "q5", MatchType.RELATED_TOPIC, 0.70),
    )
    appearances = (
        appearance("a1", "q1", "exam-1", 1),
        appearance("a2", "q2", "exam-2", 2),
        appearance("a3", "q3", "exam-3", 3),
        appearance("a4", "q4", "exam-4", 4),
        appearance("a5", "q5", "exam-5", 5),
        appearance("a6", "q3", "exam-6", 6, status=VerificationStatus.SECONDARY_LIKELY),
    )

    history = QuestionHistoryAggregator().aggregate("q1", appearances, matches)

    assert [item.question_id for item in history.exact_appearances] == ["q1", "q2"]
    assert [item.question_id for item in history.rephrased_appearances] == ["q3", "q3"]
    assert [item.question_id for item in history.same_concept_appearances] == ["q4"]
    assert [item.question_id for item in history.related_topic_appearances] == ["q5"]
    assert history.verified_appearance_count == 3
    assert history.verified_history_text == "Verified database में 3 appearances मिले"


def test_aggregator_treats_copied_sources_as_one_exam_appearance():
    matches = (QuestionMatch("q1", "q2", MatchType.EXACT, 1.0),)
    appearances = (
        appearance("copy-1", "q1", "exam-1", 12),
        appearance("copy-2", "q2", "exam-1", 12),
    )

    history = QuestionHistoryAggregator().aggregate("q1", appearances, matches)

    assert len(history.historical_equivalent_appearances) == 1
    assert history.verified_appearance_count == 1


def test_unknown_direct_appearance_match_type_defaults_to_exact():
    item = appearance("a1", "q1", "exam-1", 1, match_type="unexpected")
    history = QuestionHistoryAggregator().aggregate("q1", (item,))

    assert len(history.exact_appearances) == 1
    assert history.verified_appearance_count == 1


def test_history_service_loads_related_appearances_from_repository():
    repo = InMemoryAppearanceRepository()
    repo.save(appearance("q1-a1", "q1", "exam-1", 1))
    repo.save(appearance("q2-a1", "q2", "exam-2", 2))

    history = HistoryService(repo).build_history(
        "q1",
        (QuestionMatch("q1", "q2", MatchType.REPHRASED, 0.95),),
    )

    assert len(history.exact_appearances) == 1
    assert len(history.rephrased_appearances) == 1
    assert history.verified_appearance_count == 2



def test_history_service_verified_count_uses_canonical_deduplication():
    repo = InMemoryAppearanceRepository()
    repo.save(appearance("copy-1", "q1", "exam-1", 12))
    repo.save(appearance("copy-2", "q2", "exam-1", 12))

    from ai_comp.domain.matching import MatchType, QuestionMatch

    service = HistoryService(
        repo,
        match_repository=None,
    )

    assert service.verified_count("q1") == 1
    history = service.build_history(
        "q1",
        (QuestionMatch("q1", "q2", MatchType.EXACT, 1.0),),
    )
    assert history.verified_appearance_count == 1

def test_history_view_preserves_exam_year_shift_question_number_and_source():
    repo = InMemoryAppearanceRepository()
    repo.save(appearance("view-1", "q1", "exam-2024", 17))

    view = HistoryService(repo).get_history_view("q1")

    item = view.exact_appearances[0]
    assert isinstance(item, HistoricalAppearanceView)
    assert isinstance(view, HistoricalQuestionView)
    assert item.exam_id == "exam-2024"
    assert item.year == 2024
    assert item.shift == "Shift 1"
    assert item.question_number == 17
    assert item.source_url == "https://example.gov/view-1.pdf"
    assert item.verification_status is VerificationStatus.VERIFIED
