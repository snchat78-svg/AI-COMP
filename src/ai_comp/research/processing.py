from dataclasses import dataclass
from enum import Enum
from html.parser import HTMLParser
from io import BytesIO
import re
from typing import Protocol
import unicodedata

from ai_comp.research.discovery import infer_document_format
from ai_comp.research.metadata import DocumentMetadataStore, StoredDocumentMetadata
from ai_comp.research.paper import DocumentFormat, FetchedDocument
from ai_comp.research.storage import DocumentStorage


class ExtractionMethod(str, Enum):
    DIRECT_TEXT = "DIRECT_TEXT"
    HTML_TEXT = "HTML_TEXT"
    PDF_TEXT = "PDF_TEXT"
    OCR = "OCR"
    EMPTY = "EMPTY"


@dataclass(frozen=True)
class StoredDocument:
    document: FetchedDocument
    metadata: StoredDocumentMetadata
    content: bytes


@dataclass(frozen=True)
class TextExtractionResult:
    document: FetchedDocument
    detected_format: DocumentFormat
    text: str
    method: ExtractionMethod
    ocr_used: bool


@dataclass(frozen=True)
class NormalizedDocument:
    document: FetchedDocument
    metadata: StoredDocumentMetadata
    text: str
    extraction_method: ExtractionMethod


class OCRAdapter(Protocol):
    def extract_text(self, content: bytes, document_format: DocumentFormat) -> str:
        """Return OCR text for image/PDF fallback input."""


class NullOCRAdapter:
    """Safe no-op OCR implementation until a real OCR provider is configured."""

    def extract_text(self, content: bytes, document_format: DocumentFormat) -> str:
        return ""


class _HTMLTextParser(HTMLParser):
    _SKIP_TAGS = {"script", "style", "noscript", "template"}
    _BLOCK_TAGS = {
        "address", "article", "aside", "blockquote", "dd", "div", "dl", "dt",
        "footer", "br", "h1", "h2", "h3", "h4", "h5", "h6", "header",
        "li", "main", "nav", "ol", "p", "pre", "section", "table", "td",
        "th", "tr", "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self._SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth == 0 and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth == 0 and tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth == 0:
            self.parts.append(data)


class DocumentInspector:
    """Reads stored bytes and determines the safest actual document format."""

    def __init__(self, storage: DocumentStorage) -> None:
        self.storage = storage

    def inspect(self, document: FetchedDocument) -> StoredDocument:
        content = self.storage.read(document)
        detected = detect_document_format(
            content,
            document.content_type,
            document.source_url,
        )
        metadata = StoredDocumentMetadata(
            document_id=document.document_id,
            candidate_id=document.candidate_id,
            source_url=document.source_url,
            content_type=document.content_type,
            sha256=document.sha256,
            size_bytes=len(content),
            storage_key=document.storage_key,
            declared_format=document.format,
            detected_format=detected,
        )
        return StoredDocument(document, metadata, content)


def detect_document_format(
    content: bytes,
    content_type: str = "",
    source_url: str = "",
) -> DocumentFormat:
    """Detect actual format, preferring file signatures over declarations."""

    if content.startswith(b"%PDF-"):
        return DocumentFormat.PDF
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return DocumentFormat.IMAGE
    if content.startswith(b"\xff\xd8\xff"):
        return DocumentFormat.IMAGE
    if content.startswith((b"GIF87a", b"GIF89a")):
        return DocumentFormat.IMAGE
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return DocumentFormat.IMAGE

    declared = content_type.split(";", 1)[0].strip().lower()
    if declared == "application/pdf":
        return DocumentFormat.PDF
    if declared.startswith("image/"):
        return DocumentFormat.IMAGE
    if declared in {"text/html", "application/xhtml+xml"}:
        return DocumentFormat.HTML
    if declared.startswith("text/"):
        return DocumentFormat.TEXT

    prefix = content[:2048].lstrip().lower()
    if (
        prefix.startswith(b"<!doctype html")
        or prefix.startswith(b"<html")
        or b"<html" in prefix
    ):
        return DocumentFormat.HTML

    return infer_document_format(source_url, content_type)


class TextExtractor:
    """Extracts text directly and falls back to an injected OCR adapter."""

    def __init__(self, ocr: OCRAdapter | None = None) -> None:
        self.ocr = ocr or NullOCRAdapter()

    def extract(self, stored: StoredDocument) -> TextExtractionResult:
        fmt = stored.metadata.detected_format

        if fmt is DocumentFormat.PDF:
            text = self._extract_pdf(stored.content)
            if text.strip():
                return TextExtractionResult(
                    stored.document, fmt, text, ExtractionMethod.PDF_TEXT, False
                )
            return self._ocr_result(stored)

        if fmt is DocumentFormat.HTML:
            text = self._extract_html(stored.content)
            return TextExtractionResult(
                stored.document,
                fmt,
                text,
                ExtractionMethod.HTML_TEXT if text.strip() else ExtractionMethod.EMPTY,
                False,
            )

        if fmt is DocumentFormat.TEXT:
            text = stored.content.decode("utf-8", errors="replace")
            return TextExtractionResult(
                stored.document,
                fmt,
                text,
                ExtractionMethod.DIRECT_TEXT if text.strip() else ExtractionMethod.EMPTY,
                False,
            )

        if fmt is DocumentFormat.IMAGE:
            return self._ocr_result(stored)

        return TextExtractionResult(
            stored.document,
            fmt,
            "",
            ExtractionMethod.EMPTY,
            False,
        )

    def _extract_pdf(self, content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError(
                "PDF extraction requires the 'pypdf' package"
            ) from exc

        reader = PdfReader(BytesIO(content))
        pages: list[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    def _extract_html(self, content: bytes) -> str:
        parser = _HTMLTextParser()
        parser.feed(content.decode("utf-8", errors="replace"))
        parser.close()
        return "".join(parser.parts)

    def _ocr_result(self, stored: StoredDocument) -> TextExtractionResult:
        text = self.ocr.extract_text(
            stored.content,
            stored.metadata.detected_format,
        )
        return TextExtractionResult(
            stored.document,
            stored.metadata.detected_format,
            text,
            ExtractionMethod.OCR if text.strip() else ExtractionMethod.EMPTY,
            True,
        )


class DocumentNormalizer:
    """Converts extracted text into stable input for later question extraction."""

    _MULTISPACE_RE = re.compile(r"[ \t]+")
    _MULTIBLANK_RE = re.compile(r"\n{3,}")

    def normalize(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [
            self._MULTISPACE_RE.sub(" ", line).strip()
            for line in text.split("\n")
        ]
        normalized = "\n".join(lines)
        normalized = self._MULTIBLANK_RE.sub("\n\n", normalized)
        return normalized.strip()


class DocumentProcessor:
    """Storage -> metadata -> detection -> extraction -> normalization."""

    def __init__(
        self,
        storage: DocumentStorage,
        ocr: OCRAdapter | None = None,
        metadata_store: DocumentMetadataStore | None = None,
    ) -> None:
        self.inspector = DocumentInspector(storage)
        self.metadata_store = metadata_store or DocumentMetadataStore(storage)
        self.extractor = TextExtractor(ocr)
        self.normalizer = DocumentNormalizer()

    def process(self, document: FetchedDocument) -> NormalizedDocument:
        stored = self.inspector.inspect(document)
        self.metadata_store.write(stored.metadata)
        extracted = self.extractor.extract(stored)
        normalized = self.normalizer.normalize(extracted.text)
        return NormalizedDocument(
            document=document,
            metadata=stored.metadata,
            text=normalized,
            extraction_method=extracted.method,
        )
