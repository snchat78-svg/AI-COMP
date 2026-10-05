from dataclasses import dataclass
from enum import Enum


class DocumentFormat(str, Enum):
    PDF = "pdf"
    HTML = "html"
    IMAGE = "image"
    TEXT = "text"
    UNKNOWN = "unknown"


class DiscoveryStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    REJECTED = "REJECTED"
    FETCHED = "FETCHED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class PaperCandidate:
    candidate_id: str
    source_id: str
    url: str
    title: str
    format: DocumentFormat = DocumentFormat.UNKNOWN
    category_id: str | None = None
    discovered_at: str = ""
    status: DiscoveryStatus = DiscoveryStatus.DISCOVERED


@dataclass(frozen=True)
class FetchedDocument:
    document_id: str
    candidate_id: str
    source_url: str
    content_type: str
    sha256: str
    size_bytes: int
    storage_key: str
    format: DocumentFormat
