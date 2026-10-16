"""Policy- and size-bounded fetching for registered exam-paper candidates."""
from __future__ import annotations

from dataclasses import dataclass
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from ai_comp.domain.sources import CrawlPolicy, SourceRecord
from ai_comp.research.paper import DocumentFormat
from ai_comp.research.policy import ResearchPolicyError, validate_candidate_url
from ai_comp.research.processing import detect_document_format


@dataclass(frozen=True)
class DownloadedPaper:
    requested_url: str
    final_url: str
    content_type: str
    payload: bytes
    detected_format: DocumentFormat


class _RegisteredHostRedirectHandler(HTTPRedirectHandler):
    def __init__(
        self,
        source: SourceRecord,
        policy: CrawlPolicy,
        *,
        user_agent: str,
        robots: RobotFileParser | None,
        robots_request: bool = False,
    ) -> None:
        super().__init__()
        self.source = source
        self.policy = policy
        self.user_agent = user_agent
        self.robots = robots
        self.robots_request = robots_request

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        resolved_url = urljoin(req.full_url, newurl)
        parsed = urlparse(resolved_url)
        registered = urlparse(self.source.base_url)
        if parsed.scheme not in {"http", "https"} or parsed.netloc != registered.netloc:
            raise URLError("redirect outside registered source blocked")

        if not self.robots_request:
            validate_candidate_url(self.source, resolved_url, self.policy)
            if self.robots is None or not self.robots.can_fetch(self.user_agent, resolved_url):
                raise URLError("redirect disallowed by robots.txt")

        return super().redirect_request(req, fp, code, msg, headers, resolved_url)


class SafePaperDownloader:
    """Rechecks robots, blocks external redirects and caps downloaded bytes."""

    def __init__(
        self,
        *,
        user_agent: str = "AI-COMP/phase2.3",
        timeout_seconds: float = 20.0,
        max_bytes: int = 25 * 1024 * 1024,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes

    def download(
        self,
        source: SourceRecord,
        url: str,
        policy: CrawlPolicy,
    ) -> DownloadedPaper:
        validate_candidate_url(source, url, policy)
        robots_url = urljoin(source.base_url, "/robots.txt")
        robots_opener = build_opener(
            _RegisteredHostRedirectHandler(
                source,
                policy,
                user_agent=self.user_agent,
                robots=None,
                robots_request=True,
            )
        )
        robots_request = Request(
            robots_url,
            headers={"User-Agent": self.user_agent},
            method="GET",
        )
        try:
            with robots_opener.open(robots_request, timeout=self.timeout_seconds) as response:
                if response.status >= 400:
                    raise ResearchPolicyError("robots_unavailable")
                raw_robots = response.read(1024 * 1024 + 1)
                if len(raw_robots) > 1024 * 1024:
                    raise ResearchPolicyError("robots_too_large")
                if urlparse(response.geturl()).netloc != urlparse(source.base_url).netloc:
                    raise ResearchPolicyError("robots_redirect_outside_registered_source")
        except HTTPError as exc:
            raise ResearchPolicyError(
                "robots_unavailable" if exc.code >= 400 else "robots_request_failed"
            ) from None
        except (URLError, TimeoutError, OSError):
            raise ResearchPolicyError("robots_request_failed") from None

        parser = RobotFileParser(robots_url)
        parser.parse(raw_robots.decode("utf-8", errors="replace").splitlines())
        if not parser.can_fetch(self.user_agent, url):
            raise ResearchPolicyError("candidate_disallowed_by_robots")

        opener = build_opener(
            _RegisteredHostRedirectHandler(
                source,
                policy,
                user_agent=self.user_agent,
                robots=parser,
            )
        )
        request = Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/pdf,text/html,application/xhtml+xml,image/*,text/plain",
            },
            method="GET",
        )

        try:
            with opener.open(request, timeout=self.timeout_seconds) as response:
                final_url = response.geturl()
                if urlparse(final_url).netloc != urlparse(source.base_url).netloc:
                    raise ResearchPolicyError("redirect_outside_registered_source")
                content_type = response.headers.get("Content-Type", "application/octet-stream")
                declared_length = response.headers.get("Content-Length")
                if declared_length:
                    try:
                        if int(declared_length) > self.max_bytes:
                            raise ResearchPolicyError("paper_exceeds_size_limit")
                    except ValueError:
                        pass

                blocks: list[bytes] = []
                total = 0
                while True:
                    block = response.read(min(64 * 1024, self.max_bytes - total + 1))
                    if not block:
                        break
                    blocks.append(block)
                    total += len(block)
                    if total > self.max_bytes:
                        raise ResearchPolicyError("paper_exceeds_size_limit")
                    if policy.rate_limit_seconds > 0:
                        # Delay between network chunks would slow large PDFs too
                        # much; politeness is applied once before each document.
                        break
                if not blocks:
                    raise ResearchPolicyError("paper_download_empty")
                if policy.rate_limit_seconds > 0:
                    sleep(policy.rate_limit_seconds)
                payload = b"".join(blocks)

                # Keep reading until EOF, but still enforce the hard byte limit.
                while total <= self.max_bytes:
                    remaining = self.max_bytes - total
                    block = response.read(min(64 * 1024, remaining + 1))
                    if not block:
                        break
                    blocks.append(block)
                    total += len(block)
                    if total > self.max_bytes:
                        raise ResearchPolicyError("paper_exceeds_size_limit")
                payload = b"".join(blocks)
        except ResearchPolicyError:
            raise
        except HTTPError as exc:
            raise ResearchPolicyError(f"paper_http_{exc.code}") from None
        except (URLError, TimeoutError, OSError):
            raise ResearchPolicyError("paper_download_failed") from None

        detected = detect_document_format(payload, content_type, final_url)
        if detected is DocumentFormat.UNKNOWN:
            raise ResearchPolicyError("unsupported_document_format")
        return DownloadedPaper(
            requested_url=url,
            final_url=final_url,
            content_type=content_type,
            payload=payload,
            detected_format=detected,
        )


__all__ = ["DownloadedPaper", "SafePaperDownloader"]
