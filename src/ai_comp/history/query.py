from dataclasses import dataclass

from ai_comp.domain.verification import VerificationStatus


@dataclass(frozen=True)
class HistoryQuery:
    """Optional filters for a question-history read."""

    exam_id: str | None = None
    conducting_body_id: str | None = None
    year: int | None = None
    shift: str | None = None
    verification_status: VerificationStatus | None = None
    verified_only: bool = False

    def __post_init__(self) -> None:
        if self.year is not None and self.year < 1900:
            raise ValueError("year must be a realistic exam year")
        if (
            self.verified_only
            and self.verification_status is not None
            and self.verification_status is not VerificationStatus.VERIFIED
        ):
            raise ValueError(
                "verified_only cannot be combined with a non-VERIFIED status"
            )

    def matches(self, appearance) -> bool:
        """Return True when an appearance satisfies every configured filter."""
        if self.exam_id is not None and appearance.exam_id != self.exam_id:
            return False
        if (
            self.conducting_body_id is not None
            and appearance.conducting_body_id != self.conducting_body_id
        ):
            return False
        if self.year is not None and appearance.year != self.year:
            return False
        if self.shift is not None and appearance.shift != self.shift:
            return False

        status = appearance.verification.status
        if self.verification_status is not None and status is not self.verification_status:
            return False
        if self.verified_only and status is not VerificationStatus.VERIFIED:
            return False
        return True
