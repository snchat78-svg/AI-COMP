from pathlib import Path

from ai_comp.domain.sources import CrawlPolicy, SourcePriority, SourceRecord, SourceType
from ai_comp.research.discovery import PaperDiscovery, infer_document_format
from ai_comp.research.paper import DocumentFormat
from ai_comp.research.policy import ResearchPolicyError, validate_candidate_url


def official_source() -> SourceRecord:
    return SourceRecord(
        "RSSB_OFFICIAL", "RSSB", "https://rssb.rajasthan.gov.in/",
        SourceType.OFFICIAL_WEBSITE, SourcePriority.OFFICIAL
    )


def test_document_format_detection():
    assert infer_document_format("https://example.com/paper.pdf") is DocumentFormat.PDF
    assert infer_document_format("https://example.com/page.html") is DocumentFormat.HTML
    assert infer_document_format("https://example.com/a.png") is DocumentFormat.IMAGE


def test_discovery_rejects_external_domain():
    policy = CrawlPolicy(True)
    try:
        validate_candidate_url(official_source(), "https://evil.example/paper.pdf", policy)
    except ResearchPolicyError:
        pass
    else:
        raise AssertionError("external URL must be rejected")


def test_discovery_accepts_registered_domain():
    policy = CrawlPolicy(True)
    validate_candidate_url(
        official_source(),
        "https://rssb.rajasthan.gov.in/archive/paper.pdf",
        policy,
    )


def test_discovery_filters_invalid_links():
    discovery = PaperDiscovery(official_source(), CrawlPolicy(True))
    result = discovery.candidates_from_links([
        ("1", "https://rssb.rajasthan.gov.in/paper.pdf"),
        ("2", "https://evil.example/paper.pdf"),
    ], "RSSB_OFFICIAL")
    assert len(result) == 1
    assert result[0].format is DocumentFormat.PDF


def test_fetcher_hash_storage_is_content_based(tmp_path: Path):
    from ai_comp.research.fetcher import PaperFetcher
    from ai_comp.research.paper import FetchedDocument
    import ai_comp.research.fetcher as fetcher_module

    class FakeResponse:
        headers = {"Content-Type": "application/pdf"}
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b"same-paper"

    original = fetcher_module.urlopen
    fetcher_module.urlopen = lambda *args, **kwargs: FakeResponse()
    try:
        fetcher = PaperFetcher(tmp_path)
        first = fetcher.fetch("https://rssb.rajasthan.gov.in/paper.pdf", "1", CrawlPolicy(True))
        second = fetcher.fetch("https://rssb.rajasthan.gov.in/other.pdf", "2", CrawlPolicy(True))
    finally:
        fetcher_module.urlopen = original

    assert first.duplicate is False
    assert second.duplicate is True
    assert first.document.sha256 == second.document.sha256
    assert first.document.size_bytes == len(b"same-paper")
