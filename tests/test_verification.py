from datetime import datetime, timezone

import pytest

from ai_comp.domain.sources import SourcePriority
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
    expected_status_for_priority,
    is_historical_evidence_allowed,
)


def test_official_priority_maps_to_verified():
    assert expected_status_for_priority(SourcePriority.OFFICIAL) is VerificationStatus.VERIFIED


def test_secondary_priority_maps_to_secondary_likely():
    assert expected_status_for_priority(SourcePriority.SECONDARY) is VerificationStatus.SECONDARY_LIKELY


def test_unverified_never_supports_verified_history():
    assert is_historical_evidence_allowed(VerificationStatus.UNVERIFIED) is False
    assert is_historical_evidence_allowed(VerificationStatus.SECONDARY_LIKELY) is False
    assert is_historical_evidence_allowed(VerificationStatus.VERIFIED) is True


def test_verification_requires_timezone_aware_timestamp():
    with pytest.raises(ValueError):
        SourceVerification(
            "V1", "S1", "https://example.com/paper.pdf",
            VerificationStatus.VERIFIED,
            EvidenceType.OFFICIAL_PAPER,
            datetime(2026, 1, 1),
        )


def test_verification_validates_confidence():
    with pytest.raises(ValueError):
        SourceVerification.now(
            "V1", "S1", "https://example.com",
            VerificationStatus.VERIFIED,
            EvidenceType.OFFICIAL_PAPER,
            confidence=1.5,
        )


def test_verification_factory_uses_timezone_aware_time():
    record = SourceVerification.now(
        "V1", "S1", "https://example.com",
        VerificationStatus.VERIFIED,
        EvidenceType.OFFICIAL_ARCHIVE,
    )
    assert record.checked_at.tzinfo == timezone.utc
