from ai_comp.domain.sources import CrawlPolicy, SourcePriority, SourceRecord, SourceType
from ai_comp.research.live_discovery import (
    HttpResponse,
    HttpTransport,
    LiveOfficialSourceDiscovery,
    _SameHostRedirectHandler,
)
from ai_comp.research.seed_registry import build_initial_registry

class FakeTransport:
    def __init__(self, pages):
        self.pages = pages
        self.requested = []
    def get(self, url):
        self.requested.append(url)
        return self.pages.get(url, HttpResponse(url, 404, "", "text/plain"))

def source():
    return SourceRecord("RSSB", "RSSB", "https://rsmssb.rajasthan.gov.in/", SourceType.OFFICIAL_WEBSITE, SourcePriority.OFFICIAL, allowed_paths=("/papers/", "/archive/"))

def test_live_discovery_uses_robots_sitemap_and_creates_candidates():
    base = "https://rsmssb.rajasthan.gov.in/"
    transport = FakeTransport({
        base + "robots.txt": HttpResponse(base + "robots.txt", 200, "User-agent: AI-COMP/phase2\nSitemap: https://rsmssb.rajasthan.gov.in/sitemap.xml\n", "text/plain"),
        base + "sitemap.xml": HttpResponse(base + "sitemap.xml", 200, '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://rsmssb.rajasthan.gov.in/papers/a.pdf</loc></url><url><loc>https://evil.example/x.pdf</loc></url></urlset>', "application/xml"),
    })
    result = LiveOfficialSourceDiscovery(transport).run(source(), CrawlPolicy(True, rate_limit_seconds=0))
    assert [c.url for c in result.candidates] == [base + "papers/a.pdf"]
    assert base + "robots.txt" in transport.requested
    assert base + "sitemap.xml" in transport.requested

def test_live_discovery_handles_sitemap_index_with_bound():
    base = "https://rsmssb.rajasthan.gov.in/"
    transport = FakeTransport({
        base + "robots.txt": HttpResponse(base + "robots.txt", 200, "User-agent: AI-COMP/phase2\nSitemap: https://rsmssb.rajasthan.gov.in/sitemap_index.xml\n", "text/plain"),
        base + "sitemap_index.xml": HttpResponse(base + "sitemap_index.xml", 200, '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://rsmssb.rajasthan.gov.in/sitemap-1.xml</loc></sitemap></sitemapindex>', "application/xml"),
        base + "sitemap-1.xml": HttpResponse(base + "sitemap-1.xml", 200, '<urlset><url><loc>https://rsmssb.rajasthan.gov.in/papers/b.pdf</loc></url></urlset>', "application/xml"),
    })
    result = LiveOfficialSourceDiscovery(transport).run(source(), CrawlPolicy(True, max_depth=2, rate_limit_seconds=0))
    assert [c.url for c in result.candidates] == [base + "papers/b.pdf"]
    assert base + "sitemap-1.xml" in transport.requested

def test_live_discovery_fails_closed_when_robots_missing():
    base = "https://rsmssb.rajasthan.gov.in/"
    transport = FakeTransport({base + "robots.txt": HttpResponse(base + "robots.txt", 404, "", "text/plain")})
    try:
        LiveOfficialSourceDiscovery(transport).run(source(), CrawlPolicy(True, rate_limit_seconds=0))
    except ValueError as exc:
        assert str(exc) == "robots_unavailable"
    else:
        raise AssertionError("expected robots_unavailable")

def test_live_candidate_ids_are_stable_when_sitemap_order_changes():
    base = "https://rsmssb.rajasthan.gov.in/"
    robots = HttpResponse(
        base + "robots.txt",
        200,
        "User-agent: AI-COMP/phase2\nSitemap: " + base + "sitemap.xml\n",
        "text/plain",
    )
    first_map = (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base}papers/a.pdf</loc></url>"
        f"<url><loc>{base}papers/b.pdf</loc></url>"
        "</urlset>"
    )
    second_map = (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base}papers/b.pdf</loc></url>"
        f"<url><loc>{base}papers/a.pdf</loc></url>"
        "</urlset>"
    )
    discovery = LiveOfficialSourceDiscovery
    policy = CrawlPolicy(True, rate_limit_seconds=0)
    first = discovery(FakeTransport({
        base + "robots.txt": robots,
        base + "sitemap.xml": HttpResponse(base + "sitemap.xml", 200, first_map, "application/xml"),
    })).run(source(), policy)
    second = discovery(FakeTransport({
        base + "robots.txt": robots,
        base + "sitemap.xml": HttpResponse(base + "sitemap.xml", 200, second_map, "application/xml"),
    })).run(source(), policy)

    first_ids = {candidate.url: candidate.candidate_id for candidate in first.candidates}
    second_ids = {candidate.url: candidate.candidate_id for candidate in second.candidates}
    assert first_ids == second_ids
    assert all(candidate.discovered_at for candidate in first.candidates)



