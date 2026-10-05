from dataclasses import dataclass
from collections.abc import Iterable

from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.matching import MatchType, QuestionMatch
from ai_comp.domain.verification import VerificationStatus
from ai_comp.history.dedup import AppearanceDeduplicator, appearance_identity


@dataclass(frozen=True)
class QuestionHistory:
    """Aggregated historical view for one question identity."""

    question_id: str
    exact_appearances: tuple[ExamAppearance, ...]
    rephrased_appearances: tuple[ExamAppearance, ...]
    same_concept_appearances: tuple[ExamAppearance, ...]
    related_topic_appearances: tuple[ExamAppearance, ...]

    @property
    def historical_equivalent_appearances(self) -> tuple[ExamAppearance, ...]:
        return self.exact_appearances + self.rephrased_appearances

    @property
    def verified_appearance_count(self) -> int:
        """Count only verified EXACT/REPHRASED historical-equivalent appearances."""
        return sum(
            appearance.verification.status is VerificationStatus.VERIFIED
            for appearance in self.historical_equivalent_appearances
        )

    @property
    def verified_history_text(self) -> str:
        return f"Verified database में {self.verified_appearance_count} appearances मिले"


class QuestionHistoryAggregator:
    """Builds a bounded history view without treating concept/related links as the same question."""

    def aggregate(
        self,
        question_id: str,
        appearances: Iterable[ExamAppearance],
        matches: Iterable[QuestionMatch] = (),
    ) -> QuestionHistory:
        relationship_by_question = self._relationships_for(question_id, matches)
        buckets: dict[MatchType, list[ExamAppearance]] = {
            MatchType.EXACT: [],
            MatchType.REPHRASED: [],
            MatchType.SAME_CONCEPT: [],
            MatchType.RELATED_TOPIC: [],
        }
        deduplicator = AppearanceDeduplicator()

        for appearance in appearances:
            relation = self._relation_for_appearance(
                question_id, appearance, relationship_by_question
            )
            if relation is None or appearance_identity(appearance) in {
                appearance_identity(item)
                for items in buckets.values()
                for item in items
            }:
                continue
            if deduplicator.seen(appearance):
                continue
            if relation in buckets:
                buckets[relation].append(appearance)

        return QuestionHistory(
            question_id=question_id,
            exact_appearances=tuple(buckets[MatchType.EXACT]),
            rephrased_appearances=tuple(buckets[MatchType.REPHRASED]),
            same_concept_appearances=tuple(buckets[MatchType.SAME_CONCEPT]),
            related_topic_appearances=tuple(buckets[MatchType.RELATED_TOPIC]),
        )

    def _relationships_for(
        self,
        question_id: str,
        matches: Iterable[QuestionMatch],
    ) -> dict[str, MatchType]:
        relationships: dict[str, MatchType] = {}
        precedence = {
            MatchType.EXACT: 4,
            MatchType.REPHRASED: 3,
            MatchType.SAME_CONCEPT: 2,
            MatchType.RELATED_TOPIC: 1,
        }
        for match in matches:
            if match.left_question_id == question_id:
                other_id = match.right_question_id
            elif match.right_question_id == question_id:
                other_id = match.left_question_id
            else:
                continue

            current = relationships.get(other_id)
            if current is None or precedence.get(match.match_type, 0) > precedence.get(current, 0):
                relationships[other_id] = match.match_type
        return relationships

    def _relation_for_appearance(
        self,
        question_id: str,
        appearance: ExamAppearance,
        relationship_by_question: dict[str, MatchType],
    ) -> MatchType | None:
        if appearance.question_id == question_id:
            try:
                relation = MatchType(appearance.match_type)
            except ValueError:
                relation = MatchType.EXACT
            return None if relation is MatchType.NO_MATCH else relation

        return relationship_by_question.get(appearance.question_id)
