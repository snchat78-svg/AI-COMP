from ai_comp.research.jansoochna_service_probe import (
    FetchResult,
    probe_jansoochna_rssb_service,
)


ORIGIN = "https://jansoochna.rajasthan.gov.in"


def _fetcher_with_pages(pages):
    requested = []

    def fetcher(url, *, max_bytes, timeout_seconds, allowed_content_types):
        requested.append(url)
        assert max_bytes > 0
        assert allowed_content_types
        assert 0.5 <= timeout_seconds <= 3.0
        return pages.get(url, FetchResult(404, url, "text/html"))

    return fetcher, requested


def test_probe_reads_services_only_when_robots_permits_and_keeps_same_host_links():
    robots = FetchResult(
        200, f"{ORIGIN}/robots.txt", "text/plain",
        "User-agent: *\nAllow: /Services\nAllow: /Scheme\n",
    )
    services = FetchResult(
        200, f"{ORIGIN}/Services", "text/html",
        '<a href="/Services/RSSB?serviceId=123">Question Papers of RSSB</a>'
        '<a href="/Services/RSSB?serviceId=124">Answer Key of RSSB</a>',
    )
    scheme = FetchResult(200, f"{ORIGIN}/Scheme", "text/html", "<html></html>")
    paper_detail_url = f"{ORIGIN}/Services/RSSB?serviceId=123"
    answer_detail_url = f"{ORIGIN}/Services/RSSB?serviceId=124"
    fetcher, requested = _fetcher_with_pages({
        f"{ORIGIN}/robots.txt": robots,
        f"{ORIGIN}/Services": services,
        f"{ORIGIN}/Scheme": scheme,
        paper_detail_url: FetchResult(
            200, paper_detail_url, "text/html",
            '<a href="/Storage/RSSB-CET-2025.pdf">CET Graduation 2025 Question Paper</a>',
        ),
        answer_detail_url: FetchResult(
            200, answer_detail_url, "text/html",
            '<a href="https://rssb.rajasthan.gov.in/storage/key.pdf">RSSB Answer Key</a>',
        ),
    })

    report = probe_jansoochna_rssb_service(fetcher=fetcher)

    assert report["status"] == "SAME_HOST_RSSB_PAPER_SERVICE_LINK_FOUND"
    assert report["robots"]["status"] == "READ"
    service_page = report["pages_fetched"][0]
    assert service_page["question_papers"][0]["url"] == f"{ORIGIN}/Services/RSSB?serviceId=123"
    assert service_page["answer_keys"][0]["url"] == f"{ORIGIN}/Services/RSSB?serviceId=124"
    assert requested == [
        f"{ORIGIN}/robots.txt",
        f"{ORIGIN}/Services",
        f"{ORIGIN}/Scheme",
        paper_detail_url,
        answer_detail_url,
    ]
    assert report["service_link_inspections"][0]["status"] == "READ_ONLY_PUBLIC_DETAIL_PAGE"
    paper_links = report["service_link_inspections"][0]["document_links"]
    assert paper_links[0]["kind"] == "PDF_CANDIDATE_LINK_NOT_FETCHED"
    assert paper_links[0]["url"] == f"{ORIGIN}/Storage/RSSB-CET-2025.pdf"
    assert paper_links[0]["same_host"] is True
    assert report["service_link_inspections"][1]["document_links"][0]["target_host"] == "rssb.rajasthan.gov.in"
    assert not any("RSSB-CET-2025.pdf" in url or "/storage/key.pdf" in url for url in requested)
    assert report["service_page_bytes_fetched"] is True
    assert report["paper_bytes_fetched"] is False
    assert report["source_registry_modified"] is False


def test_probe_fails_closed_when_robots_disallows_both_service_pages():
    robots = FetchResult(
        200, f"{ORIGIN}/robots.txt", "text/plain",
        "User-agent: *\nDisallow: /Services\nDisallow: /Scheme\n",
    )
    fetcher, requested = _fetcher_with_pages({f"{ORIGIN}/robots.txt": robots})

    report = probe_jansoochna_rssb_service(fetcher=fetcher)

    assert report["status"] == "PUBLIC_PAGES_BLOCKED_BY_ROBOTS"
    assert requested == [f"{ORIGIN}/robots.txt"]
    assert all(page["status"] == "BLOCKED_BY_ROBOTS" for page in report["pages_fetched"])


