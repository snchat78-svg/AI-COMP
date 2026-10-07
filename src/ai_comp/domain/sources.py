from dataclasses import dataclass
from enum import Enum


class SourcePriority(str, Enum):
    OFFICIAL = "OFFICIAL"
    SECONDARY = "SECONDARY"
    UNVERIFIED = "UNVERIFIED"


class SourceType(str, Enum):
    OFFICIAL_WEBSITE = "OFFICIAL_WEBSITE"
    OFFICIAL_PAPER = "OFFICIAL_PAPER"
    OFFICIAL_ANSWER_KEY = "OFFICIAL_ANSWER_KEY"
    TRUSTED_SECONDARY = "TRUSTED_SECONDARY"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    name: str
    base_url: str
    source_type: SourceType
    priority: SourcePriority
    conducting_body_id: str | None = None
    allowed_paths: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class CrawlPolicy:
    allowed: bool
    respect_robots: bool = True
    respect_terms: bool = True
    rate_limit_seconds: float = 1.0
    max_depth: int = 2
    notes: str = ""
