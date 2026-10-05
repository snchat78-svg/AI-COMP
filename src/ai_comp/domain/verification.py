from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from ai_comp.domain.sources import SourcePriority, SourceType


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    SECONDARY_LIKELY = "SECONDARY_LIKELY"
    UNVERIFIED = "UNVERIFIED"


class EvidenceType(str, Enum):
    OFFICIAL_PAPER = "OFFICIAL_PAPER"
    OFFICIAL_ANSWER_KEY = "OFFICIAL_ANSWER_KEY"
    OFFICIAL_ARCHIVE = "OFFICIAL_ARCHIVE"
    TRUSTED_SECONDARY = "TRUSTED_SECONDARY"
    OTHER = "OTHER"


@dataclass(frozen=True)
class SourceVerification:
    verification_id: str
    source_id: str
    source_url: str
    status: VerificationStatus
    evidence_type: EvidenceType
    checked_at: datetime
    confidence: float | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.source_url.startswith(("http://", "https://")):
            raise ValueError("source_url must use http:// or https://")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.checked_at.tzinfo is None:
            raise ValueError("checked_at must be timezone-aware")

    @classmethod
    def now(
        cls,
        verification_id: str,
        source_id: str,
        source_url: str,
        status: VerificationStatus,
        evidence_type: EvidenceType,
        confidence: float | None = None,
        notes: str = "",
    ) -> "SourceVerification":
        return cls(
            verification_id=verification_id,
            source_id=source_id,
            source_url=source_url,
            status=status,
            evidence_type=evidence_type,
            checked_at=datetime.now(timezone.utc),
            confidence=confidence,
            notes=notes,
        )


def expected_status_for_priority(priority: SourcePriority) -> VerificationStatus:
    if priority is SourcePriority.OFFICIAL:
        return VerificationStatus.VERIFIED
    if priority is SourcePriority.SECONDARY:
        return VerificationStatus.SECONDARY_LIKELY
    return VerificationStatus.UNVERIFIED


def is_historical_evidence_allowed(status: VerificationStatus) -> bool:
    """Only verified evidence may support a verified exam-history claim."""
    return status is VerificationStatus.VERIFIED
