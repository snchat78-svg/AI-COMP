from dataclasses import dataclass
from xml.etree import ElementTree as ET

from ai_comp.domain.sources import CrawlPolicy, SourceRecord
from ai_comp.research.discovery import PaperDiscovery
from ai_comp.research.policy import ResearchPolicyError, validate_candidate_url


@dataclass(frozen=True)
class DiscoveryLink:
    url: str
    kind: str


class FeedDiscovery:
    """Parses already-fetched sitemap/RSS/Atom XML; fetching remains injectable."""

    def __init__(self, source: SourceRecord, policy: CrawlPolicy) -> None:
        self.source = source
        self.policy = policy

    def sitemap_links(self, xml: str) -> tuple[DiscoveryLink, ...]:
        root = ET.fromstring(xml)
        return tuple(
            DiscoveryLink(loc.text.strip(), "sitemap")
            for loc in root.findall(".//{*}loc")
            if loc.text and self._valid(loc.text.strip())
        )

    def feed_links(self, xml: str) -> tuple[DiscoveryLink, ...]:
        root = ET.fromstring(xml)
        links = []
        for element in root.findall(".//{*}link"):
            href = element.attrib.get("href") or (element.text or "").strip()
            if href and self._valid(href):
                links.append(DiscoveryLink(href, "feed"))
        return tuple(links)

    def _valid(self, url: str) -> bool:
        try:
            validate_candidate_url(self.source, url, self.policy)
        except ResearchPolicyError:
            return False
        return True

    def candidates(self, links: tuple[DiscoveryLink, ...], source_id: str):
        return PaperDiscovery(self.source, self.policy).candidates_from_links(
            ((f"{source_id}:{i}", item.url) for i, item in enumerate(links, 1)),
            source_id,
        )
