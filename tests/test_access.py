from ai_comp.domain.sources import CrawlPolicy, SourcePriority, SourceRecord, SourceType
from ai_comp.research.access import RobotsAccessChecker


def test_robots_check_requires_enabled_compliance():
    source = SourceRecord("S", "RSSB", "RSSB", SourceType.OFFICIAL_WEBSITE, SourcePriority.OFFICIAL)
    source = SourceRecord("S", "RSSB", "https://rssb.rajasthan.gov.in/", SourceType.OFFICIAL_WEBSITE, SourcePriority.OFFICIAL)
    decision = RobotsAccessChecker().check(source, "https://rssb.rajasthan.gov.in/a.pdf", CrawlPolicy(True, respect_robots=False))
    assert decision.allowed is False
    assert decision.reason == "robots_compliance_required"