def test_probe_fails_closed_when_robots_is_unavailable():
    fetcher, requested = _fetcher_with_pages({})
    report = probe_jansoochna_rssb_service(fetcher=fetcher)
    assert report["status"] == "ROBOTS_UNAVAILABLE"
    assert requested == [f"{ORIGIN}/robots.txt"]
    # Keep the response schema stable even when the robots gate stops discovery.
    assert report["service_link_inspections"] == []
    assert report["service_page_bytes_fetched"] is False
    assert report["paper_bytes_fetched"] is False


def test_probe_does_not_follow_or_expose_external_rssb_service_links():
    robots = FetchResult(
        200, f"{ORIGIN}/robots.txt", "text/plain",
        "User-agent: *\nAllow: /Services\nAllow: /Scheme\n",
    )
    services = FetchResult(
        200, f"{ORIGIN}/Services", "text/html",
        '<a href="https://rssb.rajasthan.gov.in/papers/a.pdf">Question Papers of RSSB</a>',
    )
    fetcher, requested = _fetcher_with_pages({
        f"{ORIGIN}/robots.txt": robots,
        f"{ORIGIN}/Services": services,
        f"{ORIGIN}/Scheme": FetchResult(200, f"{ORIGIN}/Scheme", "text/html", ""),
    })

    report = probe_jansoochna_rssb_service(fetcher=fetcher)

    link = report["pages_fetched"][0]["question_papers"][0]
    assert report["status"] == "RSSB_PAPER_LINK_POINTS_TO_OTHER_HOST"
    assert link["same_host"] is False
    assert link["target_host"] == "rssb.rajasthan.gov.in"
    assert "url" not in link
    assert requested == [f"{ORIGIN}/robots.txt", f"{ORIGIN}/Services", f"{ORIGIN}/Scheme"]


def test_probe_rejects_unbounded_timeouts():
    import pytest
    with pytest.raises(ValueError, match="between 0.5 and 3.0"):
        probe_jansoochna_rssb_service(timeout_seconds=10)



def test_probe_checks_exact_service_link_against_robots_before_fetch():
    service_url = f"{ORIGIN}/Services/GetMoreData?q=public-token"
    robots = FetchResult(
        200, f"{ORIGIN}/robots.txt", "text/plain",
        "User-agent: *\nAllow: /Services\nAllow: /Scheme\nDisallow: /Services/GetMoreData\n",
    )
    fetcher, requested = _fetcher_with_pages({
        f"{ORIGIN}/robots.txt": robots,
        f"{ORIGIN}/Services": FetchResult(
            200, f"{ORIGIN}/Services", "text/html",
            '<a href="/Services/GetMoreData?q=public-token">Question Papers of RSSB</a>',
        ),
        f"{ORIGIN}/Scheme": FetchResult(200, f"{ORIGIN}/Scheme", "text/html", ""),
    })

    report = probe_jansoochna_rssb_service(fetcher=fetcher)

    assert report["service_link_inspections"][0]["status"] == "BLOCKED_BY_ROBOTS"
    assert report["service_link_inspections"][0]["robots_allowed"] is False
    assert service_url not in requested
    assert requested == [f"{ORIGIN}/robots.txt", f"{ORIGIN}/Services", f"{ORIGIN}/Scheme"]
    assert report["service_page_bytes_fetched"] is False
    assert report["paper_bytes_fetched"] is False


