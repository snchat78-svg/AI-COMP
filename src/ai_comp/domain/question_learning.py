from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
from typing import Protocol

from ai_comp.domain.question_intelligence import RankedQuestionCandidate


class QuestionOutcomeKind(str, Enum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    UNATTEMPTED = "UNATTEMPTED"


@dataclass(frozen=True)
class LearnerQuestionAttemptRecord:
    outcome_id: str
    attempt_id: str
    learner_id: str
    test_id: str
    session_id: str
    question_id: str
    concept_ids: tuple[str, ...]
    difficulty: str
    selected_option_key: str | None
    correct_option_key: str
    outcome: QuestionOutcomeKind
    completed_at: datetime

    def __post_init__(self) -> None:
        for name in (
            "outcome_id",
            "attempt_id",
            "learner_id",
            "test_id",
            "session_id",
            "question_id",
            "difficulty",
            "correct_option_key",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if len(set(self.concept_ids)) != len(self.concept_ids):
            raise ValueError("concept_ids must be unique")
        if any(not concept.strip() for concept in self.concept_ids):
            raise ValueError("concept IDs must not be empty")

        if self.outcome is QuestionOutcomeKind.UNATTEMPTED:
            if self.selected_option_key is not None:
                raise ValueError("unattempted outcome cannot have a selected option")
        elif not self.selected_option_key or not self.selected_option_key.strip():
            raise ValueError("attempted outcome requires selected_option_key")

        if self.outcome is QuestionOutcomeKind.CORRECT:
            if self.selected_option_key is None:
                raise ValueError("correct outcome requires selected_option_key")
            if self.selected_option_key.strip().upper() != self.correct_option_key.strip().upper():
                raise ValueError("correct outcome must match correct option")


@dataclass(frozen=True)
class LearnerQuestionPerformance:
    question_id: str
    concept_ids: tuple[str, ...]
    difficulty: str
    test_count: int
    attempt_count: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    accuracy: float
    last_outcome: QuestionOutcomeKind
    mistake_count: int
    mistake_streak: int
    priority_score: float
    last_seen_at: datetime

    def __post_init__(self) -> None:
        if not self.question_id.strip():
            raise ValueError("question_id is required")
        if self.test_count < 1 or self.attempt_count < 0:
            raise ValueError("question history counts are invalid")
        if self.correct_count + self.incorrect_count != self.attempt_count:
            raise ValueError("attempt count does not reconcile")
        if self.attempt_count + self.unattempted_count < 1:
            raise ValueError("question history must contain an occurrence")
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError("accuracy must be between 0 and 1")
        if self.mistake_count != self.incorrect_count:
            raise ValueError("mistake count must equal incorrect count")
        if self.mistake_streak < 0:
            raise ValueError("mistake_streak must be non-negative")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")


@dataclass(frozen=True)
class QuestionRevisionCandidate:
    question_id: str
    concept_ids: tuple[str, ...]
    difficulty: str
    priority_score: float
    mistake_count: int
    mistake_streak: int
    last_incorrect_at: datetime
    reason: str

    def __post_init__(self) -> None:
        if not self.question_id.strip():
            raise ValueError("question_id is required")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")
        if self.mistake_count < 1:
            raise ValueError("revision candidate must contain a mistake")
        if self.mistake_streak < 0:
            raise ValueError("mistake_streak must be non-negative")
        if not self.reason.strip():
            raise ValueError("reason is required")


@dataclass(frozen=True)
class RepeatedConceptAlert:
    concept_id: str
    test_count: int
    weak_test_count: int
    question_count: int
    attempted_count: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    accuracy: float
    priority_score: float
    reason: str

    def __post_init__(self) -> None:
        if not self.concept_id.strip():
            raise ValueError("concept_id is required")
        if self.test_count < 2:
            raise ValueError("repeated concept alert requires at least two tests")
        if self.weak_test_count < 1:
            raise ValueError("weak_test_count must be positive")
        if self.question_count < 1:
            raise ValueError("question_count must be positive")
        if self.attempted_count != self.correct_count + self.incorrect_count:
            raise ValueError("concept attempted count does not reconcile")
        if self.question_count != self.attempted_count + self.unattempted_count:
            raise ValueError("concept question count does not reconcile")
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError("concept accuracy must be between 0 and 1")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")
        if not self.reason.strip():
            raise ValueError("reason is required")


@dataclass(frozen=True)
class LearnerQuestionHistory:
    learner_id: str
    outcomes: tuple[LearnerQuestionAttemptRecord, ...]
    question_performance: tuple[LearnerQuestionPerformance, ...]
    revision_candidates: tuple[QuestionRevisionCandidate, ...]
    repeated_concept_alerts: tuple[RepeatedConceptAlert, ...]
    generated_at: datetime


@dataclass(frozen=True)
class QuestionRecommendationPlan:
    question_ids: tuple[str, ...]
    ranked_candidates: tuple[RankedQuestionCandidate, ...]
    revision_question_ids: tuple[str, ...]
    alert_concept_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.question_ids:
            raise ValueError("recommendation plan requires questions")
        if tuple(candidate.question_id for candidate in self.ranked_candidates) != self.question_ids:
            raise ValueError("ranked candidates must match question IDs")
        if not set(self.revision_question_ids).issubset(self.question_ids):
            raise ValueError("revision question IDs must be selected")
        if len(set(self.question_ids)) != len(self.question_ids):
            raise ValueError("question IDs must be unique")


class QuestionLearningHistoryConflictError(RuntimeError):
    """Raised when a learner/question attempt conflicts with existing history."""


class LearnerQuestionHistoryRepository(Protocol):
    def save_outcomes(
        self,
        outcomes: tuple[LearnerQuestionAttemptRecord, ...],
    ) -> None: ...

    def list_outcomes(
        self,
        learner_id: str,
    ) -> tuple[LearnerQuestionAttemptRecord, ...]: ...


def question_attempt_identity(
    learner_id: str,
    session_id: str,
    question_id: str,
) -> str:
    value = (
        f"{learner_id.strip()}\n{session_id.strip()}\n{question_id.strip()}"
    ).encode("utf-8")
    return sha256(value).hexdigest()
