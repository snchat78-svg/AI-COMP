from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen

from ai_comp.domain.sources import CrawlPolicy
from ai_comp.research.paper import FetchedDocument


@dataclass(frozen=True)
class FetchResult:
    document: FetchedDocument
    duplicate: bool


class PaperFetcher:
    """Small dependency-free fetcher with injectable transport for tests."""

    def __init__(self, storage_dir: str | Path, timeout_seconds: float = 20.0) -> None:
        self.storage_dir = Path(storage_dir)
        self.timeout_seconds = timeout_seconds

    def fetch(self, url: str, candidate_id: str, policy: CrawlPolicy) -> FetchResult:
        if not policy.allowed:
            raise ValueError("Fetching is disabled by crawl policy")
        request = Request(url, headers={"User-Agent": "AI-COMP/phase2 research"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = response.read()
            content_type = response.headers.get("Content-Type", "application/octet-stream")
        digest = sha256(payload).hexdigest()
        target = self.storage_dir / digest
        duplicate = target.exists()
        if not duplicate:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        from ai_comp.research.discovery import infer_document_format
        document = FetchedDocument(
            document_id=digest,
            candidate_id=candidate_id,
            source_url=url,
            content_type=content_type,
            sha256=digest,
            size_bytes=len(payload),
            storage_key=str(target),
            format=infer_document_format(url, content_type),
        )
        return FetchResult(document=document, duplicate=duplicate)
