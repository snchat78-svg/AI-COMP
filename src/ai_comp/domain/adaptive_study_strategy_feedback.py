from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ai_comp.domain.adaptive_study_strategy import StudyStrategyAction
from ai_comp.domain.adaptive_study_strategy_history import StrategyHistoryScopeKind
from ai_comp.domain.study_schedule import StudyTaskKind


class StrategyFeedbackKind(str, Enum):
    CHANGE_APPROACH = "CHANGE_APPROACH"


@dataclass(frozen=True)
class StudyStrategyFeedbackFinding:
    """An evidence-qualified, non-causal next-step recommendation for one scope."""

    scope_kind: StrategyHistoryScopeKind
    scope_ids: tuple[str, ...]
    task_kind: StudyTaskKind
    decision_count: int
    assessment_count: int
    declining_count: int
    improving_count: int
    mean_delta_percentage_points: float
    latest_action: StudyStrategyAction
    kind: StrategyFeedbackKind
    priority_score: float
    reason: str

    def __post_init__(self) -> None:
        if not self.scope_ids or any(not value.strip() for value in self.scope_ids):
            raise ValueError("scope_ids are required")
        if len(self.scope_ids) != len(set(self.scope_ids)):
            raise ValueError("scope_ids must be unique")
        for name in ("decision_count", "assessment_count", "declining_count", "improving_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.decision_count < 1 or self.assessment_count < 1:
            raise ValueError("decision_count and assessment_count must be positive")
        if self.assessment_count > self.decision_count:
            raise ValueError("assessment_count cannot exceed decision_count")
        if self.declining_count + self.improving_count > self.decision_count:
            raise ValueError("trend counts cannot exceed decision_count")
        if not -100.0 <= self.mean_delta_percentage_points <= 100.0:
            raise ValueError("mean delta must be between -100 and 100")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")
        if not self.reason.strip():
            raise ValueError("reason is required")


@dataclass(frozen=True)
class AdaptiveStudyStrategyFeedbackReport:
    """Read-only summary of whether past strategy history warrants a change prompt."""

    learner_id: str
    source_audit_count: int
    evaluated_scope_count: int
    not_actionable_scope_count: int
    findings: tuple[StudyStrategyFeedbackFinding, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        for name in (
            "source_audit_count",
            "evaluated_scope_count",
            "not_actionable_scope_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.not_actionable_scope_count + len(self.findings) != self.evaluated_scope_count:
            raise ValueError("feedback scope counts do not reconcile")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        keys = tuple((item.scope_kind, item.scope_ids, item.task_kind) for item in self.findings)
        if len(keys) != len(set(keys)):
            raise ValueError("feedback findings must be unique per scope and task kind")


__all__ = [
    "AdaptiveStudyStrategyFeedbackReport",
    "StrategyFeedbackKind",
    "StudyStrategyFeedbackFinding",
]
