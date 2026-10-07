from __future__ import annotations

from pathlib import Path

from ai_comp.domain.materials import (
    MaterialFormat,
    MaterialInput,
    MaterialSource,
    NormalizedMaterial,
)
from ai_comp.research.processing import (
    DocumentProcessor,
    OCRAdapter,
    detect_document_format,
)
from ai_comp.research.paper import DocumentFormat, FetchedDocument
from ai_comp.research.storage import DocumentStorage
from ai_comp.material.storage import MaterialStorage


class MaterialProcessor:
    """User material -> stored bytes -> text/OCR -> normalized material."""

    def __init__(
        self,
        storage_root: str | Path,
        *,
        ocr: OCRAdapter | None = None,
    ) -> None:
        self.material_storage = MaterialStorage(storage_root)
        self.document_storage = DocumentStorage(storage_root)
        self.document_processor = DocumentProcessor(
            self.document_storage,
            ocr=ocr,
        )

    def process(self, material: MaterialInput) -> NormalizedMaterial:
        path = self.material_storage.write(material)
        detected = detect_document_format(
            material.content,
            material.content_type,
            material.filename,
        )
        digest = self.material_storage.sha256_for(material.content)
        material_id = self.material_storage.material_id_for(material.content)

        document = FetchedDocument(
            document_id=material_id,
            candidate_id=material_id,
            source_url=f"upload://{material_id}/{material.filename}",
            content_type=material.content_type,
            sha256=digest,
            size_bytes=len(material.content),
            storage_key=str(path),
            format=detected,
        )
        normalized = self.document_processor.process(document)

        warnings: list[str] = []
        if not normalized.text.strip():
            warnings.append(
                "no usable text was extracted; content-understanding cannot proceed"
            )

        return NormalizedMaterial(
            material_id=material_id,
            filename=material.filename,
            source=material.source,
            format=self._material_format(normalized.metadata.detected_format),
            content_type=material.content_type,
            sha256=digest,
            size_bytes=len(material.content),
            text=normalized.text,
            extraction_method=normalized.extraction_method.value,
            storage_key=str(path),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _material_format(detected: DocumentFormat) -> MaterialFormat:
        if detected is DocumentFormat.HTML:
            return MaterialFormat.TEXT
        return MaterialFormat(detected.value)

    @staticmethod
    def from_note(
        text: str,
        *,
        filename: str = "note.txt",
    ) -> MaterialInput:
        if not text.strip():
            raise ValueError("note text must not be empty")
        return MaterialInput(
            filename=filename,
            content_type="text/plain; charset=utf-8",
            content=text.encode("utf-8"),
            source=MaterialSource.USER_NOTE,
        )
