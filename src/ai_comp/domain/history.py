from dataclasses import dataclass
from enum import Enum

from ai_comp.domain.verification import SourceVerification


class AppearanceVerification(str, Enum):
    VERIFIED = "VERIFIED"
    SECONDARY_LIKELY = "SECONDARY_LIKELY"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class ExamAppearance:
    appearance_id: str
    question_id: str
    exam_id: str
    conducting_body_id: str | None
    year: int
    exam_date: str | None
    shift: str | None
    question_number: int
    original_question: str
    options: tuple[tuple[str, str], ...]
    correct_answer: str | None
    source_url: str
    paper_id: str
    verification: SourceVerification
    match_type: str = "EXACT"

    def __post_init__(self) -> None:
        if self.year < 1900:
            raise ValueError("year must be a realistic exam year")
        if self.question_number < 1:
            raise ValueError("question_number must be positive")
        if not self.source_url.startswith(("http://", "https://")):
            raise ValueError("source_url must use http:// or https://")


@dataclass(frozen=True)
class HistoricalQuestion:
    question_id: str
    concept_id: str | None
    appearances: tuple[ExamAppearance, ...]

    @property
    def verified_appearance_count(self) -> int:
        return sum(
            appearance.verification.status.value == "VERIFIED"
            for appearance in self.appearances
        )
