from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from ai_comp.domain.question_intelligence import RankedQuestionCandidate


class ReviewStatus(str, Enum):
    DUE = "DUE"
    UPCOMING = "UPCOMING"


@dataclass(frozen=True)
class SpacedRevisionPolicy:
    first_interval_days: int = 1
    second_interval_days: int = 3
    third_interval_days: int = 7
    max_interval_days: int = 30
    mistake_weight: float = 0.45
    overdue_weight: float = 0.40
    repetition_weight: float = 0.15

    def __post_init__(self) -> None:
        intervals = (
            self.first_interval_days,
            self.second_interval_days,
            self.third_interval_days,
            self.max_interval_days,
        )
        if any(value < 1 for value in intervals):
            raise ValueError("review intervals must be positive")
        if not (
            self.first_interval_days
            <= self.second_interval_days
            <= self.third_interval_days
            <= self.max_interval_days
        ):
            raise ValueError("review intervals must be non-decreasing")
        weights = (
            self.mistake_weight,
            self.overdue_weight,
            self.repetition_weight,
        )
        if any(value < 0.0 for value in weights):
            raise ValueError("review weights must be non-negative")
        if abs(sum(weights) - 1.0) > 1e-9:
            raise ValueError("review weights must sum to 1")


@dataclass(frozen=True)
class LearnerQuestionReviewSchedule:
    learner_id: str
    question_id: str
    last_review_at: datetime
    next_review_at: datetime
    interval_days: int
    correct_streak: int
    mistake_count: int
    mistake_streak: int
    status: ReviewStatus
    overdue_days: float
    priority_score: float

    def __post_init__(self) -> None:
        for name in ("learner_id", "question_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.interval_days < 1:
            raise ValueError("interval_days must be positive")
        if self.correct_streak < 0 or self.mistake_count < 0 or self.mistake_streak < 0:
            raise ValueError("review counters must be non-negative")
        if self.next_review_at < self.last_review_at:
            raise ValueError("next review cannot precede last review")
        if self.overdue_days < 0.0:
            raise ValueError("overdue_days must be non-negative")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")


@dataclass(frozen=True)
class TimeAwareQuestionPlan:
    question_ids: tuple[str, ...]
    ranked_candidates: tuple[RankedQuestionCandidate, ...]
    due_question_ids: tuple[str, ...]
    focus_question_ids: tuple[str, ...]
    schedules: tuple[LearnerQuestionReviewSchedule, ...]

    def __post_init__(self) -> None:
        if not self.question_ids:
            raise ValueError("time-aware plan requires questions")
        if tuple(item.question_id for item in self.ranked_candidates) != self.question_ids:
            raise ValueError("ranked candidates must match question IDs")
        if len(set(self.question_ids)) != len(self.question_ids):
            raise ValueError("question IDs must be unique")
        if not set(self.due_question_ids).issubset(self.question_ids):
            raise ValueError("due question IDs must be selected")
        if not set(self.focus_question_ids).issubset(self.question_ids):
            raise ValueError("focus question IDs must be selected")


def next_interval_days(
    correct_streak: int,
    *,
    policy: SpacedRevisionPolicy,
) -> int:
    if correct_streak <= 0:
        return policy.first_interval_days
    if correct_streak == 1:
        return policy.first_interval_days
    if correct_streak == 2:
        return policy.second_interval_days
    if correct_streak == 3:
        return policy.third_interval_days

    doubled = policy.third_interval_days * (2 ** (correct_streak - 3))
    return min(policy.max_interval_days, doubled)
