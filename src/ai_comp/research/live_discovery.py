from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

from ai_comp.domain.sources import CrawlPolicy, SourceRecord
from ai_comp.research.discovery import PaperDiscovery
from ai_comp.research.feed_discovery import FeedDiscovery
from ai_comp.research.paper import PaperCandidate
from ai_comp.research.policy import ResearchPolicyError, validate_candidate_url

@dataclass(frozen=True)
class HttpResponse:
    url: str
    status_code: int
    content: str
    content_type: str = ""

class HttpTransport:
    def get(self, url: str) -> HttpResponse:
        from urllib.request import Request, urlopen
        request = Request(url, headers={"User-Agent": "AI-COMP/phase2"})
        with urlopen(request, timeout=15) as response:
            body = response.read()
            return HttpResponse(response.geturl(), response.status, body.decode("utf-8", errors="replace"), response.headers.get("Content-Type", ""))

@dataclass(frozen=True)
class LiveDiscoveryResult:
    robots_url: str
    sitemap_urls: tuple[str, ...]
    feed_urls: tuple[str, ...]
    archive_urls: tuple[str, ...]
    candidates: tuple[PaperCandidate, ...]

class LiveOfficialSourceDiscovery:
    """Safely turns one registered SourceRecord into live paper candidates."""
    def __init__(self, transport: HttpTransport, user_agent: str = "AI-COMP/phase2", max_documents: int = 100) -> None:
        self.transport = transport
        self.user_agent = user_agent
        self.max_documents = max_documents

    def run(self, source: SourceRecord, policy: CrawlPolicy, source_id: str | None = None) -> LiveDiscoveryResult:
        if not policy.allowed:
            raise ResearchPolicyError("Research is disabled by crawl policy")
        if not policy.respect_robots:
            raise ResearchPolicyError("robots.txt compliance must remain enabled")
        if not policy.respect_terms:
            raise ResearchPolicyError("terms/access compliance must remain enabled")
        source_id = source_id or source.source_id
        robots_url = urljoin(source.base_url, "/robots.txt")
        robots = self.transport.get(robots_url)
        if robots.status_code >= 400:
            raise ResearchPolicyError("robots_unavailable")
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(robots.content.splitlines())
        seeds = list(parser.site_maps() or []) + list(self._configured_seeds(source))
        seeds = self._unique_allowed(source, policy, parser, seeds)
        sitemap_urls, feed_urls, archive_urls, paper_links = [], [], [], []
        pending = [(url, 0) for url in seeds]
        seen: set[str] = set()
        while pending and len(seen) < self.max_documents:
            url, depth = pending.pop(0)
            if url in seen or depth > policy.max_depth:
                continue
            seen.add(url)
            if len(seen) > 1 and policy.rate_limit_seconds > 0:
                sleep(policy.rate_limit_seconds)
            response = self.transport.get(url)
            if response.status_code >= 400:
                continue
            is_xml = "xml" in response.content_type.lower() or url.lower().endswith((".xml", ".rss", ".atom"))
            if not is_xml:
                archive_urls.append(url)
                paper_links.extend(self._archive_links(source, policy, parser, response.content, response.url))
                continue
            feed = FeedDiscovery(source, policy)
            try:
                sitemap_links = feed.sitemap_links(response.content)
            except Exception:
                sitemap_links = ()
            try:
                feed_links = feed.feed_links(response.content)
            except Exception:
                feed_links = ()
            if sitemap_links:
                sitemap_urls.append(url)
                for link in sitemap_links:
                    if link.url.lower().endswith((".xml", ".xml.gz")) and depth < policy.max_depth:
                        pending.append((link.url, depth + 1))
                    else:
                        paper_links.append(link.url)
            if feed_links:
                feed_urls.append(url)
                paper_links.extend(link.url for link in feed_links)
        paper_links = list(dict.fromkeys(paper_links))[: self.max_documents]
        candidates = PaperDiscovery(source, policy).candidates_from_links(
            ((f"{source_id}:live:{i}", url) for i, url in enumerate(paper_links, 1)), source_id)
        return LiveDiscoveryResult(robots_url, tuple(dict.fromkeys(sitemap_urls)), tuple(dict.fromkeys(feed_urls)), tuple(dict.fromkeys(archive_urls)), candidates)

    def _configured_seeds(self, source: SourceRecord) -> tuple[str, ...]:
        base = source.base_url.rstrip("/") + "/"
        return tuple(urljoin(base, path) for path in ("sitemap.xml", "sitemap_index.xml", "feed", "rss.xml", "archive"))

    def _unique_allowed(self, source, policy, parser, urls):
        result = []
        for url in dict.fromkeys(urls):
            try:
                validate_candidate_url(source, url, policy)
            except ResearchPolicyError:
                continue
            if parser.can_fetch(self.user_agent, url):
                result.append(url)
        return result

    def _archive_links(self, source, policy, parser, html, base_url):
        import re
        result = []
        for raw in re.findall(r'href\s*=\s*["\']([^"\']+)["\']', html, flags=re.I):
            url = urljoin(base_url, raw)
            try:
                validate_candidate_url(source, url, policy)
            except ResearchPolicyError:
                continue
            if parser.can_fetch(self.user_agent, url):
                result.append(url)
        return tuple(dict.fromkeys(result))