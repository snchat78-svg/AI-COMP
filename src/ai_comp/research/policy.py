from urllib.parse import urlparse

from ai_comp.domain.sources import CrawlPolicy, SourceRecord


class ResearchPolicyError(ValueError):
    pass


def validate_candidate_url(source: SourceRecord, url: str, policy: CrawlPolicy) -> None:
    if not policy.allowed:
        raise ResearchPolicyError("Research is disabled by crawl policy")
    if not policy.respect_robots:
        raise ResearchPolicyError("robots.txt compliance must remain enabled")
    if not policy.respect_terms:
        raise ResearchPolicyError("terms/access compliance must remain enabled")
    parsed = urlparse(url)
    base = urlparse(source.base_url)
    if parsed.scheme not in {"http", "https"}:
        raise ResearchPolicyError("Only HTTP(S) URLs are allowed")
    if parsed.netloc != base.netloc:
        raise ResearchPolicyError("URL is outside the registered source domain")
    if source.allowed_paths and not any(parsed.path.startswith(p) for p in source.allowed_paths):
        raise ResearchPolicyError("URL is outside the source allowed paths")


def can_research_source(source: SourceRecord, policy: CrawlPolicy) -> bool:
    return policy.allowed and policy.respect_robots and policy.respect_terms
