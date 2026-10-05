from collections.abc import Iterable

from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.verification import VerificationStatus
from ai_comp.history.repository import AppearanceRepository


class HistoryService:
    """Stores appearances and exposes bounded verified-history counts."""

    def __init__(self, repository: AppearanceRepository) -> None:
        self.repository = repository

    def record(self, appearance: ExamAppearance) -> None:
        self.repository.save(appearance)

    def record_many(self, appearances: Iterable[ExamAppearance]) -> None:
        for appearance in appearances:
            self.record(appearance)

    def verified_count(self, question_id: str) -> int:
        appearances = self.repository.get_for_question(question_id)
        return sum(
            item.verification.status is VerificationStatus.VERIFIED
            for item in appearances
        )
