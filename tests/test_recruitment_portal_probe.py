from ai_comp.research.recruitment_portal_probe import (
    FetchResult,
    probe_recruitment_portal_route,
)


ORIGIN = "https://recruitment.rajasthan.gov.in"


def _fake_fetcher(pages):
    requested = []

    def fetcher(url, *, max_bytes, timeout_seconds, allowed_content_types):
        requested.append(url)
        assert max_bytes > 0
        assert allowed_content_types
        assert 0.5 <= timeout_seconds <= 3.0
        return pages.get(url, FetchResult(404, url, "text/html"))

    return fetcher, requested


def test_probe_fails_closed_when_robots_is_unavailable():
    fetcher, requested = _fake_fetcher({})
    report = probe_recruitment_portal_route(fetcher=fetcher)

    assert report["status"] == "ROBOTS_UNAVAILABLE"
    assert requested == [f"{ORIGIN}/robots.txt"]
    assert report["pages_inspected"] == []
    assert report["source_registry_modified"] is False
    assert report["paper_bytes_fetched"] is False
    assert report["database_written"] is False
    assert report["candidate_promotions"] == 0


def test_probe_inspects_only_robots_allowed_indexes_and_never_follows_document_links():
    robots = FetchResult(
        200, f"{ORIGIN}/robots.txt", "text/plain",
        "User-agent: *\nAllow: /\nDisallow: /departmentrecservlet\n",
    )
    home = FetchResult(
        200, f"{ORIGIN}/", "text/html",
        '<a href="/downloadservlet?docId=123">RSSB Question Paper PDF</a>'
        '<a href="https://rssb.rajasthan.gov.in/storage/questionpaper_item/1.pdf">Answer Key</a>',
    )
    fetcher, requested = _fake_fetcher({
        f"{ORIGIN}/robots.txt": robots,
        f"{ORIGIN}/": home,
        f"{ORIGIN}/recruitmentservlet": FetchResult(
            200, f"{ORIGIN}/recruitmentservlet", "text/html", "<html></html>"
        ),
    })

    report = probe_recruitment_portal_route(fetcher=fetcher)

    assert report["status"] == "SAME_HOST_PAPER_OR_KEY_LINK_FOUND_NOT_FETCHED"
    assert report["robots"]["status"] == "READ"
    assert report["pages_inspected"][0]["paper_links"][0]["path"] == "/downloadservlet"
    assert report["pages_inspected"][0]["paper_links"][0]["query_present"] is True
    assert report["pages_inspected"][0]["paper_links"][0]["same_host"] is True
    assert report["pages_inspected"][1]["status"] == "BLOCKED_BY_ROBOTS"
    assert requested == [
        f"{ORIGIN}/robots.txt",
        f"{ORIGIN}/",
        f"{ORIGIN}/recruitmentservlet",
    ]
    assert not any("downloadservlet" in url or "questionpaper_item" in url for url in requested)
    assert report["paper_bytes_fetched"] is False
    assert report["database_written"] is False
    assert report["source_registry_modified"] is False
    assert report["candidate_promotions"] == 0


def test_probe_records_external_paper_links_without_exposing_url_queries_or_following_them():
    robots = FetchResult(200, f"{ORIGIN}/robots.txt", "text/plain", "User-agent: *\nAllow: /\n")
    home = FetchResult(
        200, f"{ORIGIN}/", "text/html",
        '<a href="https://rssb.rajasthan.gov.in/storage/questionpaper_item/1.pdf?token=secret">'
        'RSSB Question Paper</a>',
    )
    fetcher, requested = _fake_fetcher({f"{ORIGIN}/robots.txt": robots, f"{ORIGIN}/": home})
    report = probe_recruitment_portal_route(fetcher=fetcher)

    link = report["pages_inspected"][0]["paper_links"][0]
    assert report["status"] == "PAPER_OR_KEY_LINK_POINTS_TO_OTHER_HOST"
    assert link["target_host"] == "rssb.rajasthan.gov.in"
    assert link["same_host"] is False
    assert link["query_present"] is True
    assert "secret" not in str(report)
    assert "url" not in link
    assert requested == [
        f"{ORIGIN}/robots.txt",
        f"{ORIGIN}/",
        f"{ORIGIN}/recruitmentservlet",
        f"{ORIGIN}/departmentrecservlet",
    ]
    assert report["paper_bytes_fetched"] is False


def test_probe_rejects_out_of_range_timeout():
    import pytest

    with pytest.raises(ValueError, match="between 0.5 and 3.0"):
        probe_recruitment_portal_route(timeout_seconds=10)
