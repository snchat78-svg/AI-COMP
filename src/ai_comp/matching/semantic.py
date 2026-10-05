from collections.abc import Callable

from ai_comp.domain.matching import MatchEvidence, MatchType, QuestionMatch
from ai_comp.domain.questions import QuestionCandidate


EmbeddingFunction = Callable[[str], tuple[float, ...]]


class SemanticMatcher:
    """Embedding matcher with an injected model; never calls an LLM implicitly."""

    def __init__(self, embed: EmbeddingFunction, threshold: float = 0.90) -> None:
        if not 0.0 < threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        self.embed = embed
        self.threshold = threshold

    def similarity(self, left: QuestionCandidate, right: QuestionCandidate) -> float:
        a = self.embed(left.stem)
        b = self.embed(right.stem)
        if not a or not b or len(a) != len(b):
            raise ValueError("embedding vectors must be non-empty and same length")
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def match(self, left: QuestionCandidate, right: QuestionCandidate) -> QuestionMatch | None:
        score = self.similarity(left, right)
        if score < self.threshold:
            return None
        return QuestionMatch(
            left_question_id=left.question_id,
            right_question_id=right.question_id,
            match_type=MatchType.REPHRASED,
            confidence=max(0.0, min(1.0, score)),
            evidence=(MatchEvidence(method="embedding_cosine", score=score),),
        )
