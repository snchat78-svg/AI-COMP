from collections.abc import Callable

from ai_comp.domain.matching import MatchEvidence, MatchType, QuestionMatch
from ai_comp.domain.questions import QuestionCandidate


ConceptResolver = Callable[[QuestionCandidate], str | None]


class ConceptMatcher:
    """Matches questions by an explicit concept resolver, not keyword guessing."""

    def __init__(self, resolve_concept: ConceptResolver) -> None:
        self.resolve_concept = resolve_concept

    def match(self, left: QuestionCandidate, right: QuestionCandidate) -> QuestionMatch | None:
        left_concept = self.resolve_concept(left)
        right_concept = self.resolve_concept(right)
        if not left_concept or left_concept != right_concept:
            return None
        return QuestionMatch(
            left_question_id=left.question_id,
            right_question_id=right.question_id,
            match_type=MatchType.SAME_CONCEPT,
            confidence=0.75,
            evidence=(MatchEvidence(method="concept_id", score=1.0, notes=f"concept_id:{left_concept}"),),
        )
