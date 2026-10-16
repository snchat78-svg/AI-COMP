from dataclasses import dataclass, replace
from html import unescape
from datetime import datetime, timezone
from hashlib import sha256
from time import sleep
from urllib.parse import urljoin, urlparse
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
    """Small bounded HTTP transport with retries for transient network failures."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        retries: int = 2,
        retry_delay_seconds: float = 0.5,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if retries < 0:
            raise ValueError("retries cannot be negative")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds

    def get(self, url: str) -> HttpResponse:
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen

        request = Request(url, headers={"User-Agent": "AI-COMP/phase2"})
        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read()
                    return HttpResponse(
                        response.geturl(),
                        response.status,
                        body.decode("utf-8", errors="replace"),
                        response.headers.get("Content-Type", ""),
                    )
            except HTTPError as response:
                # HTTP status responses are not transport failures. Preserve
                # existing policy handling for 403/404/429 and other statuses.
                body = response.read()
                return HttpResponse(
                    response.geturl(),
                    response.code,
                    body.decode("utf-8", errors="replace"),
                    response.headers.get("Content-Type", ""),
                )
            except (URLError, TimeoutError, OSError):
                if attempt >= self.retries:
                    raise
                sleep(self.retry_delay_seconds * (2**attempt))
        raise RuntimeError("unreachable HTTP retry state")

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
        declared_seeds = list(parser.site_maps() or [])
        seeds = declared_seeds if declared_seeds else list(self._configured_seeds(source))
        # RPSC publishes its previous-paper archive at a stable route outside
        # the generic sitemap/feed paths. Include this registered adapter seed
        # even when the robots file declares a sitemap, subject to robots rules.
        if source.source_id == "RSSB_OFFICIAL":
            # These are official RSSB archive pages currently used for question
            # papers and answer keys. They remain subject to the same robots.txt
            # and same-host gates as sitemap-discovered URLs.
            seeds.extend((
                urljoin(
                    source.base_url,
                    "show_archived?menuName=Xj4lCb9vGxpQnfLs/xlZ2g==&theme=Default",
                ),
                urljoin(
                    source.base_url,
                    "show_archived?menuName=AGDAnN3xlANlxQ9BZvzaeg==&theme=Red",
                ),
            ))
        if source.source_id == "RPSC_OFFICIAL":
            seeds.extend((
                urljoin(source.base_url, "previousquestionpapers.aspx"),
                urljoin(source.base_url, "answerkeys.aspx"),
                urljoin(source.base_url, "Static/AnswerKeys/"),
            ))
        seeds = self._unique_allowed(source, policy, parser, seeds)
        sitemap_urls, feed_urls, archive_urls, paper_links = [], [], [], []
        paper_link_titles: dict[str, str] = {}
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
                for link_url, link_title in self._archive_link_records(
                    source, policy, parser, response.content, response.url
                ):
                    paper_links.append(link_url)
                    if link_title and link_url not in paper_link_titles:
                        paper_link_titles[link_url] = link_title
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
        # Candidate identity must remain stable across runs and link ordering.
        # An index-based ID can overwrite a different URL when a sitemap changes.
        candidates = PaperDiscovery(source, policy).candidates_from_links(
            (
                (f"{source_id}:live:{sha256(url.encode()).hexdigest()[:40]}", url)
                for url in paper_links
            ),
            source_id,
        )
        discovered_at = datetime.now(timezone.utc).isoformat()
        candidates = tuple(
            replace(
                candidate,
                title=paper_link_titles.get(candidate.url) or candidate.title,
                discovered_at=discovered_at,
            )
            for candidate in candidates
        )
        return LiveDiscoveryResult(robots_url, tuple(dict.fromkeys(sitemap_urls)), tuple(dict.fromkeys(feed_urls)), tuple(dict.fromkeys(archive_urls)), candidates)

    def _configured_seeds(self, source: SourceRecord) -> tuple[str, ...]:
        base = source.base_url.rstrip("/") + "/"
        return tuple(urljoin(base, path) for path in ("sitemap.xml", "sitemap_index.xml", "feed", "rss.xml", "archive"))

    def _unique_allowed(self, source, policy, parser, urls):
        """Allow crawl-control URLs (sitemaps/feeds) on the registered host.

        Paper path restrictions are applied when paper candidates are created;
        they must not block a source's own sitemap or feed endpoints.
        """
        result = []
        base = urlparse(source.base_url)
        for url in dict.fromkeys(urls):
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or parsed.netloc != base.netloc:
                continue
            if parser.can_fetch(self.user_agent, url):
                result.append(url)
        return result

    def _archive_links(self, source, policy, parser, html, base_url):
        """Compatibility wrapper returning only URLs from archive pages."""
        return tuple(
            url for url, _title in self._archive_link_records(
                source, policy, parser, html, base_url
            )
        )

    def _archive_link_records(self, source, policy, parser, html, base_url):
        """Extract same-host allowed links together with visible archive labels."""
        import re

        result: list[tuple[str, str]] = []
        seen: set[str] = set()
        anchor_pattern = re.compile(
            r"""<a\b[^>]*?href\s*=\s*["']([^"']+)["'][^>]*>(.*?)</a\s*>""",
            flags=re.I | re.S,
        )
        for match in anchor_pattern.finditer(html):
            url = urljoin(base_url, match.group(1).strip())
            try:
                validate_candidate_url(source, url, policy)
            except ResearchPolicyError:
                continue
            if not parser.can_fetch(self.user_agent, url) or url in seen:
                continue
            seen.add(url)
            label = re.sub(r"<[^>]+>", " ", match.group(2))
            label = re.sub(r"\s+", " ", unescape(label)).strip()
            result.append((url, label))
        return tuple(result)
