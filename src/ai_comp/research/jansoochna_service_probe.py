"""Fail-closed inspection of the public Jan Soochna RSSB service index.

This diagnostic reads robots.txt first and, only when explicitly permitted,
reads the public /Services and /Scheme HTML pages. It never follows links
found in those pages, downloads exam documents, or writes to the database.
"""
from __future__ import annotations

from dataclasses import dataclass
from http.cookiejar import CookieJar
import json
from html.parser import HTMLParser
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urljoin, urlparse, urlsplit, urlunparse, urlunsplit
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, OpenerDirector, Request, build_opener
from urllib.robotparser import RobotFileParser


HOST = "jansoochna.rajasthan.gov.in"
ORIGIN = f"https://{HOST}"
ROBOTS_URL = f"{ORIGIN}/robots.txt"
SERVICE_PATHS = ("/Services", "/Scheme")
USER_AGENT = "AI-COMP/phase2"
MAX_ROBOTS_BYTES = 128 * 1024
MAX_HTML_BYTES = 512 * 1024
MAX_DETAIL_BYTES = 512 * 1024
MAX_SERVICE_LINK_INSPECTIONS = 4
DEFAULT_TIMEOUT_SECONDS = 1.5


@dataclass(frozen=True)
class FetchResult:
    status_code: int | None
    url: str
    content_type: str
    body: str = ""
    error: str | None = None
    redirect_location: str | None = None


class _BlockedRedirect(ValueError):
    pass


