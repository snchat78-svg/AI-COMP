from ai_comp.research.jansoochna_service_probe import (
    FetchResult,
    probe_jansoochna_rssb_service,
)


ORIGIN = "https://jansoochna.rajasthan.gov.in"


def _fetcher_with_pages(pages):
    requested = []

    def fetcher(url, *, max_bytes, timeout_seconds):
        requested.append(url)
        assert max_bytes > 0
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
    fetcher, requested = _fetcher_with_pages({
        f"{ORIGIN}/robots.txt": robots,
        f"{ORIGIN}/Services": services,
        f"{ORIGIN}/Scheme": scheme,
    })

    report = probe_jansoochna_rssb_service(fetcher=fetcher)

    assert report["status"] == "SAME_HOST_RSSB_PAPER_SERVICE_LINK_FOUND"
    assert report["robots"]["status"] == "READ"
    service_page = report["pages_fetched"][0]
    assert service_page["question_papers"][0]["url"] == f"{ORIGIN}/Services/RSSB?serviceId=123"
    assert service_page["answer_keys"][0]["url"] == f"{ORIGIN}/Services/RSSB?serviceId=124"
    assert requested == [f"{ORIGIN}/robots.txt", f"{ORIGIN}/Services", f"{ORIGIN}/Scheme"]
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
