"""Read-only, robots-first inspection of the public Rajasthan Recruitment Portal.

This is a route diagnostic only. It does not admit a source, fetch linked
documents, or write to the database.
"""
from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, OpenerDirector, Request, build_opener
from urllib.robotparser import RobotFileParser


HOST = "recruitment.rajasthan.gov.in"
ORIGIN = f"https://{HOST}"
ROBOTS_URL = f"{ORIGIN}/robots.txt"
INDEX_PATHS = ("/", "/recruitmentservlet", "/departmentrecservlet")
USER_AGENT = "AI-COMP/phase2"
MAX_ROBOTS_BYTES = 128 * 1024
MAX_HTML_BYTES = 512 * 1024
DEFAULT_TIMEOUT_SECONDS = 1.0
MAX_LINKS_PER_PAGE = 20


@dataclass(frozen=True)
class FetchResult:
    status_code: int | None
    url: str
    content_type: str
    body: str = ""
    error: str | None = None
    redirect_location: str | None = None


class _NoRedirectHandler(HTTPRedirectHandler):
    """Require explicit review of redirects; this probe never follows them."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _safe_fetch_text(
    url: str,
    *,
    max_bytes: int,
    timeout_seconds: float,
    allowed_content_types: tuple[str, ...],
    opener: OpenerDirector | None = None,
) -> FetchResult:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != HOST
        or parsed.port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
    ):
        return FetchResult(None, url, "", error="fixed_host_url_rejected")

    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": ",".join(allowed_content_types)},
    )
    try:
        with (opener or build_opener(_NoRedirectHandler())).open(
            request, timeout=timeout_seconds
        ) as response:
            final_url = response.geturl()
            final = urlsplit(final_url)
            if (
                final.scheme != "https"
                or final.hostname != HOST
                or final.port not in (None, 443)
                or final.username is not None
                or final.password is not None
            ):
                return FetchResult(None, url, "", error="redirect_target_rejected")
            content_type = response.headers.get_content_type().lower()
            if content_type not in allowed_content_types:
                return FetchResult(
                    int(response.status), final_url, content_type,
                    error="content_type_not_allowed",
                )
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                return FetchResult(None, final_url, content_type, error="response_size_limit_exceeded")
            return FetchResult(
                int(response.status),
                final_url,
                content_type,
                raw.decode("utf-8", errors="replace"),
            )
    except HTTPError as exc:
        return FetchResult(
            int(exc.code), url, exc.headers.get_content_type().lower(),
            redirect_location=exc.headers.get("Location"),
        )
    except (URLError, TimeoutError, OSError) as exc:
        return FetchResult(None, url, "", error=type(exc).__name__)


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a" and self._href is None:
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(" ".join(self._text).split())))
            self._href = None
            self._text = []


def _paper_link_records(page_url: str, body: str) -> list[dict[str, object]]:
    parser = _AnchorParser()
    parser.feed(body)
    output: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    markers = ("question paper", "question-paper", "questionpaper", "answer key", "answer-key", "answerkey")
    for href, label in parser.links:
        if not href:
            continue
        folded = " ".join(label.lower().split())
        target = urlsplit(urljoin(page_url, href))
        path_folded = target.path.lower()
        if not any(marker in folded or marker in path_folded for marker in markers):
            continue
        is_same_host = (
            target.scheme == "https"
            and target.hostname == HOST
            and target.port in (None, 443)
            and target.username is None
            and target.password is None
        )
        key = (target.hostname or "", target.path)
        if key in seen:
            continue
        seen.add(key)
        row: dict[str, object] = {
            "label": label[:160],
            "same_host": is_same_host,
            "target_host": target.hostname or "",
            "path": target.path[:240],
            "query_present": bool(target.query),
            "status": "PUBLIC_LINK_FOUND_NOT_FETCHED",
        }
        if target.scheme != "https":
            row["status"] = "INSECURE_LINK_NOT_FOLLOWED"
        elif not is_same_host:
            row["status"] = "EXTERNAL_LINK_NOT_FOLLOWED"
        output.append(row)
        if len(output) >= MAX_LINKS_PER_PAGE:
            break
    return output


def probe_recruitment_portal_route(
    *,
    fetcher: Callable[..., FetchResult] | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, object]:
    """Check robots first and inspect only fixed, public portal index pages."""
    if not 0.5 <= timeout_seconds <= 3.0:
        raise ValueError("timeout_seconds must be between 0.5 and 3.0")
    get_text = fetcher or _safe_fetch_text
    base: dict[str, object] = {
        "phase": "2.2-recruitment-portal-route-probe",
        "diagnostic_only": True,
        "host": HOST,
        "pages_inspected": [],
        "source_registry_modified": False,
        "paper_bytes_fetched": False,
        "database_written": False,
        "candidate_promotions": 0,
    }
    robots_result = get_text(
        ROBOTS_URL,
        max_bytes=MAX_ROBOTS_BYTES,
        timeout_seconds=timeout_seconds,
        allowed_content_types=("text/plain",),
    )
    if robots_result.error:
        return {
            **base,
            "status": "ROBOTS_UNAVAILABLE",
            "robots": {"status": "FETCH_ERROR", "error_type": robots_result.error},
        }
    if robots_result.status_code != 200:
        return {
            **base,
            "status": "ROBOTS_UNAVAILABLE",
            "robots": {"status": "HTTP_ERROR", "http_status": robots_result.status_code},
        }
    if robots_result.content_type != "text/plain":
        return {
            **base,
            "status": "ROBOTS_CONTENT_TYPE_INVALID",
            "robots": {"status": "CONTENT_TYPE_INVALID", "content_type": robots_result.content_type[:80]},
        }

    parser = RobotFileParser(ROBOTS_URL)
    parser.parse(robots_result.body.splitlines())
    robots: dict[str, object] = {
        "status": "READ",
        "http_status": 200,
        "allowed_index_paths": {
            path: parser.can_fetch(USER_AGENT, f"{ORIGIN}{path}")
            for path in INDEX_PATHS
        },
    }
    base["robots"] = robots
    pages: list[dict[str, object]] = []
    for path in INDEX_PATHS:
        if not robots["allowed_index_paths"][path]:
            pages.append({"path": path, "status": "BLOCKED_BY_ROBOTS", "paper_links": []})
            continue
        url = f"{ORIGIN}{path}"
        page = get_text(
            url,
            max_bytes=MAX_HTML_BYTES,
            timeout_seconds=timeout_seconds,
            allowed_content_types=("text/html", "application/xhtml+xml"),
        )
        row: dict[str, object] = {"path": path, "paper_links": []}
        if page.error:
            row.update({"status": "FETCH_ERROR", "error_type": page.error})
        elif page.status_code != 200:
            row.update({"status": "HTTP_ERROR", "http_status": page.status_code})
        elif page.content_type not in {"text/html", "application/xhtml+xml"}:
            row.update({"status": "CONTENT_TYPE_INVALID", "content_type": page.content_type[:80]})
        else:
            final = urlsplit(page.url)
            if (
                final.scheme != "https"
                or final.hostname != HOST
                or final.port not in (None, 443)
                or final.username is not None
                or final.password is not None
            ):
                row["status"] = "REDIRECT_BLOCKED"
            else:
                links = _paper_link_records(page.url, page.body)
                row.update({
                    "status": "READ_ONLY_PUBLIC_HTML",
                    "final_path": final.path[:240],
                    "paper_links": links,
                })
        pages.append(row)
    base["pages_inspected"] = pages

    same_host_links = [
        item for page in pages if isinstance(page.get("paper_links"), list)
        for item in page["paper_links"]
        if isinstance(item, dict) and item.get("same_host") is True
        and item.get("status") == "PUBLIC_LINK_FOUND_NOT_FETCHED"
    ]
    external_links = [
        item for page in pages if isinstance(page.get("paper_links"), list)
        for item in page["paper_links"]
        if isinstance(item, dict) and item.get("status") == "EXTERNAL_LINK_NOT_FOLLOWED"
    ]
    if same_host_links:
        base["status"] = "SAME_HOST_PAPER_OR_KEY_LINK_FOUND_NOT_FETCHED"
    elif external_links:
        base["status"] = "PAPER_OR_KEY_LINK_POINTS_TO_OTHER_HOST"
    elif all(page.get("status") == "BLOCKED_BY_ROBOTS" for page in pages):
        base["status"] = "PUBLIC_INDEX_BLOCKED_BY_ROBOTS"
    elif any(page.get("status") == "READ_ONLY_PUBLIC_HTML" for page in pages):
        base["status"] = "PUBLIC_INDEX_READ_BUT_NO_PAPER_OR_KEY_LINK_FOUND"
    else:
        base["status"] = "PUBLIC_INDEX_UNAVAILABLE"
    return base
