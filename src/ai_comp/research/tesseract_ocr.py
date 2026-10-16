"""Tesseract OCR adapter for scanned Hindi and English paper PDFs/images."""
from __future__ import annotations

from io import BytesIO

from ai_comp.research.paper import DocumentFormat


class TesseractOCRAdapter:
    """OCR scanned PDFs/images; direct PDF text extraction remains the first path."""

    def __init__(self, *, languages: str = "hin+eng", dpi: int = 180, max_pages: int = 100) -> None:
        if dpi < 72 or dpi > 400:
            raise ValueError("dpi must be between 72 and 400")
        if max_pages < 1 or max_pages > 250:
            raise ValueError("max_pages must be between 1 and 250")
        if not languages.strip():
            raise ValueError("at least one OCR language is required")
        self.languages = languages
        self.dpi = dpi
        self.max_pages = max_pages

    def extract_text(self, content: bytes, document_format: DocumentFormat) -> str:
        try:
            from PIL import Image
            import pytesseract
        except ImportError as exc:
            raise RuntimeError(
                "OCR dependencies are missing; install the 'ocr' extra"
            ) from exc

        if document_format is DocumentFormat.IMAGE:
            with Image.open(BytesIO(content)) as image:
                return pytesseract.image_to_string(
                    image.convert("RGB"),
                    lang=self.languages,
                    config="--psm 6",
                ).strip()

        if document_format is not DocumentFormat.PDF:
            return ""

        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError(
                "Scanned-PDF OCR requires PyMuPDF; install the 'ocr' extra"
            ) from exc

        page_texts: list[str] = []
        with fitz.open(stream=content, filetype="pdf") as document:
            for page_index in range(min(len(document), self.max_pages)):
                page = document.load_page(page_index)
                pixmap = page.get_pixmap(dpi=self.dpi, alpha=False)
                with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
                    text = pytesseract.image_to_string(
                        image.convert("RGB"),
                        lang=self.languages,
                        config="--psm 6",
                    ).strip()
                if text:
                    page_texts.append(f"[Page {page_index + 1}]\n{text}")

        return "\n\n".join(page_texts)


__all__ = ["TesseractOCRAdapter"]
