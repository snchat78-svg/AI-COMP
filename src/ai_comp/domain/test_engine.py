from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TestSessionStatus(str, Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class ScoringPolicy:
    correct_marks: float = 1.0
    incorrect_marks: float = -0.25
    unattempted_marks: float = 0.0

    def __post_init__(self) -> None:
        if self.correct_marks <= 0.0:
            raise ValueError("correct_marks must be positive")
        if self.incorrect_marks > 0.0:
            raise ValueError("incorrect_marks must be zero or negative")
        if self.unattempted_marks > 0.0:
            raise ValueError("unattempted_marks must be zero or negative")


@dataclass(frozen=True)
class TestSpecification:
    test_id: str
    title: str
    question_count: int
    duration_seconds: int
    scoring: ScoringPolicy = ScoringPolicy()
    shuffle_questions: bool = False
    shuffle_seed: int | None = None

    def __post_init__(self) -> None:
        if not self.test_id.strip() or not self.title.strip():
            raise ValueError("test_id and title are required")
        if self.question_count < 1:
            raise ValueError("question_count must be positive")
        if self.duration_seconds < 1:
            raise ValueError("duration_seconds must be positive")
        if self.shuffle_questions and self.shuffle_seed is None:
            raise ValueError("shuffle_seed is required when shuffle_questions is enabled")


@dataclass(frozen=True)
class TestAnswer:
    question_id: str
    selected_option_key: str
    answered_at_seconds: float

    def __post_init__(self) -> None:
        if not self.question_id.strip():
            raise ValueError("question_id is required")
        if not self.selected_option_key.strip():
            raise ValueError("selected_option_key is required")
        if self.answered_at_seconds < 0.0:
            raise ValueError("answered_at_seconds must be non-negative")


@dataclass(frozen=True)
class TestResult:
    test_id: str
    session_id: str
    status: TestSessionStatus
    total_questions: int
    attempted_questions: int
    correct_answers: int
    incorrect_answers: int
    unattempted_questions: int
    raw_score: float
    max_score: float
    percentage: float
    accuracy: float
    timed_out: bool

    def __post_init__(self) -> None:
        if self.total_questions < 1:
            raise ValueError("total_questions must be positive")
        for name in (
            "attempted_questions",
            "correct_answers",
            "incorrect_answers",
            "unattempted_questions",
        ):
            value = getattr(self, name)
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.attempted_questions != self.correct_answers + self.incorrect_answers:
            raise ValueError("attempted_questions must equal correct + incorrect")
        if self.total_questions != self.attempted_questions + self.unattempted_questions:
            raise ValueError("question counts do not reconcile")
        if self.max_score <= 0.0:
            raise ValueError("max_score must be positive")
        if not -100.0 <= self.percentage <= 100.0:
            raise ValueError("percentage must be between -100 and 100")
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError("accuracy must be between 0 and 1")


@dataclass(frozen=True)
class TestSession:
    session_id: str
    test_id: str
    question_ids: tuple[str, ...]
    current_index: int
    answers: tuple[TestAnswer, ...]
    review_question_ids: tuple[str, ...]
    status: TestSessionStatus
    started_at: float | None
    deadline_at: float | None
    submitted_at: float | None
    result: TestResult | None = None

    def __post_init__(self) -> None:
        if not self.session_id.strip() or not self.test_id.strip():
            raise ValueError("session_id and test_id are required")
        if not self.question_ids:
            raise ValueError("test session requires questions")
        if len(set(self.question_ids)) != len(self.question_ids):
            raise ValueError("test session question IDs must be unique")
        if not 0 <= self.current_index < len(self.question_ids):
            raise ValueError("current_index is out of range")
        answer_ids = [answer.question_id for answer in self.answers]
        if len(answer_ids) != len(set(answer_ids)):
            raise ValueError("a question may have only one current answer")
        if set(answer_ids) - set(self.question_ids):
            raise ValueError("answers contain unknown question IDs")
        if set(self.review_question_ids) - set(self.question_ids):
            raise ValueError("review set contains unknown question IDs")
        if self.status is TestSessionStatus.IN_PROGRESS:
            if self.started_at is None or self.deadline_at is None:
                raise ValueError("active sessions require timing state")
        if self.status in (
            TestSessionStatus.SUBMITTED,
            TestSessionStatus.EXPIRED,
            TestSessionStatus.CANCELLED,
        ) and self.submitted_at is None:
            raise ValueError("finished sessions require submitted_at")


class TestSessionRepository:
    def save(self, session: TestSession) -> None:
        raise NotImplementedError

    def get(self, session_id: str) -> TestSession:
        raise NotImplementedError


class InMemoryTestSessionRepository(TestSessionRepository):
    def __init__(self) -> None:
        self._sessions: dict[str, TestSession] = {}

    def save(self, session: TestSession) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> TestSession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise KeyError(f"test session not found: {session_id}") from exc
