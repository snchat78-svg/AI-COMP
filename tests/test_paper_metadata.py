from ai_comp.domain.sources import SourcePriority, SourceRecord, SourceType
from ai_comp.research.paper import DocumentFormat, PaperCandidate
from ai_comp.research.paper_metadata import (
    PaperArtifactRole,
    PaperMetadataResolver,
)
from ai_comp.research.seed_registry import build_initial_registry


def _source(source_id="RSSB_OFFICIAL"):
    registry = build_initial_registry()
    return next(source for source in registry.sources() if source.source_id == source_id)


def _candidate(candidate_id, source_id, url, title):
    return PaperCandidate(
        candidate_id=candidate_id,
        source_id=source_id,
        url=url,
        title=title,
        format=DocumentFormat.PDF,
    )


def test_resolves_explicit_rssb_cet_question_paper_and_year():
    registry = build_initial_registry()
    resolver = PaperMetadataResolver(registry)
    source = _source()
    candidate = _candidate(
        "cet-2024",
        source.source_id,
        "https://rssb.rajasthan.gov.in/files/CET_2024_Shift_1_Question_Paper.pdf",
        "Rajasthan CET 2024 Shift 1 Question Paper",
    )

    result = resolver.resolve(
        candidate, source, question_count=100, answer_key_entry_count=0
    )

    assert result.role is PaperArtifactRole.QUESTION_PAPER
    assert result.exam_id == "RSSB_CET"
    assert result.year == 2024
    assert result.shift == "1"
    assert result.category_id == "RSSB_CET_QUESTION_PAPER"
    assert result.ready_for_pairing is True


def test_resolves_explicit_rpsc_answer_key_separately():
    registry = build_initial_registry()
    resolver = PaperMetadataResolver(registry)
    source = _source("RPSC_OFFICIAL")
    candidate = _candidate(
        "rpsc-key",
        source.source_id,
        "https://rpsc.rajasthan.gov.in/Static/AnswerKeys/Senior_Teacher_2022_Final_Answer_Key.pdf",
        "RPSC Senior Teacher 2022 Final Answer Key",
    )

    result = resolver.resolve(
        candidate, source, question_count=0, answer_key_entry_count=100
    )

    assert result.role is PaperArtifactRole.ANSWER_KEY
    assert result.exam_id == "RPSC_SENIOR_TEACHER"
    assert result.year == 2022
    assert result.category_id == "RPSC_SENIOR_TEACHER_ANSWER_KEY"
    assert result.ready_for_pairing is True


def test_generic_board_paper_does_not_guess_exam_id():
    registry = build_initial_registry()
    resolver = PaperMetadataResolver(registry)
    source = _source("RPSC_OFFICIAL")
    candidate = _candidate(
        "generic",
        source.source_id,
        "https://rpsc.rajasthan.gov.in/question-paper-2023.pdf",
        "RPSC Question Paper 2023",
    )

    result = resolver.resolve(
        candidate, source, question_count=50, answer_key_entry_count=0
    )

    assert result.exam_id is None
    assert result.year == 2023
    assert result.role is PaperArtifactRole.QUESTION_PAPER
    assert result.ready_for_pairing is False


def test_conflicting_years_require_review_instead_of_guessing():
    registry = build_initial_registry()
    resolver = PaperMetadataResolver(registry)
    source = _source()
    candidate = _candidate(
        "two-years",
        source.source_id,
        "https://rssb.rajasthan.gov.in/files/CET_2023_Revised_2024.pdf",
        "Rajasthan CET 2023 revised 2024 question paper",
    )

    result = resolver.resolve(
        candidate, source, question_count=60, answer_key_entry_count=0
    )

    assert result.exam_id == "RSSB_CET"
    assert result.year is None
    assert result.ready_for_pairing is False


def test_unknown_document_type_is_not_automatically_classified():
    registry = build_initial_registry()
    resolver = PaperMetadataResolver(registry)
    source = _source()
    candidate = _candidate(
        "unlabelled",
        source.source_id,
        "https://rssb.rajasthan.gov.in/files/download-123.pdf",
        "Download 123",
    )

    result = resolver.resolve(
        candidate, source, question_count=0, answer_key_entry_count=0
    )

    assert result.role is PaperArtifactRole.UNKNOWN
    assert result.ready_for_pairing is False
