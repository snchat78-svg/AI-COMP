from dataclasses import dataclass
from enum import Enum


class MatchType(str, Enum):
    EXACT = "EXACT"
    REPHRASED = "REPHRASED"
    SAME_CONCEPT = "SAME_CONCEPT"
    RELATED_TOPIC = "RELATED_TOPIC"
    NO_MATCH = "NO_MATCH"


@dataclass(frozen=True)
class MatchEvidence:
    method: str
    score: float | None = None
    notes: str = ""


@dataclass(frozen=True)
class QuestionMatch:
    left_question_id: str
    right_question_id: str
    match_type: MatchType
    confidence: float
    evidence: tuple[MatchEvidence, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.left_question_id == self.right_question_id:
            raise ValueError("a question cannot match itself")


@dataclass(frozen=True)
class ConceptRecord:
    concept_id: str
    label: str
    subject: str | None = None
    topic: str | None = None
    subtopic: str | None = None
