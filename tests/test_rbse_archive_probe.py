from ai_comp.research.rbse_archive_probe import FetchResult, probe_rbse_archive_route


ORIGIN = "https://rajeduboard.rajasthan.gov.in"
INDEX = f"{ORIGIN}/books/PAPERS-2025/index.htm"


def _fake_fetcher(pages):
    requested = []

    def fetcher(url, *, max_bytes, timeout_seconds, allowed_content_types):
        requested.append(url)
        assert max_bytes > 0
        assert allowed_content_types
        assert 0.5 <= timeout_seconds <= 3.0
        return pages.get(url, FetchResult(404, url, "text/html"))

    return fetcher, requested


def test_probe_fails_closed_when_robots_has_network_error():
    fetcher, requested = _fake_fetcher({
        f"{ORIGIN}/robots.txt": FetchResult(
            None, f"{ORIGIN}/robots.txt", "", error="TimeoutError"
        ),
    })

    report = probe_rbse_archive_route(fetcher=fetcher)

    assert report["status"] == "ROBOTS_UNAVAILABLE"
    assert report["robots"] == {"status": "FETCH_ERROR", "error_type": "TimeoutError"}
    assert requested == [f"{ORIGIN}/robots.txt"]
    assert report["pages_inspected"] == []
    assert report["source_registry_modified"] is False
    assert report["paper_bytes_fetched"] is False
    assert report["database_written"] is False
    assert report["candidate_promotions"] == 0


def test_probe_rejects_html_robots_response_without_reading_archive_index():
    fetcher, requested = _fake_fetcher({
        f"{ORIGIN}/robots.txt": FetchResult(
            200, f"{ORIGIN}/robots.txt", "text/html", "<html>not robots</html>"
        ),
    })

    report = probe_rbse_archive_route(fetcher=fetcher)

    assert report["status"] == "ROBOTS_CONTENT_TYPE_INVALID"
    assert report["robots"]["content_type"] == "text/html"
    assert requested == [f"{ORIGIN}/robots.txt"]
    assert report["pages_inspected"] == []


def test_probe_fails_closed_for_robots_access_denial_and_server_error():
    for status_code in (403, 429, 500, 503):
        fetcher, requested = _fake_fetcher({
            f"{ORIGIN}/robots.txt": FetchResult(
                status_code, f"{ORIGIN}/robots.txt", "text/plain"
            ),
        })

        report = probe_rbse_archive_route(fetcher=fetcher)

        assert report["status"] == "ROBOTS_UNAVAILABLE"
        assert report["robots"]["http_status"] == status_code
        assert requested == [f"{ORIGIN}/robots.txt"]
        assert report["pages_inspected"] == []


def test_probe_inspects_only_fixed_index_when_robots_explicitly_returns_404():
    page = FetchResult(
        200,
        INDEX,
        "text/html",
        '<a href="/books/PAPERS-2025/SRS/SS-14.pdf">19. SR SECONDARY - GEOGRAPHY</a>'
        '<a href="https://external.example/paper.pdf">External paper</a>',
    )
    fetcher, requested = _fake_fetcher({
        f"{ORIGIN}/robots.txt": FetchResult(
            404, f"{ORIGIN}/robots.txt", "text/html"
        ),
        INDEX: page,
    })

    report = probe_rbse_archive_route(fetcher=fetcher)

    assert report["status"] == "SAME_HOST_PAPER_LINKS_FOUND_NOT_FETCHED"
    assert report["board_id"] == "RBSE"
    assert report["robots"]["status"] == "NOT_PUBLISHED_HTTP_404"
    assert report["robots"]["allowed_index_path"] is True
    assert report["pages_inspected"][0]["status"] == "READ_ONLY_PUBLIC_HTML"
    links = report["pages_inspected"][0]["pdf_links"]
    assert links[0]["same_host"] is True
    assert links[0]["path"] == "/books/PAPERS-2025/SRS/SS-14.pdf"
    assert links[0]["status"] == "PUBLIC_PDF_LINK_FOUND_NOT_FETCHED"
    assert links[1]["same_host"] is False
    assert links[1]["status"] == "EXTERNAL_OR_OUT_OF_SCOPE_PDF_NOT_FOLLOWED"
    assert requested == [f"{ORIGIN}/robots.txt", INDEX]
    assert not any(url.lower().endswith(".pdf") for url in requested)
    assert report["paper_bytes_fetched"] is False
    assert report["database_written"] is False
    assert report["source_registry_modified"] is False
    assert report["candidate_promotions"] == 0


