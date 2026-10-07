from pathlib import Path

from ai_comp.research.metadata import DocumentMetadataStore
from ai_comp.research.paper import DocumentFormat, FetchedDocument
from ai_comp.research.processing import (
    DocumentProcessor,
    ExtractionMethod,
    detect_document_format,
)
from ai_comp.research.storage import DocumentStorage


def make_document(
    content: bytes,
    fmt: DocumentFormat,
    content_type: str,
) -> FetchedDocument:
    from hashlib import sha256

    digest = sha256(content).hexdigest()
    return FetchedDocument(
        document_id=digest,
        candidate_id="C1",
        source_url="https://example.com/paper.pdf",
        content_type=content_type,
        sha256=digest,
        size_bytes=len(content),
        storage_key=digest,
        format=fmt,
    )


def test_detection_prefers_pdf_signature():
    content = b"%PDF-1.7 fake"
    assert (
        detect_document_format(
            content,
            "text/html",
            "https://example.com/x.html",
        )
        is DocumentFormat.PDF
    )


def test_detection_accepts_common_image_signatures():
    assert detect_document_format(b"\x89PNG\r\n\x1a\nrest") is DocumentFormat.IMAGE
    assert detect_document_format(b"\xff\xd8\xffrest") is DocumentFormat.IMAGE
    assert detect_document_format(b"GIF89arest") is DocumentFormat.IMAGE


def test_html_extraction_and_normalization(tmp_path: Path):
    content = b"""<html><head><title>Ignore</title><style>x{}</style></head>
    <body><h1>  Exam   Paper </h1><p>Q1: India   is a country.</p></body></html>"""
    document = make_document(content, DocumentFormat.HTML, "text/html")

    storage = DocumentStorage(tmp_path)
    storage.write(document, content)

    result = DocumentProcessor(storage).process(document)

    assert result.extraction_method is ExtractionMethod.HTML_TEXT
    assert "Exam Paper" in result.text
    assert "Q1: India is a country." in result.text
    assert "Ignore" not in result.text
    assert (tmp_path / "metadata" / f"{document.sha256}.json").exists()


def test_image_uses_ocr_fallback(tmp_path: Path):
    content = b"\x89PNG\r\n\x1a\nimage"
    document = make_document(content, DocumentFormat.IMAGE, "image/png")

    class FakeOCR:
        def extract_text(
            self,
            content: bytes,
            document_format: DocumentFormat,
        ) -> str:
            assert document_format is DocumentFormat.IMAGE
            return "Q1: OCR extracted question"

    storage = DocumentStorage(tmp_path)
    storage.write(document, content)

    result = DocumentProcessor(storage, ocr=FakeOCR()).process(document)

    assert result.extraction_method is ExtractionMethod.OCR
    assert result.text == "Q1: OCR extracted question"


def test_metadata_round_trip(tmp_path: Path):
    content = b"plain exam text"
    document = make_document(content, DocumentFormat.TEXT, "text/plain")

    storage = DocumentStorage(tmp_path)
    storage.write(document, content)

    DocumentProcessor(storage).process(document)

    metadata = DocumentMetadataStore(storage).read(document)
    assert metadata.sha256 == document.sha256
    assert metadata.detected_format is DocumentFormat.TEXT