def test_safe_fetch_refuses_pdf_content_before_reading_body(monkeypatch):
    import pytest
    from ai_comp.research import jansoochna_service_probe as probe_module

    service_url = f"{ORIGIN}/Services/GetMoreData?q=public-token"

    class Headers:
        def get_content_type(self):
            return "application/pdf"

    class Response:
        status = 200
        headers = Headers()

        def geturl(self):
            return service_url

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, *_args, **_kwargs):
            pytest.fail("binary PDF body must never be read by the service-index probe")

    class Opener:
        def open(self, request, *, timeout):
            assert request.full_url == service_url
            assert timeout == 1.0
            return Response()

    monkeypatch.setattr(probe_module, "build_opener", lambda *_args: Opener())

    result = probe_module._safe_fetch_text(
        service_url,
        max_bytes=1024,
        timeout_seconds=1.0,
        allowed_content_types=("text/html", "application/json"),
    )

    assert result.status_code == 200
    assert result.content_type == "application/pdf"
    assert result.error == "content_type_not_allowed"
    assert result.body == ""

def test_probe_records_redirect_host_and_path_without_following():
    detail_url = f"{ORIGIN}/Services/GetMoreData?q=opaque-public-token"
    robots = FetchResult(
        200, f"{ORIGIN}/robots.txt", "text/plain",
        "User-agent: *\nAllow: /Services\nAllow: /Scheme\n",
    )
    services = FetchResult(
        200, f"{ORIGIN}/Services", "text/html",
        '<a href="/Services/GetMoreData?q=opaque-public-token">Question Papers of RSSB</a>',
    )
    fetcher, requested = _fetcher_with_pages({
        f"{ORIGIN}/robots.txt": robots,
        f"{ORIGIN}/Services": services,
        f"{ORIGIN}/Scheme": FetchResult(200, f"{ORIGIN}/Scheme", "text/html", ""),
        detail_url: FetchResult(
            302, detail_url, "text/html",
            redirect_location="https://rssb.rajasthan.gov.in/papers/2025.pdf?token=secret-value#fragment",
        ),
    })

    report = probe_jansoochna_rssb_service(fetcher=fetcher)

    inspection = report["service_link_inspections"][0]
    assert inspection["status"] == "REDIRECT_NOT_FOLLOWED"
    assert inspection["redirect_target_scheme"] == "https"
    assert inspection["redirect_target_host"] == "rssb.rajasthan.gov.in"
    assert inspection["redirect_target_path"] == "/papers/2025.pdf"
    assert "secret-value" not in str(inspection)
    assert "fragment" not in str(inspection)
    assert requested == [
        f"{ORIGIN}/robots.txt",
        f"{ORIGIN}/Services",
        f"{ORIGIN}/Scheme",
        detail_url,
    ]
    assert not any("rssb.rajasthan.gov.in" in url for url in requested)
    assert report["paper_bytes_fetched"] is False
    assert report["source_registry_modified"] is False


def test_safe_fetch_preserves_only_redirect_location_metadata(monkeypatch):
    from email.message import Message
    from urllib.error import HTTPError
    from ai_comp.research import jansoochna_service_probe as probe_module

    service_url = f"{ORIGIN}/Services/GetMoreData?q=opaque-public-token"
    headers = Message()
    headers["Content-Type"] = "text/html"
    headers["Location"] = "https://rssb.rajasthan.gov.in/papers/2025.pdf?token=secret-value"

    class Opener:
        def open(self, request, *, timeout):
            assert request.full_url == service_url
            raise HTTPError(service_url, 302, "Found", headers, None)

    monkeypatch.setattr(probe_module, "build_opener", lambda *_args: Opener())
    result = probe_module._safe_fetch_text(
        service_url,
        max_bytes=1024,
        timeout_seconds=1.0,
        allowed_content_types=("text/html",),
    )

    assert result.status_code == 302
    assert result.redirect_location == "https://rssb.rajasthan.gov.in/papers/2025.pdf?token=secret-value"
    assert result.body == ""

