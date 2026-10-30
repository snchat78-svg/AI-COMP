"""Read-only, robots-first inspection of the fixed RBSE 2025 paper index.

The RBSE school-board archive is kept separate from RSSB/RPSC competitive-exam
sources. This probe reads one permitted public HTML index only. It never follows
PDF links, fetches paper bytes, changes the source registry, or writes the DB.
"""
from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, OpenerDirector, Request, build_opener
from urllib.robotparser import RobotFileParser

from ai_comp.research.recruitment_portal_probe import _robots_allows_url


HOST = "rajeduboard.rajasthan.gov.in"
ORIGIN = f"https://{HOST}"
INDEX_PATH = "/books/PAPERS-2025/index.htm"
ROBOTS_URL = f"{ORIGIN}/robots.txt"
INDEX_URL = f"{ORIGIN}{INDEX_PATH}"
USER_AGENT = "AI-COMP/phase2"
MAX_ROBOTS_BYTES = 128 * 1024
MAX_HTML_BYTES = 512 * 1024
DEFAULT_TIMEOUT_SECONDS = 1.0
MAX_PDF_LINKS = 200


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


class _PdfAnchorParser(HTMLParser):
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


def _safe_fetch_text(
    url: str,
    *,
    max_bytes: int,
    timeout_seconds: float,
    allowed_content_types: tuple[str, ...],
    opener: OpenerDirector | None = None,
) -> FetchResult:
    """Fetch only the two fixed same-host text resources using normal TLS."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != HOST
        or parsed.port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"/robots.txt", INDEX_PATH}
        or parsed.query
        or parsed.fragment
    ):
        return FetchResult(None, url, "", error="fixed_host_url_rejected")

    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": ",".join(allowed_content_types),
        },
    )
    try:
        with (opener or build_opener(_NoRedirectHandler())).open(
            request, timeout=timeout_seconds
        ) as response:
            final = urlsplit(response.geturl())
            if (
                final.scheme != "https"
                or final.hostname != HOST
                or final.port not in (None, 443)
                or final.username is not None
                or final.password is not None
                or final.path != parsed.path
                or final.query
            ):
                return FetchResult(None, url, "", error="redirect_target_rejected")
            content_type = response.headers.get_content_type().lower()
            if content_type not in allowed_content_types:
                return FetchResult(
                    int(response.status), final.geturl(), content_type,
                    error="content_type_not_allowed",
                )
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                return FetchResult(
                    None, final.geturl(), content_type,
                    error="response_size_limit_exceeded",
                )
            return FetchResult(
                int(response.status),
                final.geturl(),
                content_type,
                raw.decode("utf-8", errors="replace"),
            )
    except HTTPError as exc:
        return FetchResult(
            int(exc.code),
            url,
            exc.headers.get_content_type().lower(),
            redirect_location=exc.headers.get("Location"),
        )
    except (URLError, TimeoutError, OSError) as exc:
        return FetchResult(None, url, "", error=type(exc).__name__)


def _pdf_link_records(
    page_url: str,
    body: str,
    *,
    robots_parser: RobotFileParser | None,
) -> list[dict[str, object]]:
    parser = _PdfAnchorParser()
    parser.feed(body)
    output: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for href, label in parser.links:
        if not href:
            continue
        target = urlsplit(urljoin(page_url, href))
        if not target.path.lower().endswith(".pdf"):
            continue
        key = (target.hostname or "", target.path)
        if key in seen:
            continue
        seen.add(key)
        same_host = (
            target.scheme == "https"
            and target.hostname == HOST
            and target.port in (None, 443)
            and target.username is None
            and target.password is None
            and target.path.startswith("/books/PAPERS-2025/")
        )
        robots_allowed: bool | None = None
        if same_host and robots_parser is not None:
            robots_allowed = _robots_allows_url(
                robots_parser, USER_AGENT, target.geturl()
            )
        if not same_host:
            status = "EXTERNAL_OR_OUT_OF_SCOPE_PDF_NOT_FOLLOWED"
        elif robots_allowed is None:
            # The exact-404 exception authorizes reading only the fixed HTML
            # index; it does not silently authorize linked PDF paths.
            status = "PDF_ROBOTS_NOT_EVALUATED"
        elif robots_allowed:
            status = "PDF_ROBOTS_ALLOWED_NOT_FETCHED"
        else:
            status = "PDF_BLOCKED_BY_ROBOTS"
        row: dict[str, object] = {
            "label": label[:160],
            "target_host": (target.hostname or "")[:120],
            "path": target.path[:240],
            "same_host": same_host,
            "query_present": bool(target.query),
            "robots_allowed": robots_allowed,
            "status": status,
        }
        output.append(row)
        if len(output) >= MAX_PDF_LINKS:
            break
    return output


def probe_rbse_archive_route(
    *,
    fetcher: Callable[..., FetchResult] | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, object]:
    """Check robots first, then read only the one fixed public paper index."""
    if not 0.5 <= timeout_seconds <= 3.0:
        raise ValueError("timeout_seconds must be between 0.5 and 3.0")
    get_text = fetcher or _safe_fetch_text
    base: dict[str, object] = {
        "phase": "2.2-rbse-archive-route-probe",
        "diagnostic_only": True,
        "host": HOST,
        "board_id": "RBSE",
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

    # RFC 9309 treats a 4xx robots response as unavailable. This implementation
    # adopts only the narrow 404 case (robots file not published), and then
    # requests just the one fixed, public index path. 403/429/5xx and all
    # network/TLS errors continue to fail closed.
    robots_missing_404 = robots_result.status_code == 404
    if robots_result.status_code != 200 and not robots_missing_404:
        return {
            **base,
            "status": "ROBOTS_UNAVAILABLE",
            "robots": {
                "status": "HTTP_ERROR",
                "http_status": robots_result.status_code,
            },
        }

    robots_parser: RobotFileParser | None = None
    if robots_missing_404:
        robots: dict[str, object] = {
            "status": "NOT_PUBLISHED_HTTP_404",
            "http_status": 404,
            "policy": "RFC9309_4XX_UNAVAILABLE_FIXED_INDEX_ONLY",
            "allowed_index_path": True,
        }
    else:
        if robots_result.content_type != "text/plain":
            return {
                **base,
                "status": "ROBOTS_CONTENT_TYPE_INVALID",
                "robots": {
                    "status": "CONTENT_TYPE_INVALID",
                    "content_type": robots_result.content_type[:80],
                },
            }
        robots_parser = RobotFileParser(ROBOTS_URL)
        robots_parser.parse(robots_result.body.splitlines())
        allowed = _robots_allows_url(robots_parser, USER_AGENT, INDEX_URL)
        robots = {
            "status": "READ",
            "http_status": 200,
            "allowed_index_path": allowed,
        }

    base["robots"] = robots
    if not robots["allowed_index_path"]:
        base["status"] = "PUBLIC_INDEX_BLOCKED_BY_ROBOTS"
        return base

    page = get_text(
        INDEX_URL,
        max_bytes=MAX_HTML_BYTES,
        timeout_seconds=timeout_seconds,
        allowed_content_types=("text/html", "application/xhtml+xml"),
    )
    row: dict[str, object] = {
        "path": INDEX_PATH,
        "status": "FETCH_ERROR",
        "pdf_links": [],
    }
    if page.error:
        row.update({"error_type": page.error})
    elif page.status_code != 200:
        row.update({"status": "HTTP_ERROR", "http_status": page.status_code})
        if page.status_code in (301, 302, 303, 307, 308):
            row["status"] = "REDIRECT_NOT_FOLLOWED"
    elif page.content_type not in {"text/html", "application/xhtml+xml"}:
        row.update({
            "status": "CONTENT_TYPE_INVALID",
            "content_type": page.content_type[:80],
        })
    else:
        final = urlsplit(page.url)
        if (
            final.scheme != "https"
            or final.hostname != HOST
            or final.port not in (None, 443)
            or final.username is not None
            or final.password is not None
            or final.path != INDEX_PATH
        ):
            row["status"] = "REDIRECT_BLOCKED"
        else:
            links = _pdf_link_records(
                page.url, page.body, robots_parser=robots_parser
            )
            row.update({
                "status": "READ_ONLY_PUBLIC_HTML",
                "pdf_links": links,
            })
    base["pages_inspected"] = [row]

    if row["status"] == "READ_ONLY_PUBLIC_HTML":
        links = row["pdf_links"]
        if any(
            link["status"] in {
                "PDF_ROBOTS_ALLOWED_NOT_FETCHED",
                "PDF_BLOCKED_BY_ROBOTS",
                "PDF_ROBOTS_NOT_EVALUATED",
            }
            for link in links
        ):
            base["status"] = "SAME_HOST_PAPER_LINKS_FOUND_NOT_FETCHED"
        elif links:
            base["status"] = "PDF_LINKS_OUT_OF_SCOPE_NOT_FOLLOWED"
        else:
            base["status"] = "PUBLIC_INDEX_READ_NO_PDF_LINK_FOUND"
    else:
        base["status"] = "PUBLIC_INDEX_UNAVAILABLE"
    return base
