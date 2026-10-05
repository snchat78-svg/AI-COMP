from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable

from ai_comp.domain.sources import CrawlPolicy, SourceRecord
from ai_comp.research.discovery import PaperDiscovery
from ai_comp.research.fetcher import PaperFetcher, FetchResult
from ai_comp.research.paper import PaperCandidate
from ai_comp.research.storage import DocumentStorage


@dataclass(frozen=True)
class ResearchBatchResult:
    candidates: tuple[PaperCandidate, ...]
    fetched: tuple[FetchResult, ...]


class PaperResearchPipeline:
    """Connects Phase 2 discovery, fetch, hashing and storage.

    Source links are supplied by a discovery adapter. This keeps live network
    orchestration outside the domain and makes every candidate pass through
    the Phase 1 source/policy boundary.
    """

    def __init__(
        self,
        source: SourceRecord,
        policy: CrawlPolicy,
        storage_dir: str | Path,
    ) -> None:
        self.source = source
        self.policy = policy
        self.discovery = PaperDiscovery(source, policy)
        self.fetcher = PaperFetcher(storage_dir)
        self.storage = DocumentStorage(storage_dir)

    def discover(self, links: Iterable[tuple[str, str]], source_id: str) -> tuple[PaperCandidate, ...]:
        return self.discovery.candidates_from_links(links, source_id)

    def fetch_candidates(
        self,
        candidates: Iterable[PaperCandidate],
    ) -> tuple[FetchResult, ...]:
        results: list[FetchResult] = []
        for candidate in candidates:
            result = self.fetcher.fetch(
                candidate.url,
                candidate.candidate_id,
                self.policy,
            )
            # Fetcher writes content-addressed bytes; storage verifies metadata
            # if the document is explicitly persisted through the storage API.
            results.append(result)
        return tuple(results)

    def run(
        self,
        links: Iterable[tuple[str, str]],
        source_id: str,
    ) -> ResearchBatchResult:
        candidates = self.discover(links, source_id)
        return ResearchBatchResult(candidates, self.fetch_candidates(candidates))
