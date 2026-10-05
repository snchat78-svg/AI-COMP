from collections.abc import Iterable

from ai_comp.database.repository import MatchRepository
from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.matching import QuestionMatch
from ai_comp.domain.verification import VerificationStatus
from ai_comp.history.aggregator import QuestionHistory, QuestionHistoryAggregator
from ai_comp.history.query import HistoryQuery
from ai_comp.history.repository import AppearanceRepository
from ai_comp.history.view import HistoricalQuestionView


class HistoryService:
    """Stores appearances and exposes bounded historical views."""

    def __init__(
        self,
        repository: AppearanceRepository,
        aggregator: QuestionHistoryAggregator | None = None,
        match_repository: MatchRepository | None = None,
    ) -> None:
        self.repository = repository
        self.aggregator = aggregator or QuestionHistoryAggregator()
        self.match_repository = match_repository

    def record(self, appearance: ExamAppearance) -> None:
        self.repository.save(appearance)

    def record_many(self, appearances: Iterable[ExamAppearance]) -> None:
        for appearance in appearances:
            self.record(appearance)

    def verified_count(self, question_id: str) -> int:
        return self.build_history(question_id).verified_appearance_count

    def get_history_view(
        self,
        question_id: str,
        matches: Iterable[QuestionMatch] | None = None,
    ) -> HistoricalQuestionView:
        return HistoricalQuestionView.from_history(
            self.build_history(question_id, matches)
        )

    def query_history_view(
        self,
        question_id: str,
        matches: Iterable[QuestionMatch] | None = None,
        query: HistoryQuery | None = None,
    ) -> HistoricalQuestionView:
        """Build a history view after applying optional exam/verification filters."""
        history = self.build_history(question_id, matches)
        if query is None:
            return HistoricalQuestionView.from_history(history)

        filtered = QuestionHistory(
            question_id=history.question_id,
            exact_appearances=tuple(
                item for item in history.exact_appearances if query.matches(item)
            ),
            rephrased_appearances=tuple(
                item for item in history.rephrased_appearances if query.matches(item)
            ),
            same_concept_appearances=tuple(
                item for item in history.same_concept_appearances if query.matches(item)
            ),
            related_topic_appearances=tuple(
                item for item in history.related_topic_appearances if query.matches(item)
            ),
        )
        return HistoricalQuestionView.from_history(filtered)

    def _resolve_matches(
        self,
        question_id: str,
        matches: Iterable[QuestionMatch] | None,
    ) -> tuple[QuestionMatch, ...]:
        if matches is not None:
            return tuple(matches)
        if self.match_repository is None:
            return ()
        return tuple(self.match_repository.get_for_question(question_id))

    def build_history(
        self,
        question_id: str,
        matches: Iterable[QuestionMatch] | None = None,
    ) -> QuestionHistory:
        """Aggregate direct appearance records using supplied or persisted relationships."""
        match_items = self._resolve_matches(question_id, matches)
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
