from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


@dataclass(frozen=True)
class QuestionIntelligenceInput:
    """Evidence used to score an accepted generated question."""

    generated_question_id: str
    requested_difficulty: DifficultyLevel
    fact_importance_scores: tuple[float, ...] = ()
    fact_confidences: tuple[float, ...] = ()
    concept_confidences: tuple[float, ...] = ()
    verified_appearance_count: int = 0
    novelty_score: float = 1.0
    coverage_score: float = 0.0
    difficulty_signal: float | None = None

    def __post_init__(self) -> None:
        if not self.generated_question_id.strip():
            raise ValueError("generated_question_id is required")
        for name, values in (
            ("fact_importance_scores", self.fact_importance_scores),
            ("fact_confidences", self.fact_confidences),
            ("concept_confidences", self.concept_confidences),
        ):
            if any(not 0.0 <= value <= 1.0 for value in values):
                raise ValueError(f"{name} values must be between 0 and 1")
        if self.verified_appearance_count < 0:
            raise ValueError("verified_appearance_count must be non-negative")
        for name, value in (
            ("novelty_score", self.novelty_score),
            ("coverage_score", self.coverage_score),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.difficulty_signal is not None and not 0.0 <= self.difficulty_signal <= 1.0:
            raise ValueError("difficulty_signal must be between 0 and 1")


@dataclass(frozen=True)
class QuestionIntelligenceScore:
    generated_question_id: str
    difficulty: DifficultyLevel
    difficulty_score: float
    importance_score: float
    novelty_score: float
    coverage_score: float
    selection_score: float

    def __post_init__(self) -> None:
        if not self.generated_question_id.strip():
            raise ValueError("generated_question_id is required")
        for name in (
            "difficulty_score",
            "importance_score",
            "novelty_score",
            "coverage_score",
            "selection_score",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class RankedQuestionCandidate:
    question_id: str
    score: QuestionIntelligenceScore
    rank: int


@dataclass(frozen=True)
class QuestionIntelligencePolicy:
    """Transparent scoring policy; weights are deliberately explicit."""

    fact_importance_weight: float = 0.40
    historical_frequency_weight: float = 0.30
    fact_confidence_weight: float = 0.15
    concept_confidence_weight: float = 0.15
    selection_importance_weight: float = 0.55
    selection_novelty_weight: float = 0.25
    selection_coverage_weight: float = 0.20

    def __post_init__(self) -> None:
        weights = (
            self.fact_importance_weight,
            self.historical_frequency_weight,
            self.fact_confidence_weight,
            self.concept_confidence_weight,
        )
        if any(value < 0.0 for value in weights):
            raise ValueError("importance weights must be non-negative")
        if abs(sum(weights) - 1.0) > 1e-9:
            raise ValueError("importance weights must sum to 1")
        selection = (
            self.selection_importance_weight,
            self.selection_novelty_weight,
            self.selection_coverage_weight,
        )
        if any(value < 0.0 for value in selection):
            raise ValueError("selection weights must be non-negative")
        if abs(sum(selection) - 1.0) > 1e-9:
            raise ValueError("selection weights must sum to 1")
