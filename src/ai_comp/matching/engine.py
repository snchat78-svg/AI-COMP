from ai_comp.domain.matching import MatchType, QuestionMatch
from ai_comp.domain.questions import QuestionCandidate
from ai_comp.matching.concept import ConceptMatcher
from ai_comp.matching.exact import ExactMatcher
from ai_comp.matching.semantic import SemanticMatcher


class MatchEngine:
    """Ordered matching: exact -> semantic -> concept."""

    def __init__(
        self,
        exact: ExactMatcher | None = None,
        semantic: SemanticMatcher | None = None,
        concept: ConceptMatcher | None = None,
    ) -> None:
        self.exact = exact or ExactMatcher()
        self.semantic = semantic
        self.concept = concept

    def match(self, left: QuestionCandidate, right: QuestionCandidate) -> QuestionMatch | None:
        exact = self.exact.match(left, right)
        if exact is not None:
            return exact
        if self.semantic is not None:
            semantic = self.semantic.match(left, right)
            if semantic is not None:
                return semantic
        if self.concept is not None:
            concept = self.concept.match(left, right)
            if concept is not None:
                return concept
        return None

    @staticmethod
    def is_historical_equivalent(match: QuestionMatch | None) -> bool:
        return match is not None and match.match_type in {
            MatchType.EXACT,
            MatchType.REPHRASED,
        }
