from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PerformanceBand(str, Enum):
    STRONG = "STRONG"
    AVERAGE = "AVERAGE"
    WEAK = "WEAK"


@dataclass(frozen=True)
class QuestionOutcome:
    question_id: str
    concept_ids: tuple[str, ...]
    selected_option_key: str | None
    correct_option_key: str
    attempted: bool
    correct: bool
    difficulty: str

    @property
    def incorrect(self) -> bool:
        return self.attempted and not self.correct


@dataclass(frozen=True)
class TopicPerformance:
    concept_id: str
    question_count: int
    attempted_count: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    accuracy: float
    performance: PerformanceBand


@dataclass(frozen=True)
class WeakTopic:
    concept_id: str
    priority_score: float
    accuracy: float
    attempted_count: int
    question_count: int
    reason: str


@dataclass(frozen=True)
class TestAnalysis:
    test_id: str
    session_id: str
    total_questions: int
    attempted_questions: int
    correct_answers: int
    incorrect_answers: int
    unattempted_questions: int
    raw_score: float
    percentage: float
    accuracy: float
    outcomes: tuple[QuestionOutcome, ...]
    topic_performance: tuple[TopicPerformance, ...]
    weak_topics: tuple[WeakTopic, ...]

    def __post_init__(self) -> None:
        if self.total_questions < 1:
            raise ValueError("total_questions must be positive")
        if len(self.outcomes) != self.total_questions:
            raise ValueError("outcome count must equal total questions")
        if self.attempted_questions != self.correct_answers + self.incorrect_answers:
            raise ValueError("attempted count does not reconcile")
        if self.total_questions != self.attempted_questions + self.unattempted_questions:
            raise ValueError("question counts do not reconcile")