def test_rpsc_discovery_includes_registered_question_and_answer_key_archives():
    base = "https://rpsc.rajasthan.gov.in/"
    rpsc_source = SourceRecord(
        "RPSC_OFFICIAL",
        "RPSC Official",
        base,
        SourceType.OFFICIAL_WEBSITE,
        SourcePriority.OFFICIAL,
    )
    question_archive = base + "viewcommon?Slice=QP"
    answer_archive = base + "viewcommon?Slice=AK"
    transport = FakeTransport({
        base + "robots.txt": HttpResponse(
            base + "robots.txt",
            200,
            "User-agent: AI-COMP/phase2\nSitemap: " + base + "sitemap.xml\n",
            "text/plain",
        ),
        base + "sitemap.xml": HttpResponse(
            base + "sitemap.xml",
            200,
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>',
            "application/xml",
        ),
        question_archive: HttpResponse(
            question_archive,
            200,
            '<a href="/Static/PreviousQuestionPaper/old-paper.pdf">RAS old question paper</a>',
            "text/html",
        ),
        answer_archive: HttpResponse(
            answer_archive,
            200,
            '<a href="/Static/AnswerKeys/final-key.pdf">RAS final answer key</a>',
            "text/html",
        ),
    })

    result = LiveOfficialSourceDiscovery(transport).run(
        rpsc_source,
        CrawlPolicy(True, rate_limit_seconds=0),
    )

    urls = {candidate.url for candidate in result.candidates}
    assert base + "Static/PreviousQuestionPaper/old-paper.pdf" in urls
    assert base + "Static/AnswerKeys/final-key.pdf" in urls
    titles = {candidate.url: candidate.title for candidate in result.candidates}
    assert titles[base + "Static/PreviousQuestionPaper/old-paper.pdf"] == "RAS old question paper"
    assert titles[base + "Static/AnswerKeys/final-key.pdf"] == "RAS final answer key"
    assert question_archive in transport.requested
    assert answer_archive in transport.requested
    assert base + "robots.txt" in transport.requested



def test_rssb_registry_uses_current_official_host():
    rssb = next(
        source
        for source in build_initial_registry().sources()
        if source.source_id == "RSSB_OFFICIAL"
    )
    assert rssb.base_url == "https://rsmssb.rajasthan.gov.in/"


def test_rssb_discovery_includes_official_question_and_answer_key_archives():
    base = "https://rsmssb.rajasthan.gov.in/"
    source = SourceRecord(
        "RSSB_OFFICIAL",
        "RSSB Official",
        base,
        SourceType.OFFICIAL_WEBSITE,
        SourcePriority.OFFICIAL,
    )
    question_archive = (
        base + "show_archived?menuName=Xj4lCb9vGxpQnfLs/xlZ2g==&theme=Default"
    )
    answer_archive = (
        base + "show_archived?menuName=AGDAnN3xlANlxQ9BZvzaeg==&theme=Red"
    )
    sitemap = base + "sitemap.xml"
    transport = FakeTransport({
        base + "robots.txt": HttpResponse(
            base + "robots.txt",
            200,
            "Sitemap: " + sitemap,
            "text/plain",
        ),
        sitemap: HttpResponse(sitemap, 200, "<urlset></urlset>", "application/xml"),
        question_archive: HttpResponse(
            question_archive,
            200,
            '<a href="/files/Patwar-2021-question-paper.pdf">Patwar 2021 Master Question Paper</a>',
            "text/html",
        ),
        answer_archive: HttpResponse(
            answer_archive,
            200,
            '<a href="/files/Patwar-2021-final-answer-key.pdf">Patwar 2021 Final Answer Key</a>',
            "text/html",
        ),
    })

    result = LiveOfficialSourceDiscovery(transport).run(
        source,
        CrawlPolicy(True, rate_limit_seconds=0),
    )

    by_url = {candidate.url: candidate.title for candidate in result.candidates}
    assert base + "files/Patwar-2021-question-paper.pdf" in by_url
    assert base + "files/Patwar-2021-final-answer-key.pdf" in by_url
    assert question_archive in transport.requested
    assert answer_archive in transport.requested


def test_http_transport_retries_transient_network_failures(monkeypatch):
    from urllib.error import URLError

    calls = []

    class FakeResponse:
        status = 200
        headers = {"Content-Type": "text/plain"}

        def __init__(self, url):
            self.url = url

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return self.url

        def read(self):
            return b"ok"

    class FakeOpener:
        def open(self, request, timeout):
            calls.append((request.full_url, timeout))
            if len(calls) == 1:
                raise URLError("temporary network failure")
            return FakeResponse(request.full_url)

    monkeypatch.setattr("urllib.request.build_opener", lambda _handler: FakeOpener())
    monkeypatch.setattr("ai_comp.research.live_discovery.sleep", lambda _delay: None)

    response = HttpTransport(
        timeout_seconds=3,
        retries=1,
        retry_delay_seconds=0,
    ).get("https://rsmssb.rajasthan.gov.in/robots.txt")

    assert response.status_code == 200
    assert response.content == "ok"
    assert len(calls) == 2



def test_live_discovery_blocks_cross_host_redirects():
    base = "https://rsmssb.rajasthan.gov.in/"
    transport = FakeTransport({
        base + "robots.txt": HttpResponse(
            "https://untrusted.example/robots.txt",
            200,
            "",
            "text/plain",
        ),
    })
    try:
        LiveOfficialSourceDiscovery(transport).run(
            source(),
            CrawlPolicy(True, rate_limit_seconds=0),
        )
    except ValueError as exc:
        assert str(exc) == "cross_host_redirect_blocked"
    else:
        raise AssertionError("cross-host redirects must be rejected")



def test_http_redirect_handler_rejects_cross_host_before_following():
    from urllib.request import Request

    handler = _SameHostRedirectHandler()
    request = Request("https://rsmssb.rajasthan.gov.in/robots.txt")
    try:
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://untrusted.example/robots.txt",
        )
    except ValueError as exc:
        assert str(exc) == "cross_host_redirect_blocked"
    else:
        raise AssertionError("cross-host redirect should not be followed")
