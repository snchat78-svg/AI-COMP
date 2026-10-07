from pathlib import Path

from ai_comp.domain.sources import CrawlPolicy, SourcePriority, SourceRecord, SourceType
from ai_comp.research.fetcher import FetchResult
from ai_comp.research.paper import DocumentFormat, FetchedDocument
from ai_comp.research.pipeline import PaperResearchPipeline
from ai_comp.research.storage import DocumentStorage


def source() -> SourceRecord:
    return SourceRecord(
        "RSSB_OFFICIAL",
        "RSSB",
        "https://rssb.rajasthan.gov.in/",
        SourceType.OFFICIAL_WEBSITE,
        SourcePriority.OFFICIAL,
    )


def test_pipeline_processes_fetched_document_to_normalized(tmp_path: Path):
    content = b"<html><body><h1> Exam   Paper </h1><p>Q1: India</p></body></html>"
    from hashlib import sha256

    digest = sha256(content).hexdigest()
    document = FetchedDocument(
        document_id=digest,
        candidate_id="C1",
        source_url="https://rssb.rajasthan.gov.in/paper.html",
        content_type="text/html",
        sha256=digest,
        size_bytes=len(content),
        storage_key=digest,
        format=DocumentFormat.HTML,
    )
    storage = DocumentStorage(tmp_path)
    storage.write(document, content)

    pipeline = PaperResearchPipeline(source(), CrawlPolicy(True), tmp_path)
    result = pipeline.process_fetched((FetchResult(document, duplicate=False),))

    assert len(result) == 1
    assert result[0].text == "Exam Paper\nQ1: India"
    assert result[0].metadata.detected_format is DocumentFormat.HTML
