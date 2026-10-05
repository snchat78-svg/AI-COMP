from collections import defaultdict
from collections.abc import Iterable

from ai_comp.domain.questions import QuestionCandidate
from ai_comp.matching.normalization import question_text_key


class CandidatePairIndex:
    """Builds bounded candidate pairs without performing semantic matching."""

    def __init__(self, questions: Iterable[QuestionCandidate] = ()) -> None:
        self._questions: dict[str, QuestionCandidate] = {}
        self._exact_keys: dict[str, list[str]] = defaultdict(list)
        self.add_many(questions)

    @staticmethod
    def exact_key(question: QuestionCandidate) -> str:
        stem = question_text_key(question.stem)
        options = "|".join(
            f"{option.key}:{question_text_key(option.text)}"
            for option in question.options
        )
        return f"{stem}||{options}"

    def add(self, question: QuestionCandidate) -> None:
        if question.question_id in self._questions:
            return
        self._questions[question.question_id] = question
        key = self.exact_key(question)
        if question.question_id not in self._exact_keys[key]:
            self._exact_keys[key].append(question.question_id)

    def add_many(self, questions: Iterable[QuestionCandidate]) -> None:
        for question in questions:
            self.add(question)

    def exact_candidates(self, question: QuestionCandidate) -> tuple[QuestionCandidate, ...]:
        return tuple(
            self._questions[item_id]
            for item_id in self._exact_keys.get(self.exact_key(question), ())
            if item_id != question.question_id
        )

    def potential_semantic_candidates(
        self,
        question: QuestionCandidate,
        *,
        limit: int = 100,
    ) -> tuple[QuestionCandidate, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        exact_ids = {
            candidate.question_id for candidate in self.exact_candidates(question)
        }
        candidates = (
            item
            for item in self._questions.values()
            if item.question_id != question.question_id
            and item.question_id not in exact_ids
        )
        return tuple(candidates)[:limit]