def test_probe_blocks_redirect_target_when_exact_path_is_robots_disallowed():
    service_url = f"{ORIGIN}/Services/GetMoreData?q=opaque-public-token"
    redirect_url = f"{ORIGIN}/Services/ClickablePDF?token=private-value"
    robots = FetchResult(
        200, f"{ORIGIN}/robots.txt", "text/plain",
        "User-agent: *\nAllow: /Services\nAllow: /Scheme\nDisallow: /Services/ClickablePDF\n",
    )
    fetcher, requested = _fetcher_with_pages({
        f"{ORIGIN}/robots.txt": robots,
        f"{ORIGIN}/Services": FetchResult(
            200, f"{ORIGIN}/Services", "text/html",
            '<a href="/Services/GetMoreData?q=opaque-public-token">Question Papers of RSSB</a>',
        ),
        f"{ORIGIN}/Scheme": FetchResult(200, f"{ORIGIN}/Scheme", "text/html", ""),
        service_url: FetchResult(
            302, service_url, "text/html", redirect_location=redirect_url,
        ),
    })

    report = probe_jansoochna_rssb_service(fetcher=fetcher)

    inspection = report["service_link_inspections"][0]
    assert inspection["status"] == "REDIRECT_NOT_FOLLOWED"
    assert inspection["redirect_target_status"] == "BLOCKED_BY_ROBOTS"
    assert inspection["redirect_target_robots_allowed"] is False
    assert inspection["redirect_target_path"] == "/Services/ClickablePDF"
    assert redirect_url not in requested
    assert "private-value" not in str(inspection)
    assert report["paper_bytes_fetched"] is False


def test_probe_inspects_robots_permitted_redirect_target_without_fetching_documents():
    service_url = f"{ORIGIN}/Services/GetMoreData?q=opaque-public-token"
    redirect_url = f"{ORIGIN}/Services/ClickablePDF?token=private-value"
    robots = FetchResult(
        200, f"{ORIGIN}/robots.txt", "text/plain",
        "User-agent: *\nAllow: /Services\nAllow: /Scheme\n",
    )
    fetcher, requested = _fetcher_with_pages({
        f"{ORIGIN}/robots.txt": robots,
        f"{ORIGIN}/Services": FetchResult(
            200, f"{ORIGIN}/Services", "text/html",
            '<a href="/Services/GetMoreData?q=opaque-public-token">Question Papers of RSSB</a>',
        ),
        f"{ORIGIN}/Scheme": FetchResult(200, f"{ORIGIN}/Scheme", "text/html", ""),
        service_url: FetchResult(
            302, service_url, "text/html", redirect_location=redirect_url,
        ),
        redirect_url: FetchResult(
            200, redirect_url, "text/html",
            '<a href="/Files/RSSB-CET-2025.pdf">RSSB CET Graduation Question Paper</a>',
        ),
    })

    report = probe_jansoochna_rssb_service(fetcher=fetcher)

    inspection = report["service_link_inspections"][0]
    assert inspection["status"] == "REDIRECT_NOT_FOLLOWED"
    assert inspection["redirect_target_robots_allowed"] is True
    assert inspection["redirect_target_status"] == "READ_ONLY_PUBLIC_DETAIL_PAGE"
    document_link = inspection["redirect_target_document_links"][0]
    assert document_link["kind"] == "PDF_CANDIDATE_LINK_NOT_FETCHED"
    assert document_link["url"] == f"{ORIGIN}/Files/RSSB-CET-2025.pdf"
    assert redirect_url in requested
    assert not any(url.endswith("/Files/RSSB-CET-2025.pdf") for url in requested)
    assert "private-value" not in str(inspection)
    assert report["service_page_bytes_fetched"] is True
    assert report["paper_bytes_fetched"] is False

