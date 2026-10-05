from dataclasses import dataclass
from collections.abc import Iterable

from ai_comp.domain.matching import QuestionMatch
from ai_comp.domain.questions import QuestionCandidate
from ai_comp.matching.engine import MatchEngine
from ai_comp.matching.index import CandidatePairIndex


@dataclass(frozen=True)
class MatchBatch:
    question_id: str
    matches: tuple[QuestionMatch, ...]


class MatchingService:
    """Coordinates indexing and ordered matching while keeping storage separate."""

    def __init__(
        self,
        index: CandidatePairIndex,
        engine: MatchEngine,
    ) -> None:
        self.index = index
        self.engine = engine

    def match_question(
        self,
        question: QuestionCandidate,
        *,
        semantic_limit: int = 100,
    ) -> MatchBatch:
        exact = tuple(
            self.engine.match(question, candidate)
            for candidate in self.index.exact_candidates(question)
        )
        semantic = tuple(
            self.engine.match(question, candidate)
            for candidate in self.index.potential_semantic_candidates(
                question, limit=semantic_limit
            )
        )
        matches = tuple(item for item in (*exact, *semantic) if item is not None)
        return MatchBatch(question_id=question.question_id, matches=matches)

    def match_many(
        self,
        questions: Iterable[QuestionCandidate],
        *,
        semantic_limit: int = 100,
    ) -> tuple[MatchBatch, ...]:
        return tuple(
            self.match_question(question, semantic_limit=semantic_limit)
            for question in questions
        )
