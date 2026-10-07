from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen

from ai_comp.domain.sources import CrawlPolicy
from ai_comp.research.paper import FetchedDocument
from ai_comp.research.storage import DocumentStorage

@dataclass(frozen=True)
class FetchResult:
    document: FetchedDocument
    duplicate: bool

class PaperFetcher:
    """Fetches a candidate and persists bytes through DocumentStorage."""
    def __init__(self, storage_dir: str | Path, timeout_seconds: float = 20.0, storage: DocumentStorage | None = None) -> None:
        self.storage_dir = Path(storage_dir)
        self.timeout_seconds = timeout_seconds
        self.storage = storage or DocumentStorage(self.storage_dir)

    def fetch(self, url: str, candidate_id: str, policy: CrawlPolicy) -> FetchResult:
        if not policy.allowed:
            raise ValueError("Fetching is disabled by crawl policy")
        request = Request(url, headers={"User-Agent": "AI-COMP/phase2 research"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = response.read()
            content_type = response.headers.get("Content-Type", "application/octet-stream")
        digest = sha256(payload).hexdigest()
        from ai_comp.research.discovery import infer_document_format
        document = FetchedDocument(digest, candidate_id, url, content_type, digest, len(payload), str(self.storage.root / digest), infer_document_format(url, content_type))
        duplicate = self.storage.exists(document)
        self.storage.write(document, payload)
        return FetchResult(document, duplicate)