from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ai_comp.domain.adaptive_study_strategy import StudyStrategyAction
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_schedule import StudyTaskKind


class StrategyHistoryScopeKind(str, Enum):
    CONCEPTS = "CONCEPTS"
    QUESTIONS = "QUESTIONS"


@dataclass(frozen=True)
class StrategyAuditHistoryEntry:
    audit_id: str
    assessment_session_id: str
    source_schedule_id: str
    resulting_schedule_id: str
    recorded_at: datetime
    adjustment_count: int
    adapted_task_count: int
    evidence_limited_count: int
    baseline_accuracy_percentage: float | None
    follow_up_accuracy_percentage: float | None
    delta_percentage_points: float | None
    actions: tuple[StudyStrategyAction, ...]
    trends: tuple[LearningTrend, ...]

    def __post_init__(self) -> None:
        for name in (
            "audit_id", "assessment_session_id", "source_schedule_id",
            "resulting_schedule_id",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.recorded_at.tzinfo is None or self.recorded_at.utcoffset() is None:
            raise ValueError("recorded_at must be timezone-aware")
        for name in ("adjustment_count", "adapted_task_count", "evidence_limited_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.adapted_task_count + self.evidence_limited_count != self.adjustment_count:
            raise ValueError("strategy history entry counts do not reconcile")
        if len(self.actions) != self.adjustment_count or len(self.trends) != self.adjustment_count:
            raise ValueError("actions and trends must align with adjustments")
        for name, value in (
            ("baseline_accuracy_percentage", self.baseline_accuracy_percentage),
            ("follow_up_accuracy_percentage", self.follow_up_accuracy_percentage),
        ):
            if value is not None and not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be between 0 and 100")


@dataclass(frozen=True)
class ConceptStrategyHistory:
    scope_kind: StrategyHistoryScopeKind
    scope_ids: tuple[str, ...]
    task_kind: StudyTaskKind
    decision_count: int
    assessment_count: int
    improving_count: int
    declining_count: int
    stable_count: int
    insufficient_data_count: int
    mean_baseline_accuracy_percentage: float | None
    mean_follow_up_accuracy_percentage: float | None
    mean_delta_percentage_points: float | None
    mean_recommended_priority_delta: float | None
    mean_applied_priority_delta: float | None
    latest_action: StudyStrategyAction
    latest_recorded_at: datetime

    def __post_init__(self) -> None:
        if not self.scope_ids or any(not item.strip() for item in self.scope_ids):
            raise ValueError("scope_ids are required")
        if self.decision_count < 1 or self.assessment_count < 1:
            raise ValueError("decision and assessment counts must be positive")
        trend_total = (
            self.improving_count + self.declining_count
            + self.stable_count + self.insufficient_data_count
        )
        if trend_total != self.decision_count:
            raise ValueError("scope trend counts do not reconcile")
        for name, value in (
            ("mean_baseline_accuracy_percentage", self.mean_baseline_accuracy_percentage),
            ("mean_follow_up_accuracy_percentage", self.mean_follow_up_accuracy_percentage),
        ):
            if value is not None and not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be between 0 and 100")
        for name, value in (
            ("mean_delta_percentage_points", self.mean_delta_percentage_points),
            ("mean_recommended_priority_delta", self.mean_recommended_priority_delta),
            ("mean_applied_priority_delta", self.mean_applied_priority_delta),
        ):
            if value is not None and not -100.0 <= value <= 100.0:
                raise ValueError(f"{name} is outside the supported range")
        if self.latest_recorded_at.tzinfo is None or self.latest_recorded_at.utcoffset() is None:
            raise ValueError("latest_recorded_at must be timezone-aware")


@dataclass(frozen=True)
class AdaptiveStudyStrategyHistoryReport:
    learner_id: str
    entries: tuple[StrategyAuditHistoryEntry, ...]
    scopes: tuple[ConceptStrategyHistory, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        audit_ids = tuple(entry.audit_id for entry in self.entries)
        if len(audit_ids) != len(set(audit_ids)):
            raise ValueError("audit history entry IDs must be unique")
        if any(entry.assessment_session_id.strip() == "" for entry in self.entries):
            raise ValueError("assessment session is required")
        scope_keys = tuple((item.scope_kind, item.scope_ids, item.task_kind) for item in self.scopes)
        if len(scope_keys) != len(set(scope_keys)):
            raise ValueError("strategy scopes must be unique")

    @property
    def audit_count(self) -> int:
        return len(self.entries)

    @property
    def decision_count(self) -> int:
        return sum(entry.adjustment_count for entry in self.entries)

    @property
    def adapted_task_count(self) -> int:
        return sum(entry.adapted_task_count for entry in self.entries)

    @property
    def evidence_limited_count(self) -> int:
        return sum(entry.evidence_limited_count for entry in self.entries)


__all__ = [
    "AdaptiveStudyStrategyHistoryReport",
    "ConceptStrategyHistory",
    "StrategyAuditHistoryEntry",
    "StrategyHistoryScopeKind",
]
