from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ai_comp.domain.learning_progress import LearnerProgressReport
from ai_comp.domain.personalized_preparation import PersonalizedPreparationPlan


class PreparationActionKind(str, Enum):
    REVIEW_PREVIOUS_MISTAKES = "REVIEW_PREVIOUS_MISTAKES"
    PRACTICE_WEAK_TOPICS = "PRACTICE_WEAK_TOPICS"
    REVIEW_RETENTION_ITEMS = "REVIEW_RETENTION_ITEMS"
    RESPOND_TO_DECLINING_TREND = "RESPOND_TO_DECLINING_TREND"
    MAINTAIN_STUDY_ROUTINE = "MAINTAIN_STUDY_ROUTINE"
    COLLECT_MORE_PROGRESS_DATA = "COLLECT_MORE_PROGRESS_DATA"


@dataclass(frozen=True)
class PreparationGuidanceAction:
    """One deterministic, explainable learner action derived from stored evidence."""

    kind: PreparationActionKind
    title: str
    reason: str
    priority_score: float
    concept_ids: tuple[str, ...] = ()
    question_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.title.strip() or not self.reason.strip():
            raise ValueError("action title and reason are required")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")
        for name, values in (
            ("concept_ids", self.concept_ids),
            ("question_ids", self.question_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must be unique")
            if any(not value.strip() for value in values):
                raise ValueError(f"{name} must not contain empty IDs")


@dataclass(frozen=True)
class PreparationGuidance:
    """Progress-aware preparation plan for one learner, with ranked next actions."""

    learner_id: str
    progress_report: LearnerProgressReport
    preparation_plan: PersonalizedPreparationPlan
    actions: tuple[PreparationGuidanceAction, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        if self.progress_report.learner_id != self.learner_id:
            raise ValueError("progress report learner does not match")
        if self.preparation_plan.learner_id != self.learner_id:
            raise ValueError("preparation plan learner does not match")
        if not self.actions:
            raise ValueError("at least one preparation action is required")
        kinds = tuple(action.kind for action in self.actions)
        if len(kinds) != len(set(kinds)):
            raise ValueError("preparation action kinds must be unique")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")


__all__ = [
    "PreparationActionKind",
    "PreparationGuidance",
    "PreparationGuidanceAction",
]
