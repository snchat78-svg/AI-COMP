from ai_comp.domain.sources import CrawlPolicy, SourcePriority, SourceRecord, SourceType
from ai_comp.research.live_discovery import HttpResponse, LiveOfficialSourceDiscovery

class FakeTransport:
    def __init__(self, pages):
        self.pages = pages
        self.requested = []
    def get(self, url):
        self.requested.append(url)
        return self.pages[url]

def source():
    return SourceRecord("RSSB", "RSSB", "https://rssb.rajasthan.gov.in/", SourceType.OFFICIAL_WEBSITE, SourcePriority.OFFICIAL, allowed_paths=("/papers/", "/archive/"))

def test_live_discovery_uses_robots_sitemap_and_creates_candidates():
    base = "https://rssb.rajasthan.gov.in/"
    transport = FakeTransport({
        base + "robots.txt": HttpResponse(base + "robots.txt", 200, "User-agent: AI-COMP/phase2\nSitemap: https://rssb.rajasthan.gov.in/sitemap.xml\n", "text/plain"),
        base + "sitemap.xml": HttpResponse(base + "sitemap.xml", 200, '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://rssb.rajasthan.gov.in/papers/a.pdf</loc></url><url><loc>https://evil.example/x.pdf</loc></url></urlset>', "application/xml"),
    })
    result = LiveOfficialSourceDiscovery(transport).run(source(), CrawlPolicy(True, rate_limit_seconds=0))
    assert [c.url for c in result.candidates] == [base + "papers/a.pdf"]
    assert base + "robots.txt" in transport.requested
    assert base + "sitemap.xml" in transport.requested

def test_live_discovery_handles_sitemap_index_with_bound():
    base = "https://rssb.rajasthan.gov.in/"
    transport = FakeTransport({
        base + "robots.txt": HttpResponse(base + "robots.txt", 200, "User-agent: AI-COMP/phase2\nSitemap: https://rssb.rajasthan.gov.in/sitemap_index.xml\n", "text/plain"),
        base + "sitemap_index.xml": HttpResponse(base + "sitemap_index.xml", 200, '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://rssb.rajasthan.gov.in/sitemap-1.xml</loc></sitemap></sitemapindex>', "application/xml"),
        base + "sitemap-1.xml": HttpResponse(base + "sitemap-1.xml", 200, '<urlset><url><loc>https://rssb.rajasthan.gov.in/papers/b.pdf</loc></url></urlset>', "application/xml"),
    })
    result = LiveOfficialSourceDiscovery(transport).run(source(), CrawlPolicy(True, max_depth=2, rate_limit_seconds=0))
    assert [c.url for c in result.candidates] == [base + "papers/b.pdf"]
    assert base + "sitemap-1.xml" in transport.requested

def test_live_discovery_fails_closed_when_robots_missing():
    base = "https://rssb.rajasthan.gov.in/"
    transport = FakeTransport({base + "robots.txt": HttpResponse(base + "robots.txt", 404, "", "text/plain")})
    try:
        LiveOfficialSourceDiscovery(transport).run(source(), CrawlPolicy(True, rate_limit_seconds=0))
    except ValueError as exc:
        assert str(exc) == "robots_unavailable"
    else:
        raise AssertionError("expected robots_unavailable")