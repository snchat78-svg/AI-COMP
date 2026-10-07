from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Protocol
from datetime import datetime


class LongTermPerformanceBand(str, Enum):
    STRONG = "STRONG"
    AVERAGE = "AVERAGE"
    WEAK = "WEAK"


class LearningTrend(str, Enum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class LearningAttemptRecord:
    attempt_id: str
    learner_id: str
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
    completed_at: datetime

    def __post_init__(self) -> None:
        for name in ("attempt_id", "learner_id", "test_id", "session_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.total_questions < 1:
            raise ValueError("total_questions must be positive")
        if self.attempted_questions != self.correct_answers + self.incorrect_answers:
            raise ValueError("attempted count does not reconcile")
        if self.total_questions != self.attempted_questions + self.unattempted_questions:
            raise ValueError("question counts do not reconcile")
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError("accuracy must be between 0 and 1")


@dataclass(frozen=True)
class TopicAttemptRecord:
    attempt_id: str
    learner_id: str
    test_id: str
    session_id: str
    concept_id: str
    question_count: int
    attempted_count: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    accuracy: float
    performance: LongTermPerformanceBand

    def __post_init__(self) -> None:
        if not self.attempt_id.strip() or not self.learner_id.strip():
            raise ValueError("attempt identity is required")
        if not self.test_id.strip() or not self.session_id.strip():
            raise ValueError("test/session identity is required")
        if not self.concept_id.strip():
            raise ValueError("concept_id is required")
        if self.question_count < 1:
            raise ValueError("question_count must be positive")
        if self.attempted_count != self.correct_count + self.incorrect_count:
            raise ValueError("topic attempted count does not reconcile")
        if self.question_count != self.attempted_count + self.unattempted_count:
            raise ValueError("topic question counts do not reconcile")
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError("topic accuracy must be between 0 and 1")


@dataclass(frozen=True)
class LearnerTopicPerformance:
    concept_id: str
    test_count: int
    question_count: int
    attempted_count: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    accuracy: float
    recent_accuracy: float
    performance: LongTermPerformanceBand
    trend: LearningTrend
    weak_streak: int
    priority_score: float

    def __post_init__(self) -> None:
        if not self.concept_id.strip():
            raise ValueError("concept_id is required")
        if self.test_count < 1 or self.question_count < 1:
            raise ValueError("topic history counts must be positive")
        if self.attempted_count != self.correct_count + self.incorrect_count:
            raise ValueError("history attempted count does not reconcile")
        if self.question_count != self.attempted_count + self.unattempted_count:
            raise ValueError("history question counts do not reconcile")
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError("history accuracy must be between 0 and 1")
        if not 0.0 <= self.recent_accuracy <= 1.0:
            raise ValueError("recent accuracy must be between 0 and 1")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")


@dataclass(frozen=True)
class LearnerLearningHistory:
    learner_id: str
    attempts: tuple[LearningAttemptRecord, ...]
    topic_performance: tuple[LearnerTopicPerformance, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")


class LearningHistoryConflictError(RuntimeError):
    """Raised when an existing learner attempt conflicts with a new payload."""


class LearningHistoryRepository(Protocol):
    def save_attempt(
        self,
        attempt: LearningAttemptRecord,
        topics: tuple[TopicAttemptRecord, ...],
    ) -> None: ...

    def get_attempt(
        self,
        learner_id: str,
        session_id: str,
    ) -> LearningAttemptRecord | None: ...

    def list_attempts(
        self,
        learner_id: str,
    ) -> tuple[LearningAttemptRecord, ...]: ...

    def list_topic_attempts(
        self,
        learner_id: str,
    ) -> tuple[TopicAttemptRecord, ...]: ...


def attempt_identity(learner_id: str, session_id: str) -> str:
    value = f"{learner_id.strip()}\n{session_id.strip()}".encode("utf-8")
    return sha256(value).hexdigest()