class _NoRedirectHandler(HTTPRedirectHandler):
    """Do not follow redirects before checking robots permissions for the target."""

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
    """GET a fixed same-host HTTPS URL, refusing redirects and unknown/binary bodies."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != HOST
        or parsed.port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
    ):
        return FetchResult(None, url, "", error="fixed_host_url_rejected")

    accept_header = ",".join(allowed_content_types)
    if parsed.path == "/robots.txt":
        # Keep the expected plain-text media type preferred, while allowing
        # ordinary HTTP content negotiation rather than forcing only one type.
        # The response is still required to be text/plain before parsing.
        accept_header = "text/plain, */*;q=0.8"

    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept_header,
        },
    )
    active_opener = opener or build_opener(_NoRedirectHandler())
    try:
        with active_opener.open(request, timeout=timeout_seconds) as response:
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
            content_type = response.headers.get_content_type().lower()
            # Reject binary content before reading any body bytes; in particular,
            # a service link must never cause a PDF download.
            if content_type not in allowed_content_types:
                return FetchResult(
                    int(response.status), final_url, content_type,
                    error="content_type_not_allowed",
                )
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                return FetchResult(None, final_url, content_type, error="response_size_limit_exceeded")
            return FetchResult(int(response.status), final_url, content_type, raw.decode("utf-8", errors="replace"))
    except HTTPError as exc:
        # Do not follow redirects or read their bodies. Preserve only the Location
        # header as metadata; the reporter later strips query/fragment details.
        return FetchResult(
            int(exc.code),
            url,
            exc.headers.get_content_type().lower(),
            redirect_location=exc.headers.get("Location"),
        )
    except (URLError, TimeoutError, OSError) as exc:
        return FetchResult(None, url, "", error=type(exc).__name__)


def _build_session_fetcher() -> Callable[..., FetchResult]:
    """Create an ephemeral cookie-aware transport that never follows redirects.

    Some public portals set session cookies on a redirect response. Preserve
    those cookies only for this single probe run so the next explicitly
    robots-approved same-host request can be evaluated in its intended session.
    The cookie jar is never persisted or included in the diagnostic report.
    """
    cookie_jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar), _NoRedirectHandler())

    def fetch(
        url: str,
        *,
        max_bytes: int,
        timeout_seconds: float,
        allowed_content_types: tuple[str, ...],
    ) -> FetchResult:
        return _safe_fetch_text(
            url,
            max_bytes=max_bytes,
            timeout_seconds=timeout_seconds,
            allowed_content_types=allowed_content_types,
            opener=opener,
        )

    return fetch


def _robots_allows_url(parser: RobotFileParser, user_agent: str, url: str) -> bool:
    """Apply the most-specific matching robots rule (Allow wins equal-length ties).

    urllib.robotparser currently evaluates the first matching rule, which can
    incorrectly allow a path when a broad Allow appears before a narrower
    Disallow. Keep its group parsing but resolve precedence by rule specificity.
    """
    if parser.disallow_all:
        return False
    if parser.allow_all:
        return True
    if not parser.last_checked:
        return False

    specific_entries = [
        entry
        for entry in parser.entries
        if entry.applies_to(user_agent)
        and not any(agent.strip() == "*" for agent in entry.useragents)
    ]
    if specific_entries:
        entries = specific_entries
    elif parser.default_entry is not None:
        entries = [parser.default_entry]
    else:
        return True

    parsed = urlparse(unquote(url))
    filename = urlunparse(("", "", parsed.path, parsed.params, parsed.query, parsed.fragment))
    filename = quote(filename)
    matching_rules = [
        rule
        for entry in entries
        for rule in entry.rulelines
        if rule.applies_to(filename)
    ]
    if not matching_rules:
        return True
    longest = max(len(rule.path) for rule in matching_rules)
    most_specific = [rule for rule in matching_rules if len(rule.path) == longest]
    return any(rule.allowance for rule in most_specific)


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



def _extract_document_links(
    page_url: str,
    body: str,
    content_type: str,
) -> list[dict[str, object]]:
    """Report likely document links from a public service response without following them."""
    candidates: list[tuple[str, str]] = []
    if content_type in {"text/html", "application/xhtml+xml"}:
        parser = _AnchorParser()
        parser.feed(body)
        candidates = list(parser.links)
    elif content_type == "application/json":
        def walk(value: object) -> list[str]:
            if isinstance(value, str):
                return [value]
            if isinstance(value, list):
                return [part for child in value for part in walk(child)]
            if isinstance(value, dict):
                return [part for child in value.values() for part in walk(child)]
            return []

        try:
            payload = json.loads(body)
        except (TypeError, ValueError):
            return []
        for value in walk(payload):
            folded = value.lower()
            if ".pdf" in folded or ".ashx" in folded or "download" in folded:
                candidates.append((value, value.rsplit("/", 1)[-1][:160]))

    output: list[dict[str, object]] = []
    seen: set[str] = set()
    for href, label in candidates:
        if not href:
            continue
        destination = urlsplit(urljoin(page_url, href))
        folded_label = " ".join(label.lower().split())
        is_pdf = destination.path.lower().endswith(".pdf")
        relevant_label = any(
            marker in folded_label
            for marker in ("paper", "answer key", "rssb", "question", "cet", "graduation")
        )
        if not is_pdf and not relevant_label and not any(
            marker in href.lower() for marker in (".pdf", ".ashx", "download")
        ):
            continue
        item = _rssb_link_record(page_url, href, label)
        dedupe_key = str(item.get("url") or item.get("target_host") or "")
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        item["kind"] = "PDF_CANDIDATE_LINK_NOT_FETCHED" if is_pdf or ".pdf" in href.lower() else "RELATED_PUBLIC_LINK_NOT_FETCHED"
        output.append(item)
        if len(output) >= 30:
            break
    return output


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
    # Reuse an ephemeral cookie jar across this probe's bounded requests. Injected
    # test fetchers remain isolated and do not get an implicit network session.
    get_text = fetcher if fetcher is not None else _build_session_fetcher()
    robots_result = get_text(
        ROBOTS_URL,
        max_bytes=MAX_ROBOTS_BYTES,
        timeout_seconds=timeout_seconds,
        allowed_content_types=("text/plain",),
    )
    base: dict[str, object] = {
        "phase": "2.5-jansoochna-public-service-probe",
        "diagnostic_only": True,
        "host": HOST,
        "pages_fetched": [],
        "service_link_inspections": [],
        "service_page_bytes_fetched": False,
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
            allowed_content_types=("text/html", "application/xhtml+xml"),
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
    # Inspect a bounded number of same-host service links exposed by the permitted
    # index pages. Each exact URL is checked against robots before fetching. No
    # redirects are followed, and document/PDF links found on detail pages stay
    # as metadata only; this function never requests them.
    observed_service_links: list[dict[str, object]] = []
    seen_service_urls: set[str] = set()
    for page in pages:
        for field in ("question_papers", "answer_keys"):
            links = page.get(field, [])
            if not isinstance(links, list):
                continue
            for link in links:
                if not isinstance(link, dict) or link.get("same_host") is not True:
                    continue
                service_url = link.get("url")
                if not isinstance(service_url, str) or service_url in seen_service_urls:
                    continue
                seen_service_urls.add(service_url)
                if len(observed_service_links) >= MAX_SERVICE_LINK_INSPECTIONS:
                    break
                parsed = urlsplit(service_url)
                if (
                    parsed.scheme != "https"
                    or parsed.hostname != HOST
                    or parsed.port not in (None, 443)
                    or parsed.username is not None
                    or parsed.password is not None
                ):
                    continue
                observed_service_links.append({
                    "url": service_url,
                    "label": str(link.get("label", ""))[:160],
                    "field": field,
                })
            if len(observed_service_links) >= MAX_SERVICE_LINK_INSPECTIONS:
                break
        if len(observed_service_links) >= MAX_SERVICE_LINK_INSPECTIONS:
            break

    service_link_inspections: list[dict[str, object]] = []
    for link in observed_service_links:
        service_url = str(link["url"])
        parsed = urlsplit(service_url)
        permission = _robots_allows_url(parser, USER_AGENT, service_url)
        inspection: dict[str, object] = {
            "path": parsed.path or "/",
            "label": link["label"],
            "field": link["field"],
            "robots_allowed": permission,
            "document_links": [],
        }
        if not permission:
            inspection["status"] = "BLOCKED_BY_ROBOTS"
            service_link_inspections.append(inspection)
            continue

        detail = get_text(
            service_url,
            max_bytes=MAX_DETAIL_BYTES,
            timeout_seconds=timeout_seconds,
            allowed_content_types=(
                "text/html",
                "application/xhtml+xml",
                "application/json",
                "text/plain",
            ),
        )
        if detail.error == "content_type_not_allowed":
            inspection.update({
                "status": "CONTENT_TYPE_NOT_READ",
                "http_status": detail.status_code,
                "content_type": detail.content_type[:80],
            })
        elif detail.error:
            inspection.update({"status": "FETCH_ERROR", "error_type": detail.error})
        elif detail.status_code in {301, 302, 303, 307, 308}:
            inspection.update({"status": "REDIRECT_NOT_FOLLOWED", "http_status": detail.status_code})
            if detail.redirect_location:
                # Keep query data transiently for a same-host request only after a
                # robots check. Never include query/fragment values in the report.
                redirect_url = urljoin(service_url, detail.redirect_location)
                redirect = urlsplit(redirect_url)
                inspection.update({
                    "redirect_target_scheme": redirect.scheme.lower(),
                    "redirect_target_host": (redirect.hostname or "").lower(),
                    "redirect_target_path": redirect.path or "/",
                })
                same_host_https = (
                    redirect.scheme == "https"
                    and redirect.hostname == HOST
                    and redirect.port in (None, 443)
                    and redirect.username is None
                    and redirect.password is None
                )
                if not same_host_https:
                    inspection["redirect_target_status"] = "NOT_SAME_HOST_HTTPS"
                elif not _robots_allows_url(parser, USER_AGENT, redirect_url):
                    inspection["redirect_target_robots_allowed"] = False
                    inspection["redirect_target_status"] = "BLOCKED_BY_ROBOTS"
                else:
                    inspection["redirect_target_robots_allowed"] = True
                    # Inspect at most this one robots-approved redirect target.
                    # Redirects from the target are still never followed, and
                    # binary MIME types are rejected before reading body bytes.
                    redirected = get_text(
                        redirect_url,
                        max_bytes=MAX_DETAIL_BYTES,
                        timeout_seconds=timeout_seconds,
                        allowed_content_types=(
                            "text/html",
                            "application/xhtml+xml",
                            "application/json",
                            "text/plain",
                        ),
                    )
                    if redirected.error == "content_type_not_allowed":
                        inspection.update({
                            "redirect_target_status": "CONTENT_TYPE_NOT_READ",
                            "redirect_target_http_status": redirected.status_code,
                            "redirect_target_content_type": redirected.content_type[:80],
                        })
                    elif redirected.error:
                        inspection.update({
                            "redirect_target_status": "FETCH_ERROR",
                            "redirect_target_error_type": redirected.error,
                        })
                    elif redirected.status_code in {301, 302, 303, 307, 308}:
                        inspection.update({
                            "redirect_target_status": "REDIRECT_NOT_FOLLOWED",
                            "redirect_target_http_status": redirected.status_code,
                        })
                        if redirected.redirect_location:
                            # Report the second Location header only. The chain is
                            # intentionally capped here; never issue a third request.
                            next_target = urlsplit(urljoin(redirect_url, redirected.redirect_location))
                            inspection.update({
                                "redirect_chain_target_scheme": next_target.scheme.lower(),
                                "redirect_chain_target_host": (next_target.hostname or "").lower(),
                                "redirect_chain_target_path": next_target.path or "/",
                            })
                    elif redirected.status_code != 200:
                        inspection.update({
                            "redirect_target_status": "HTTP_ERROR",
                            "redirect_target_http_status": redirected.status_code,
                        })
                    elif redirected.content_type not in {
                        "text/html", "application/xhtml+xml", "application/json", "text/plain"
                    }:
                        inspection.update({
                            "redirect_target_status": "CONTENT_TYPE_NOT_READ",
                            "redirect_target_http_status": redirected.status_code,
                            "redirect_target_content_type": redirected.content_type[:80],
                        })
                    else:
                        final_target = urlsplit(redirected.url)
                        if (
                            final_target.scheme != "https"
                            or final_target.hostname != HOST
                            or final_target.port not in (None, 443)
                            or final_target.username is not None
                            or final_target.password is not None
                        ):
                            inspection["redirect_target_status"] = "FIXED_HOST_CHECK_FAILED"
                        else:
                            target_status = (
                                "READ_ONLY_PUBLIC_JSON"
                                if redirected.content_type == "application/json"
                                else "READ_ONLY_PUBLIC_DETAIL_PAGE"
                            )
                            inspection.update({
                                "redirect_target_status": target_status,
                                "redirect_target_http_status": 200,
                                "redirect_target_document_links": _extract_document_links(
                                    redirected.url,
                                    redirected.body,
                                    redirected.content_type,
                                ),
                            })
        elif detail.status_code != 200:
            inspection.update({"status": "HTTP_ERROR", "http_status": detail.status_code})
        elif detail.content_type not in {"text/html", "application/xhtml+xml", "application/json", "text/plain"}:
            # The live fetcher refuses to read a body whose type is not approved.
            inspection.update({
                "status": "CONTENT_TYPE_NOT_READ",
                "http_status": detail.status_code,
                "content_type": detail.content_type[:80],
            })
        else:
            final = urlsplit(detail.url)
            if (
                final.scheme != "https"
                or final.hostname != HOST
                or final.port not in (None, 443)
                or final.username is not None
                or final.password is not None
            ):
                inspection["status"] = "FIXED_HOST_CHECK_FAILED"
            else:
                inspection.update({
                    "status": (
                        "READ_ONLY_PUBLIC_JSON"
                        if detail.content_type == "application/json"
                        else "READ_ONLY_PUBLIC_DETAIL_PAGE"
                    ),
                    "http_status": 200,
                    "final_path": final.path,
                    "document_links": _extract_document_links(
                        detail.url,
                        detail.body,
                        detail.content_type,
                    ),
                })
        service_link_inspections.append(inspection)

    return {
        **base,
        "status": status,
        "robots": robots_summary,
        "pages_fetched": pages,
        "service_link_inspections": service_link_inspections,
        "service_page_bytes_fetched": any(
            item.get("status") in {"READ_ONLY_PUBLIC_DETAIL_PAGE", "READ_ONLY_PUBLIC_JSON"}
        or item.get("redirect_target_status") in {"READ_ONLY_PUBLIC_DETAIL_PAGE", "READ_ONLY_PUBLIC_JSON"}
            for item in service_link_inspections
        ),
        "paper_bytes_fetched": False,
    }
