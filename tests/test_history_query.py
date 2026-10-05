from datetime import datetime, timezone

from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.matching import MatchType, QuestionMatch
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
)
from ai_comp.history.query import HistoryQuery
from ai_comp.history.repository import InMemoryAppearanceRepository
from ai_comp.history.service import HistoryService


def verification(status=VerificationStatus.VERIFIED, source_id="rssb"):
    return SourceVerification(
        verification_id=f"v-{source_id}-{status.value}",
        source_id=source_id,
        source_url="https://example.gov/paper.pdf",
        status=status,
        evidence_type=EvidenceType.OFFICIAL_PAPER,
        checked_at=datetime.now(timezone.utc),
    )


def appearance(
    appearance_id,
    question_id,
    exam_id,
    year,
    shift,
    *,
    conducting_body_id="rssb",
    match_type="EXACT",
    status=VerificationStatus.VERIFIED,
):
    return ExamAppearance(
        appearance_id=appearance_id,
        question_id=question_id,
        exam_id=exam_id,
        conducting_body_id=conducting_body_id,
        year=year,
        exam_date=f"{year}-01-01",
        shift=shift,
        question_number=1,
        original_question="Example?",
        options=(("A", "one"), ("B", "two")),
        correct_answer="A",
        source_url=f"https://example.gov/{appearance_id}.pdf",
        paper_id=f"paper-{appearance_id}",
        verification=verification(status, source_id=conducting_body_id or "none"),
        match_type=match_type,
    )


def test_history_query_filters_exam_year_shift_and_body():
    repo = InMemoryAppearanceRepository()
    repo.save(appearance("a1", "q1", "exam-a", 2024, "Shift 1"))
    repo.save(
        appearance(
            "a2",
            "q1",
            "exam-b",
            2025,
            "Shift 2",
            conducting_body_id="rpsc",
        )
    )
    repo.save(appearance("a3", "q1", "exam-a", 2024, "Shift 2"))

    view = HistoryService(repo).query_history_view(
        "q1",
        query=HistoryQuery(
            exam_id="exam-a",
            conducting_body_id="rssb",
            year=2024,
            shift="Shift 2",
        ),
    )

    assert [item.appearance_id for item in view.exact_appearances] == ["a3"]
    assert view.verified_appearance_count == 1


def test_verified_only_excludes_secondary_and_unverified_history():
    repo = InMemoryAppearanceRepository()
    repo.save(appearance("verified", "q1", "exam-a", 2024, "Shift 1"))
    repo.save(
        appearance(
            "secondary",
            "q1",
            "exam-b",
            2024,
            "Shift 1",
            status=VerificationStatus.SECONDARY_LIKELY,
        )
    )
    repo.save(
        appearance(
            "unverified",
            "q1",
            "exam-c",
            2024,
            "Shift 1",
            status=VerificationStatus.UNVERIFIED,
        )
    )

    view = HistoryService(repo).query_history_view(
        "q1",
        query=HistoryQuery(verified_only=True),
    )

    assert [item.appearance_id for item in view.exact_appearances] == ["verified"]
    assert view.verified_appearance_count == 1
    assert view.verified_history_text == "Verified database में 1 appearances मिले"


def test_history_query_preserves_match_type_buckets():
    repo = InMemoryAppearanceRepository()
    repo.save(appearance("exact", "q1", "exam-a", 2024, "Shift 1"))
    repo.save(appearance("rephrased", "q2", "exam-b", 2024, "Shift 1"))

    matches = (QuestionMatch("q1", "q2", MatchType.REPHRASED, 0.96),)

    view = HistoryService(repo).query_history_view(
        "q1",
        matches=matches,
        query=HistoryQuery(year=2024),
    )

    assert [item.appearance_id for item in view.exact_appearances] == ["exact"]
    assert [item.appearance_id for item in view.rephrased_appearances] == ["rephrased"]
    assert view.verified_appearance_count == 2


def test_query_rejects_conflicting_verified_only_status():
    try:
        HistoryQuery(
            verified_only=True,
            verification_status=VerificationStatus.SECONDARY_LIKELY,
        )
    except ValueError as exc:
        assert "non-VERIFIED" in str(exc)
    else:
        raise AssertionError("expected ValueError")
