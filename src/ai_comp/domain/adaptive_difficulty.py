from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.question_intelligence import DifficultyLevel


class MasteryStatus(str, Enum):
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    LEARNING = "LEARNING"
    DEVELOPING = "DEVELOPING"
    MASTERED = "MASTERED"
    RETENTION_DUE = "RETENTION_DUE"


class AdaptiveAction(str, Enum):
    STABILIZE = "STABILIZE"
    REMEDIATE = "REMEDIATE"
    ADVANCE = "ADVANCE"
    RETAIN = "RETAIN"


@dataclass(frozen=True)
class AdaptiveDifficultyPolicy:
    """Conservative deterministic policy for learner difficulty evolution."""

    min_tests_for_progression: int = 2
    mastery_min_tests: int = 3
    remediation_accuracy_threshold: float = 0.50
    mastery_accuracy_threshold: float = 0.85
    mastery_recent_accuracy_threshold: float = 0.85
    decline_threshold: float = -0.10

    def __post_init__(self) -> None:
        if self.min_tests_for_progression < 1:
            raise ValueError("min_tests_for_progression must be positive")
        if self.mastery_min_tests < self.min_tests_for_progression:
            raise ValueError(
                "mastery_min_tests must be at least min_tests_for_progression"
            )
        for name, value in (
            ("remediation_accuracy_threshold", self.remediation_accuracy_threshold),
            ("mastery_accuracy_threshold", self.mastery_accuracy_threshold),
            ("mastery_recent_accuracy_threshold", self.mastery_recent_accuracy_threshold),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if not -1.0 <= self.decline_threshold <= 0.0:
            raise ValueError("decline_threshold must be between -1 and 0")


@dataclass(frozen=True)
class AdaptiveDifficultyDecision:
    concept_id: str
    test_count: int
    accuracy: float
    recent_accuracy: float
    trend: LearningTrend
    weak_streak: int
    mastery: MasteryStatus
    action: AdaptiveAction
    recommended_difficulty: DifficultyLevel
    retention_due_count: int
    priority_score: float
    reason: str

    def __post_init__(self) -> None:
        if not self.concept_id.strip():
            raise ValueError("concept_id is required")
        if self.test_count < 1:
            raise ValueError("test_count must be positive")
        for name, value in (
            ("accuracy", self.accuracy),
            ("recent_accuracy", self.recent_accuracy),
            ("priority_score", self.priority_score),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.weak_streak < 0 or self.retention_due_count < 0:
            raise ValueError("adaptive counters must be non-negative")
        if not self.reason.strip():
            raise ValueError("reason is required")


@dataclass(frozen=True)
class AdaptiveDifficultyProfile:
    learner_id: str
    decisions: tuple[AdaptiveDifficultyDecision, ...]
    recommended_difficulty: DifficultyLevel
    retention_due_question_ids: tuple[str, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        if len(set(self.retention_due_question_ids)) != len(
            self.retention_due_question_ids
        ):
            raise ValueError("retention_due_question_ids must be unique")
        if any(
            not question_id.strip()
            for question_id in self.retention_due_question_ids
        ):
            raise ValueError("retention due question IDs must not be empty")
        decision_ids = [decision.concept_id for decision in self.decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("adaptive decisions must have unique concepts")


__all__ = [
    "AdaptiveAction",
    "AdaptiveDifficultyDecision",
    "AdaptiveDifficultyPolicy",
    "AdaptiveDifficultyProfile",
    "MasteryStatus",
]
