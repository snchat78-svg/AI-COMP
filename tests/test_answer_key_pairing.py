from ai_comp.research.paper_metadata import (
    PaperArtifactRole,
    ResolvedPaperMetadata,
)
from ai_comp.research.verification_pipeline import decide_answer_key_pairs


def meta(candidate_id, role, *, exam_id="RSSB_CET", year=2024, shift=None, ready=True):
    return ResolvedPaperMetadata(
        candidate_id=candidate_id,
        role=role,
        exam_id=exam_id,
        year=year,
        shift=shift,
        category_id=None,
        ready_for_pairing=ready,
        reason="test",
        question_count=1 if role is PaperArtifactRole.QUESTION_PAPER else 0,
        answer_key_entry_count=1 if role is PaperArtifactRole.ANSWER_KEY else 0,
    )


def test_unique_exact_exam_year_and_shift_pair_is_matched():
    decisions = decide_answer_key_pairs((
        meta("paper", PaperArtifactRole.QUESTION_PAPER, shift="1"),
        meta("key", PaperArtifactRole.ANSWER_KEY, shift="1"),
    ))

    assert len(decisions) == 1
    assert decisions[0].status == "MATCHED"
    assert decisions[0].question_candidate_id == "paper"
    assert decisions[0].answer_key_candidate_id == "key"


def test_mismatched_shift_requires_manual_review():
    decisions = decide_answer_key_pairs((
        meta("paper", PaperArtifactRole.QUESTION_PAPER, shift="1"),
        meta("key", PaperArtifactRole.ANSWER_KEY, shift="2"),
    ))

    assert len(decisions) == 1
    assert decisions[0].status == "NEEDS_REVIEW"


def test_multiple_question_papers_or_keys_never_auto_pair():
    decisions = decide_answer_key_pairs((
        meta("paper-1", PaperArtifactRole.QUESTION_PAPER),
        meta("paper-2", PaperArtifactRole.QUESTION_PAPER),
        meta("key-1", PaperArtifactRole.ANSWER_KEY),
        meta("key-2", PaperArtifactRole.ANSWER_KEY),
    ))

    assert len(decisions) == 4
    assert all(item.status == "NEEDS_REVIEW" for item in decisions)


def test_different_exam_or_year_never_pair():
    decisions = decide_answer_key_pairs((
        meta("paper", PaperArtifactRole.QUESTION_PAPER, year=2024),
        meta("key-wrong-year", PaperArtifactRole.ANSWER_KEY, year=2023),
        meta("key-wrong-exam", PaperArtifactRole.ANSWER_KEY, exam_id="RPSC_RAS"),
    ))

    assert decisions == ()


def test_empty_question_or_answer_key_extractions_are_not_auto_paired():
    paper = ResolvedPaperMetadata(
        candidate_id="paper",
        role=PaperArtifactRole.QUESTION_PAPER,
        exam_id="RSSB_CET",
        year=2024,
        shift=None,
        category_id=None,
        ready_for_pairing=True,
        reason="label matched but extraction is empty",
        question_count=0,
        answer_key_entry_count=0,
    )
    key = ResolvedPaperMetadata(
        candidate_id="key",
        role=PaperArtifactRole.ANSWER_KEY,
        exam_id="RSSB_CET",
        year=2024,
        shift=None,
        category_id=None,
        ready_for_pairing=True,
        reason="label matched but extraction is empty",
        question_count=0,
        answer_key_entry_count=0,
    )
    assert decide_answer_key_pairs((paper, key)) == ()


def test_unready_metadata_is_excluded_from_pairing():
    decisions = decide_answer_key_pairs((
        meta("paper", PaperArtifactRole.QUESTION_PAPER),
        meta("key-unverified", PaperArtifactRole.ANSWER_KEY, ready=False),
    ))

    assert decisions == ()
