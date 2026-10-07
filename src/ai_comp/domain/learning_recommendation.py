from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ai_comp.domain.question_intelligence import RankedQuestionCandidate


class RecommendedDifficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"


@dataclass(frozen=True)
class LearningRecommendation:
    concept_id: str
    priority_score: float
    accuracy: float
    recommended_difficulty: RecommendedDifficulty
    reason: str

    def __post_init__(self) -> None:
        if not self.concept_id.strip():
            raise ValueError("concept_id is required")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError("accuracy must be between 0 and 1")
        if not self.reason.strip():
            raise ValueError("reason is required")


@dataclass(frozen=True)
class LearningRecommendationPolicy:
    """Deterministic policy for turning weak topics into study actions."""

    max_recommendations: int = 3
    easy_accuracy_threshold: float = 0.25
    focus_ratio: float = 0.75

    def __post_init__(self) -> None:
        if self.max_recommendations < 1:
            raise ValueError("max_recommendations must be positive")
        if not 0.0 <= self.easy_accuracy_threshold <= 0.50:
            raise ValueError("easy_accuracy_threshold must be between 0 and 0.50")
        if not 0.0 < self.focus_ratio <= 1.0:
            raise ValueError("focus_ratio must be between 0 and 1")


@dataclass(frozen=True)
class NextTestPlan:
    question_ids: tuple[str, ...]
    ranked_candidates: tuple[RankedQuestionCandidate, ...]
    focus_concept_ids: tuple[str, ...]
    recommendations: tuple[LearningRecommendation, ...]

    def __post_init__(self) -> None:
        if not self.question_ids:
            raise ValueError("next test plan requires at least one question")
        if tuple(candidate.question_id for candidate in self.ranked_candidates) != self.question_ids:
            raise ValueError("ranked candidates must exactly match question IDs")
        if not self.focus_concept_ids:
            raise ValueError("next test plan requires at least one focus concept")
        if not self.recommendations:
            raise ValueError("next test plan requires learning recommendations")
