from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from ai_comp.domain.sources import CrawlPolicy, SourceRecord


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str


class RobotsAccessChecker:
    def __init__(self, user_agent: str = "AI-COMP/phase2") -> None:
        self.user_agent = user_agent

    def check(self, source: SourceRecord, url: str, policy: CrawlPolicy) -> AccessDecision:
        if not policy.allowed:
            return AccessDecision(False, "research_disabled")
        if not policy.respect_robots:
            return AccessDecision(False, "robots_compliance_required")
        parsed = urlparse(url)
        base = urlparse(source.base_url)
        if parsed.scheme not in {"http", "https"} or parsed.netloc != base.netloc:
            return AccessDecision(False, "outside_registered_domain")
        robots_url = f"{base.scheme}://{base.netloc}/robots.txt"
        parser = RobotFileParser(robots_url)
        try:
            parser.read()
        except OSError:
            return AccessDecision(False, "robots_unavailable")
        return AccessDecision(
            parser.can_fetch(self.user_agent, url),
            "allowed" if parser.can_fetch(self.user_agent, url) else "robots_denied",
        )
