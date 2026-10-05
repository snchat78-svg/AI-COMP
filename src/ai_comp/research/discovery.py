from collections.abc import Iterable
from urllib.parse import urlparse

from ai_comp.domain.sources import CrawlPolicy, SourceRecord
from ai_comp.research.paper import DocumentFormat, PaperCandidate
from ai_comp.research.policy import ResearchPolicyError, validate_candidate_url


def infer_document_format(url: str, content_type: str | None = None) -> DocumentFormat:
    content_type = (content_type or "").lower()
    path = urlparse(url).path.lower()
    if "pdf" in content_type or path.endswith(".pdf"):
        return DocumentFormat.PDF
    if "html" in content_type or path.endswith((".html", ".htm", "/")):
        return DocumentFormat.HTML
    if content_type.startswith("image/") or path.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return DocumentFormat.IMAGE
    if "text/plain" in content_type or path.endswith(".txt"):
        return DocumentFormat.TEXT
    return DocumentFormat.UNKNOWN


class PaperDiscovery:
    """Phase 2 discovery contract; network access is intentionally injected."""

    def __init__(self, source: SourceRecord, policy: CrawlPolicy) -> None:
        self.source = source
        self.policy = policy

    def candidates_from_links(
        self, links: Iterable[tuple[str, str]], source_id: str
    ) -> tuple[PaperCandidate, ...]:
        candidates: list[PaperCandidate] = []
        for candidate_id, url in links:
            try:
                validate_candidate_url(self.source, url, self.policy)
            except ResearchPolicyError:
                continue
            candidates.append(
                PaperCandidate(
                    candidate_id=candidate_id,
                    source_id=source_id,
                    url=url,
                    title=url.rsplit("/", 1)[-1] or url,
                    format=infer_document_format(url),
                )
            )
        return tuple(candidates)
