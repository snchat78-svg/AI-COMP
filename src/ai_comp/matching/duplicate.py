from dataclasses import dataclass
from hashlib import sha256

from ai_comp.domain.questions import QuestionCandidate
from ai_comp.matching.normalization import question_text_key


@dataclass(frozen=True)
class QuestionDuplicateKey:
    normalized_key: str


def duplicate_key(question: QuestionCandidate) -> QuestionDuplicateKey:
    parts = [question_text_key(question.stem)]
    parts.extend(f"{option.key}:{question_text_key(option.text)}" for option in question.options)
    value = "|".join(parts)
    return QuestionDuplicateKey(sha256(value.encode("utf-8")).hexdigest())


class QuestionDuplicateDetector:
    """Detects copied question records without treating them as exam appearances."""

    def are_duplicates(self, left: QuestionCandidate, right: QuestionCandidate) -> bool:
        return duplicate_key(left) == duplicate_key(right)
