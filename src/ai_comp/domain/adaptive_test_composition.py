from __future__ import annotations

from dataclasses import dataclass

from ai_comp.domain.adaptive_difficulty import AdaptiveDifficultyDecision
from ai_comp.domain.question_intelligence import DifficultyLevel, RankedQuestionCandidate


@dataclass(frozen=True)
class AdaptiveTestCompositionPolicy:
    """Deterministic slot and coverage policy for adaptive test composition."""

    retention_ratio: float = 0.60
    revision_ratio: float = 0.40
    remediation_ratio: float = 0.75
    max_concept_ratio: float = 0.50

    def __post_init__(self) -> None:
        for name, value in (
            ("retention_ratio", self.retention_ratio),
            ("revision_ratio", self.revision_ratio),
            ("remediation_ratio", self.remediation_ratio),
            ("max_concept_ratio", self.max_concept_ratio),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.max_concept_ratio <= 0.0:
            raise ValueError("max_concept_ratio must be positive")


@dataclass(frozen=True)
class ConceptCoverage:
    concept_id: str
    selected_count: int
    available_count: int
    action: str

    def __post_init__(self) -> None:
        if not self.concept_id.strip():
            raise ValueError("concept_id is required")
        if self.selected_count < 0 or self.available_count < 0:
            raise ValueError("coverage counts must be non-negative")
        if self.selected_count > self.available_count:
            raise ValueError("selected_count cannot exceed available_count")
        if not self.action.strip():
            raise ValueError("action is required")


@dataclass(frozen=True)
class AdaptiveTestCompositionPlan:
    question_ids: tuple[str, ...]
    ranked_candidates: tuple[RankedQuestionCandidate, ...]
    retention_question_ids: tuple[str, ...]
    revision_question_ids: tuple[str, ...]
    remediation_question_ids: tuple[str, ...]
    advancement_question_ids: tuple[str, ...]
    focus_concept_ids: tuple[str, ...]
    coverage: tuple[ConceptCoverage, ...]
    recommended_difficulty: DifficultyLevel
    reason: str
    decisions: tuple[AdaptiveDifficultyDecision, ...] = ()

    def __post_init__(self) -> None:
        if not self.question_ids:
            raise ValueError("adaptive test composition requires questions")
        if tuple(item.question_id for item in self.ranked_candidates) != self.question_ids:
            raise ValueError("ranked candidates must match question IDs")
        if len(set(self.question_ids)) != len(self.question_ids):
            raise ValueError("question IDs must be unique")
        selected = set(self.question_ids)
        for name, values in (
            ("retention_question_ids", self.retention_question_ids),
            ("revision_question_ids", self.revision_question_ids),
            ("remediation_question_ids", self.remediation_question_ids),
            ("advancement_question_ids", self.advancement_question_ids),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must be unique")
            if not set(values).issubset(selected):
                raise ValueError(f"{name} must contain selected questions")
        if len(set(self.focus_concept_ids)) != len(self.focus_concept_ids):
            raise ValueError("focus concept IDs must be unique")
        if any(not item.strip() for item in self.focus_concept_ids):
            raise ValueError("focus concept IDs must not be empty")
        decision_ids = [item.concept_id for item in self.decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("decisions must contain unique concepts")
        if not self.reason.strip():
            raise ValueError("reason is required")