def test_probe_reports_second_redirect_location_without_following():
    service_url = f"{ORIGIN}/Services/GetMoreData?q=opaque-public-token"
    redirect_url = f"{ORIGIN}/Services/ClickablePDF?token=first-secret"
    second_location = f"{ORIGIN}/Storage/RSSB-CET-2025.pdf?download=second-secret#hidden"
    robots = FetchResult(
        200, f"{ORIGIN}/robots.txt", "text/plain",
        "User-agent: *\nAllow: /Services\nAllow: /Scheme\nAllow: /Storage\n",
    )
    fetcher, requested = _fetcher_with_pages({
        f"{ORIGIN}/robots.txt": robots,
        f"{ORIGIN}/Services": FetchResult(
            200, f"{ORIGIN}/Services", "text/html",
            '<a href="/Services/GetMoreData?q=opaque-public-token">Question Papers of RSSB</a>',
        ),
        f"{ORIGIN}/Scheme": FetchResult(200, f"{ORIGIN}/Scheme", "text/html", ""),
        service_url: FetchResult(302, service_url, "text/html", redirect_location=redirect_url),
        redirect_url: FetchResult(
            302, redirect_url, "text/html", redirect_location=second_location,
        ),
    })

    report = probe_jansoochna_rssb_service(fetcher=fetcher)

    inspection = report["service_link_inspections"][0]
    assert inspection["redirect_target_status"] == "REDIRECT_NOT_FOLLOWED"
    assert inspection["redirect_chain_target_scheme"] == "https"
    assert inspection["redirect_chain_target_host"] == "jansoochna.rajasthan.gov.in"
    assert inspection["redirect_chain_target_path"] == "/Storage/RSSB-CET-2025.pdf"
    assert "first-secret" not in str(inspection)
    assert "second-secret" not in str(inspection)
    assert "hidden" not in str(inspection)
    assert second_location not in requested
    assert requested == [
        f"{ORIGIN}/robots.txt",
        f"{ORIGIN}/Services",
        f"{ORIGIN}/Scheme",
        service_url,
        redirect_url,
    ]
    assert report["paper_bytes_fetched"] is False

def test_probe_session_fetcher_reuses_cookie_jar_without_redirect_handler(monkeypatch):
    from http.cookiejar import CookieJar
    from urllib.request import HTTPCookieProcessor
    from ai_comp.research import jansoochna_service_probe as probe_module

    created_handlers = []
    observed_openers = []

    class StubOpener:
        pass

    def fake_build_opener(*handlers):
        created_handlers.append(handlers)
        return StubOpener()

    def fake_safe_fetch_text(url, **kwargs):
        observed_openers.append(kwargs["opener"])
        return FetchResult(200, url, "text/plain", "ok")

    monkeypatch.setattr(probe_module, "build_opener", fake_build_opener)
    monkeypatch.setattr(probe_module, "_safe_fetch_text", fake_safe_fetch_text)

    session_fetcher = probe_module._build_session_fetcher()
    first = session_fetcher(
        f"{ORIGIN}/robots.txt",
        max_bytes=100,
        timeout_seconds=1.0,
        allowed_content_types=("text/plain",),
    )
    second = session_fetcher(
        f"{ORIGIN}/Services",
        max_bytes=100,
        timeout_seconds=1.0,
        allowed_content_types=("text/html",),
    )

    assert first.status_code == second.status_code == 200
    assert len(created_handlers) == 1
    assert observed_openers[0] is observed_openers[1]
    assert isinstance(created_handlers[0][0], HTTPCookieProcessor)
    assert isinstance(created_handlers[0][0].cookiejar, CookieJar)
    assert type(created_handlers[0][1]).__name__ == "_NoRedirectHandler"


def test_robots_request_allows_normal_accept_negotiation_and_requires_plain_text(monkeypatch):
    from email.message import Message
    from ai_comp.research import jansoochna_service_probe as probe_module

    url = f"{ORIGIN}/robots.txt"
    headers = Message()
    headers["Content-Type"] = "text/plain"

    class Response:
        status = 200

        def __init__(self):
            self.headers = headers

        def geturl(self):
            return url

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, limit):
            assert limit > 0
            return b"User-agent: *\\nDisallow: /private\\n"

    class Opener:
        def open(self, request, *, timeout):
            assert request.full_url == url
            assert request.get_header("Accept") == "text/plain, */*;q=0.8"
            assert request.get_header("User-agent") == probe_module.USER_AGENT
            assert timeout == 1.0
            return Response()

    monkeypatch.setattr(probe_module, "build_opener", lambda *_args: Opener())

    result = probe_module._safe_fetch_text(
        url,
        max_bytes=1024,
        timeout_seconds=1.0,
        allowed_content_types=("text/plain",),
    )

    assert result.status_code == 200
    assert result.content_type == "text/plain"
    assert result.error is None
    assert "Disallow: /private" in result.body