def test_probe_reads_index_only_when_robot_rules_allow_the_exact_path():
    robots = FetchResult(
        200,
        f"{ORIGIN}/robots.txt",
        "text/plain",
        "User-agent: *\nAllow: /books/PAPERS-2025/index.htm\nDisallow: /books/PAPERS-2025/\n",
    )
    page = FetchResult(
        200, INDEX, "text/html",
        '<a href="/books/PAPERS-2025/SRS/SS-14.pdf">Geography</a>',
    )
    fetcher, requested = _fake_fetcher({
        f"{ORIGIN}/robots.txt": robots,
        INDEX: page,
    })

    report = probe_rbse_archive_route(fetcher=fetcher)

    assert report["robots"]["status"] == "READ"
    assert report["robots"]["allowed_index_path"] is True
    assert report["status"] == "SAME_HOST_PAPER_LINKS_FOUND_NOT_FETCHED"
    assert requested == [f"{ORIGIN}/robots.txt", INDEX]


def test_probe_does_not_read_index_when_robot_rules_disallow_it():
    robots = FetchResult(
        200,
        f"{ORIGIN}/robots.txt",
        "text/plain",
        "User-agent: *\nAllow: /\nDisallow: /books/PAPERS-2025/index.htm\n",
    )
    fetcher, requested = _fake_fetcher({f"{ORIGIN}/robots.txt": robots})

    report = probe_rbse_archive_route(fetcher=fetcher)

    assert report["status"] == "PUBLIC_INDEX_BLOCKED_BY_ROBOTS"
    assert report["robots"]["allowed_index_path"] is False
    assert report["pages_inspected"] == []
    assert requested == [f"{ORIGIN}/robots.txt"]


def test_probe_does_not_follow_pdf_links_or_expose_query_values():
    page = FetchResult(
        200,
        INDEX,
        "text/html",
        '<a href="/books/PAPERS-2025/SRS/SS-14.pdf?token=do-not-print">Geography</a>',
    )
    fetcher, requested = _fake_fetcher({
        f"{ORIGIN}/robots.txt": FetchResult(404, f"{ORIGIN}/robots.txt", "text/html"),
        INDEX: page,
    })

    report = probe_rbse_archive_route(fetcher=fetcher)

    assert report["status"] == "SAME_HOST_PAPER_LINKS_FOUND_NOT_FETCHED"
    link = report["pages_inspected"][0]["pdf_links"][0]
    assert link["query_present"] is True
    assert "do-not-print" not in str(report)
    assert "url" not in link
    assert requested == [f"{ORIGIN}/robots.txt", INDEX]
    assert report["paper_bytes_fetched"] is False


def test_probe_does_not_follow_index_redirects():
    fetcher, requested = _fake_fetcher({
        f"{ORIGIN}/robots.txt": FetchResult(404, f"{ORIGIN}/robots.txt", "text/html"),
        INDEX: FetchResult(
            302, INDEX, "text/html",
            redirect_location="https://other.example/index.htm",
        ),
    })

    report = probe_rbse_archive_route(fetcher=fetcher)

    assert report["status"] == "PUBLIC_INDEX_UNAVAILABLE"
    assert report["pages_inspected"][0]["status"] == "REDIRECT_NOT_FOLLOWED"
    assert requested == [f"{ORIGIN}/robots.txt", INDEX]


def test_probe_rejects_out_of_range_timeout():
    import pytest

    with pytest.raises(ValueError, match="between 0.5 and 3.0"):
        probe_rbse_archive_route(timeout_seconds=10)
