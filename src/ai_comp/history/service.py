from collections.abc import Iterable

from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.matching import QuestionMatch
from ai_comp.domain.verification import VerificationStatus
from ai_comp.history.aggregator import QuestionHistory, QuestionHistoryAggregator
from ai_comp.history.repository import AppearanceRepository


class HistoryService:
    """Stores appearances and exposes bounded historical views."""

    def __init__(
        self,
        repository: AppearanceRepository,
        aggregator: QuestionHistoryAggregator | None = None,
    ) -> None:
        self.repository = repository
        self.aggregator = aggregator or QuestionHistoryAggregator()

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

    def build_history(
        self,
        question_id: str,
        matches: Iterable[QuestionMatch] = (),
    ) -> QuestionHistory:
        """Aggregate direct appearance records using the supplied match relationships."""
        match_items = tuple(matches)
        question_ids = {question_id}
        for match in match_items:
            if match.left_question_id == question_id:
                question_ids.add(match.right_question_id)
            elif match.right_question_id == question_id:
                question_ids.add(match.left_question_id)

        appearances = tuple(
            appearance
            for related_question_id in question_ids
            for appearance in self.repository.get_for_question(related_question_id)
        )
        return self.aggregator.aggregate(
            question_id=question_id,
            appearances=appearances,
            matches=match_items,
        )
