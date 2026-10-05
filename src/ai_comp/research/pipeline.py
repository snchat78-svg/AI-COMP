from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from ai_comp.domain.sources import CrawlPolicy, SourceRecord
from ai_comp.research.discovery import PaperDiscovery
from ai_comp.research.fetcher import FetchResult, PaperFetcher
from ai_comp.research.live_discovery import LiveDiscoveryResult, LiveOfficialSourceDiscovery, HttpTransport
from ai_comp.research.paper import PaperCandidate
from ai_comp.research.storage import DocumentStorage

@dataclass(frozen=True)
class ResearchBatchResult:
    candidates: tuple[PaperCandidate, ...]
    fetched: tuple[FetchResult, ...]

class PaperResearchPipeline:
    """Connects discovery -> candidate -> fetch -> SHA-256 -> storage."""
    def __init__(self, source: SourceRecord, policy: CrawlPolicy, storage_dir: str | Path) -> None:
        self.source = source
        self.policy = policy
        self.discovery = PaperDiscovery(source, policy)
        self.storage = DocumentStorage(storage_dir)
        self.fetcher = PaperFetcher(storage_dir, storage=self.storage)

    def discover(self, links: Iterable[tuple[str, str]], source_id: str) -> tuple[PaperCandidate, ...]:
        return self.discovery.candidates_from_links(links, source_id)

    def fetch_candidates(self, candidates: Iterable[PaperCandidate]) -> tuple[FetchResult, ...]:
        return tuple(self.fetcher.fetch(c.url, c.candidate_id, self.policy) for c in candidates)

    def run(self, links: Iterable[tuple[str, str]], source_id: str) -> ResearchBatchResult:
        candidates = self.discover(links, source_id)
        return ResearchBatchResult(candidates, self.fetch_candidates(candidates))

    def run_live(self, transport: HttpTransport | None = None, max_documents: int = 100) -> ResearchBatchResult:
        """Discover from the registered source, then fetch every safe candidate."""
        live = LiveOfficialSourceDiscovery(transport or HttpTransport(), max_documents=max_documents)
        discovered: LiveDiscoveryResult = live.run(self.source, self.policy, self.source.source_id)
        return ResearchBatchResult(discovered.candidates, self.fetch_candidates(discovered.candidates))