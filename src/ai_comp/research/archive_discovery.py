from collections.abc import Iterable

from ai_comp.domain.sources import CrawlPolicy, SourceRecord
from ai_comp.research.discovery import PaperDiscovery


class ArchiveDiscovery:
    """Turns explicitly supplied archive links into paper candidates."""

    def __init__(self, source: SourceRecord, policy: CrawlPolicy) -> None:
        self.discovery = PaperDiscovery(source, policy)

    def candidates(self, links: Iterable[str], source_id: str):
        return self.discovery.candidates_from_links(
            ((f"{source_id}:archive:{i}", url) for i, url in enumerate(links, 1)),
            source_id,
        )
