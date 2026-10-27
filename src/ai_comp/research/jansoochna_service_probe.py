"""Fail-closed inspection of the public Jan Soochna RSSB service index.

This diagnostic reads robots.txt first and, only when explicitly permitted,
reads the public /Services and /Scheme HTML pages. It never follows links
found in those pages, downloads exam documents, or writes to the database.
"""
from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser


HOST = "jansoochna.rajasthan.gov.in"
ORIGIN = f"https://{HOST}"
ROBOTS_URL = f"{ORIGIN}/robots.txt"
SERVICE_PATHS = ("/Services", "/Scheme")
USER_AGENT = "AI-COMP/phase2"
MAX_ROBOTS_BYTES = 128 * 1024
MAX_HTML_BYTES = 512 * 1024
DEFAULT_TIMEOUT_SECONDS = 1.5


@dataclass(frozen=True)
class FetchResult:
    status_code: int | None
    url: str
    content_type: str
    body: str = ""
    error: str | None = None


class _BlockedRedirect(ValueError):
    pass


class _SameHostHttpsRedirectHandler(HTTPRedirectHandler):
    """Allow HTTPS redirects only when the destination remains on the fixed host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        from urllib.parse import urljoin

        destination = urlsplit(urljoin(req.full_url, newurl))
        if (
            destination.scheme != "https"
            or destination.hostname != HOST
            or destination.port not in (None, 443)
            or destination.username is not None
            or destination.password is not None
        ):
            raise _BlockedRedirect("cross_host_or_insecure_redirect_blocked")
        return super().redirect_request(req, fp, code, msg, headers, destination.geturl())


def _safe_fetch_text(
    url: str,
    *,
    max_bytes: int,
    timeout_seconds: float,
) -> FetchResult:
    """GET a fixed same-host HTTPS URL with a strict byte limit and normal TLS."""
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
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain,text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
        },
    )
    opener = build_opener(_SameHostHttpsRedirectHandler())
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            final_url = response.geturl()
            final = urlsplit(final_url)
            if (
                final.scheme != "https"
                or final.hostname != HOST
                or final.port not in (None, 443)
                or final.username is not None
                or final.password is not None
            ):
                return FetchResult(None, url, "", error="cross_host_or_insecure_redirect_blocked")
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                return FetchResult(
                    None, final_url, response.headers.get_content_type(),
                    error="response_size_limit_exceeded",
                )
            return FetchResult(
                int(response.status),
                final_url,
                response.headers.get_content_type().lower(),
                raw.decode("utf-8", errors="replace"),
            )
    except HTTPError as exc:
        # Record only the HTTP status. Never include a body or server error text.
        return FetchResult(int(exc.code), url, exc.headers.get_content_type().lower())
    except _BlockedRedirect:
        return FetchResult(None, url, "", error="cross_host_or_insecure_redirect_blocked")
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
            attributes = dict(attrs)
            self._href = attributes.get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(" ".join(self._text).split())))
            self._href = None
            self._text = []


def _rssb_link_record(page_url: str, href: str, label: str) -> dict[str, object]:
    destination = urlsplit(urljoin(page_url, href))
    is_same_host = (
        destination.scheme == "https"
        and destination.hostname == HOST
        and destination.port in (None, 443)
        and destination.username is None
        and destination.password is None
    )
    if not is_same_host:
        return {
            "label": label[:160],
            "same_host": False,
            "status": "EXTERNAL_LINK_NOT_FOLLOWED",
            "target_host": destination.hostname or "",
        }
    clean_url = urlunsplit((
        "https",
        HOST,
        destination.path or "/",
        destination.query,
        "",
    ))
    return {
        "label": label[:160],
        "same_host": True,
        "status": "PUBLIC_LINK_FOUND_NOT_FETCHED",
        "url": clean_url,
    }


def _extract_rssb_links(page_url: str, body: str) -> dict[str, list[dict[str, object]]]:
    parser = _AnchorParser()
    parser.feed(body)
    papers: list[dict[str, object]] = []
    answer_keys: list[dict[str, object]] = []
    seen_papers: set[str] = set()
    seen_keys: set[str] = set()
    for href, label in parser.links:
        folded = " ".join(label.lower().split())
        is_papers = "rssb" in folded and "question paper" in folded
        is_answer_key = "rssb" in folded and "answer key" in folded
        if not (is_papers or is_answer_key) or not href:
            continue
        item = _rssb_link_record(page_url, href, label)
        key = str(item.get("url") or item.get("target_host") or "")
        if is_papers and key not in seen_papers:
            seen_papers.add(key)
            papers.append(item)
        if is_answer_key and key not in seen_keys:
            seen_keys.add(key)
            answer_keys.append(item)
    return {"question_papers": papers[:10], "answer_keys": answer_keys[:10]}


def probe_jansoochna_rssb_service(
    *,
    fetcher: Callable[..., FetchResult] | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, object]:
    """Inspect public RSSB service links only after robots.txt explicitly permits it.

    The probe follows no page links, returns no page body, and never downloads
    question papers or answer keys. It does not register an exam source.
    """
    if not 0.5 <= timeout_seconds <= 3.0:
        raise ValueError("timeout_seconds must be between 0.5 and 3.0")
    get_text = fetcher or _safe_fetch_text
    robots_result = get_text(
        ROBOTS_URL,
        max_bytes=MAX_ROBOTS_BYTES,
        timeout_seconds=timeout_seconds,
    )
    base: dict[str, object] = {
        "phase": "2.5-jansoochna-public-service-probe",
        "diagnostic_only": True,
        "host": HOST,
        "pages_fetched": [],
        "source_registry_modified": False,
        "paper_bytes_fetched": False,
    }
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
    if not robots_result.content_type.startswith("text/plain"):
        return {
            **base,
            "status": "ROBOTS_CONTENT_TYPE_INVALID",
            "robots": {
                "status": "CONTENT_TYPE_INVALID",
                "content_type": robots_result.content_type[:80],
            },
        }

    parser = RobotFileParser(ROBOTS_URL)
    parser.parse(robots_result.body.splitlines())
    robots_summary: dict[str, object] = {
        "status": "READ",
        "http_status": 200,
        "can_fetch_services": parser.can_fetch(USER_AGENT, f"{ORIGIN}/Services"),
        "can_fetch_scheme": parser.can_fetch(USER_AGENT, f"{ORIGIN}/Scheme"),
    }
    base["robots"] = robots_summary
    pages: list[dict[str, object]] = []
    for path, permission_key in (
        ("/Services", "can_fetch_services"),
        ("/Scheme", "can_fetch_scheme"),
    ):
        if not robots_summary[permission_key]:
            pages.append({"path": path, "status": "BLOCKED_BY_ROBOTS"})
            continue
        page_url = f"{ORIGIN}{path}"
        page = get_text(
            page_url,
            max_bytes=MAX_HTML_BYTES,
            timeout_seconds=timeout_seconds,
        )
        record: dict[str, object] = {"path": path}
        if page.error:
            record.update({"status": "FETCH_ERROR", "error_type": page.error})
        elif page.status_code != 200:
            record.update({"status": "HTTP_ERROR", "http_status": page.status_code})
        elif page.content_type not in {"text/html", "application/xhtml+xml"}:
            record.update({
                "status": "CONTENT_TYPE_INVALID",
                "http_status": page.status_code,
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
            ):
                record.update({"status": "REDIRECT_BLOCKED"})
            else:
                links = _extract_rssb_links(page.url, page.body)
                record.update({
                    "status": "READ_ONLY_PUBLIC_HTML",
                    "http_status": 200,
                    "final_path": final.path,
                    **links,
                })
        pages.append(record)

    base["pages_fetched"] = pages
    paper_links = [
        link for page in pages if isinstance(page.get("question_papers"), list)
        for link in page["question_papers"]
    ]
    key_links = [
        link for page in pages if isinstance(page.get("answer_keys"), list)
        for link in page["answer_keys"]
    ]
    if any(link.get("same_host") for link in paper_links):
        status = "SAME_HOST_RSSB_PAPER_SERVICE_LINK_FOUND"
    elif paper_links:
        status = "RSSB_PAPER_LINK_POINTS_TO_OTHER_HOST"
    elif any(link.get("same_host") for link in key_links):
        status = "SAME_HOST_RSSB_ANSWER_KEY_SERVICE_LINK_FOUND"
    elif key_links:
        status = "RSSB_ANSWER_KEY_LINK_POINTS_TO_OTHER_HOST"
    elif all(page.get("status") == "BLOCKED_BY_ROBOTS" for page in pages):
        status = "PUBLIC_PAGES_BLOCKED_BY_ROBOTS"
    elif any(page.get("status") == "READ_ONLY_PUBLIC_HTML" for page in pages):
        status = "RSSB_SERVICE_LINKS_NOT_FOUND"
    else:
        status = "PUBLIC_SERVICE_PAGE_UNAVAILABLE"
    return {**base, "status": status, "robots": robots_summary, "pages_fetched": pages}
