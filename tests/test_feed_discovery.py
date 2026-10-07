from ai_comp.domain.sources import CrawlPolicy, SourcePriority, SourceRecord, SourceType
from ai_comp.research.feed_discovery import FeedDiscovery


def source():
    return SourceRecord("S", "RSSB", "https://rssb.rajasthan.gov.in/", SourceType.OFFICIAL_WEBSITE, SourcePriority.OFFICIAL)


def test_sitemap_and_feed_links_are_domain_filtered():
    d = FeedDiscovery(source(), CrawlPolicy(True))
    sitemap = """<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://rssb.rajasthan.gov.in/papers/a.pdf</loc></url>
      <url><loc>https://evil.example/x.pdf</loc></url>
    </urlset>"""
    links = d.sitemap_links(sitemap)
    assert [x.url for x in links] == ["https://rssb.rajasthan.gov.in/papers/a.pdf"]

    feed = """<rss><channel>
      <item><link>https://rssb.rajasthan.gov.in/papers/b.pdf</link></item>
      <item><link>https://evil.example/y.pdf</link></item>
    </channel></rss>"""
    links = d.feed_links(feed)
    assert [x.url for x in links] == ["https://rssb.rajasthan.gov.in/papers/b.pdf"]


def test_discovered_links_become_candidates():
    d = FeedDiscovery(source(), CrawlPolicy(True))
    links = d.sitemap_links("""<urlset><url><loc>https://rssb.rajasthan.gov.in/a.pdf</loc></url></urlset>""")
    candidates = d.candidates(links, "S")
    assert len(candidates) == 1
    assert candidates[0].url.endswith(".pdf")
