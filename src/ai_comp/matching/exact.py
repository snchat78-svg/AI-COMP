from hashlib import sha256

from ai_comp.domain.questions import QuestionCandidate
from ai_comp.domain.matching import MatchEvidence, MatchType, QuestionMatch
from ai_comp.matching.normalization import question_text_key


class ExactMatcher:
    """Deterministic exact/normalized-text matcher. No semantic inference."""

    def match(
        self,
        left: QuestionCandidate,
        right: QuestionCandidate,
    ) -> QuestionMatch | None:
        if question_text_key(left.stem) != question_text_key(right.stem):
            return None

        left_options = tuple(question_text_key(option.text) for option in left.options)
        right_options = tuple(question_text_key(option.text) for option in right.options)
        if left_options != right_options:
            return None

        digest = sha256(question_text_key(left.stem).encode("utf-8")).hexdigest()
        evidence = MatchEvidence(
            method="normalized_text_and_options",
            score=1.0,
            notes=f"sha256:{digest}",
        )
        return QuestionMatch(
            left_question_id=left.question_id,
            right_question_id=right.question_id,
            match_type=MatchType.EXACT,
            confidence=1.0,
            evidence=(evidence,),
        )
