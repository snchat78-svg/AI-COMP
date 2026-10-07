from dataclasses import asdict, dataclass
import json
from pathlib import Path

from ai_comp.research.paper import DocumentFormat, FetchedDocument
from ai_comp.research.storage import DocumentStorage


@dataclass(frozen=True)
class StoredDocumentMetadata:
    """Metadata describing a stored document and its detected format."""

    document_id: str
    candidate_id: str
    source_url: str
    content_type: str
    sha256: str
    size_bytes: int
    storage_key: str
    declared_format: DocumentFormat
    detected_format: DocumentFormat

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["declared_format"] = self.declared_format.value
        data["detected_format"] = self.detected_format.value
        return data


class DocumentMetadataStore:
    """Stores metadata separately from immutable content-addressed bytes."""

    def __init__(self, storage: DocumentStorage) -> None:
        self.storage = storage
        self.root = storage.root / "metadata"

    def path_for(self, document: FetchedDocument) -> Path:
        return self.root / f"{document.sha256}.json"

    def write(self, metadata: StoredDocumentMetadata) -> Path:
        path = self.root / f"{metadata.sha256}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(metadata.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def read(self, document: FetchedDocument) -> StoredDocumentMetadata:
        path = self.path_for(document)
        data = json.loads(path.read_text(encoding="utf-8"))
        return StoredDocumentMetadata(
            document_id=str(data["document_id"]),
            candidate_id=str(data["candidate_id"]),
            source_url=str(data["source_url"]),
            content_type=str(data["content_type"]),
            sha256=str(data["sha256"]),
            size_bytes=int(data["size_bytes"]),
            storage_key=str(data["storage_key"]),
            declared_format=DocumentFormat(data["declared_format"]),
            detected_format=DocumentFormat(data["detected_format"]),
        )
