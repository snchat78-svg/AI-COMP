from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ai_comp.domain.adaptive_difficulty import AdaptiveAction, MasteryStatus
from ai_comp.domain.learning_history import LearningTrend, LongTermPerformanceBand


@dataclass(frozen=True)
class LearnerTopicProgress:
    """Topic-level progress with existing history and optional adaptive decision."""

    concept_id: str
    accuracy: float
    recent_accuracy: float
    trend: LearningTrend
    performance: LongTermPerformanceBand
    weak_streak: int
    priority_score: float
    mastery: MasteryStatus | None = None
    recommended_action: AdaptiveAction | None = None
    decision_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.concept_id.strip():
            raise ValueError("concept_id is required")
        for name, value in (
            ("accuracy", self.accuracy),
            ("recent_accuracy", self.recent_accuracy),
            ("priority_score", self.priority_score),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.weak_streak < 0:
            raise ValueError("weak_streak must be non-negative")
        if self.decision_reason is not None and not self.decision_reason.strip():
            raise ValueError("decision_reason must not be empty")


@dataclass(frozen=True)
class LearnerProgressReport:
    """Read-only progress snapshot derived from persisted learner outcome histories."""

    learner_id: str
    completed_test_count: int
    total_questions: int
    current_test_percentage: float | None
    baseline_average_percentage: float | None
    recent_average_percentage: float | None
    delta_percentage_points: float | None
    trend: LearningTrend
    baseline_test_count: int
    recent_test_count: int
    question_outcome_count: int
    question_attempt_count: int
    question_correct_count: int
    question_accuracy: float | None
    topics: tuple[LearnerTopicProgress, ...]
    retention_due_question_ids: tuple[str, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        for name in (
            "completed_test_count", "total_questions", "baseline_test_count",
            "recent_test_count", "question_outcome_count",
            "question_attempt_count", "question_correct_count",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.question_correct_count > self.question_attempt_count:
            raise ValueError("correct question count cannot exceed attempted count")
        if self.question_attempt_count > self.question_outcome_count:
            raise ValueError("attempted question count cannot exceed outcome count")
        for name, value in (
            ("current_test_percentage", self.current_test_percentage),
            ("baseline_average_percentage", self.baseline_average_percentage),
            ("recent_average_percentage", self.recent_average_percentage),
        ):
            if value is not None and not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be between 0 and 100")
        if self.question_accuracy is not None and not 0.0 <= self.question_accuracy <= 1.0:
            raise ValueError("question_accuracy must be between 0 and 1")
        if self.trend is LearningTrend.INSUFFICIENT_DATA:
            if any(value is not None for value in (
                self.baseline_average_percentage,
                self.recent_average_percentage,
                self.delta_percentage_points,
            )):
                raise ValueError("insufficient-data report cannot contain a comparison")
            if self.baseline_test_count or self.recent_test_count:
                raise ValueError("insufficient-data report cannot contain comparison counts")
        else:
            if any(value is None for value in (
                self.baseline_average_percentage,
                self.recent_average_percentage,
                self.delta_percentage_points,
            )):
                raise ValueError("comparison metrics are required when trend is available")
            if self.baseline_test_count < 1 or self.recent_test_count < 1:
                raise ValueError("comparison test counts must be positive")
            if self.baseline_test_count != self.recent_test_count:
                raise ValueError("baseline and recent comparison windows must match")
        topic_ids = tuple(topic.concept_id for topic in self.topics)
        if len(topic_ids) != len(set(topic_ids)):
            raise ValueError("topic progress must have unique concepts")
        if len(set(self.retention_due_question_ids)) != len(self.retention_due_question_ids):
            raise ValueError("retention due question IDs must be unique")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")


__all__ = ["LearnerProgressReport", "LearnerTopicProgress"]
