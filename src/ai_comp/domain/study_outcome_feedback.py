from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_schedule import StudyTaskKind
from ai_comp.domain.study_schedule_execution import StudyTaskExecutionStatus


class OutcomeEvidenceKind(str, Enum):
    DIRECT_QUESTION_MATCH = "DIRECT_QUESTION_MATCH"
    CONCEPT_OVERLAP = "CONCEPT_OVERLAP"
    NO_RELATED_EVIDENCE = "NO_RELATED_EVIDENCE"


@dataclass(frozen=True)
class StudyTaskOutcome:
    """Observed result evidence associated with one previously executed study task."""

    task_id: str
    task_kind: StudyTaskKind
    execution_event_ids: tuple[str, ...]
    execution_status: StudyTaskExecutionStatus
    evidence_kind: OutcomeEvidenceKind
    assessment_session_id: str
    assessed_at: datetime
    related_question_ids: tuple[str, ...]
    related_concept_ids: tuple[str, ...]
    question_count: int
    attempted_count: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    accuracy_percentage: float | None
    baseline_attempted_count: int
    baseline_accuracy_percentage: float | None
    follow_up_attempted_count: int
    follow_up_accuracy_percentage: float | None
    delta_percentage_points: float | None
    trend: LearningTrend
    interpretation: str

    def __post_init__(self) -> None:
        for name in ("task_id", "assessment_session_id", "interpretation"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if not self.execution_event_ids:
            raise ValueError("at least one execution event is required")
        if len(self.execution_event_ids) != len(set(self.execution_event_ids)):
            raise ValueError("execution event IDs must be unique")
        if len(self.related_question_ids) != len(set(self.related_question_ids)):
            raise ValueError("related question IDs must be unique")
        if len(self.related_concept_ids) != len(set(self.related_concept_ids)):
            raise ValueError("related concept IDs must be unique")
        if self.assessed_at.tzinfo is None or self.assessed_at.utcoffset() is None:
            raise ValueError("assessed_at must be timezone-aware")
        for name in (
            "question_count", "attempted_count", "correct_count",
            "incorrect_count", "unattempted_count", "baseline_attempted_count",
            "follow_up_attempted_count",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.question_count != self.attempted_count + self.unattempted_count:
            raise ValueError("question counts do not reconcile")
        if self.attempted_count != self.correct_count + self.incorrect_count:
            raise ValueError("attempted count does not reconcile")
        for name, value in (
            ("accuracy_percentage", self.accuracy_percentage),
            ("baseline_accuracy_percentage", self.baseline_accuracy_percentage),
            ("follow_up_accuracy_percentage", self.follow_up_accuracy_percentage),
        ):
            if value is not None and not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be between 0 and 100")
        if self.accuracy_percentage is not None and self.attempted_count == 0:
            raise ValueError("accuracy requires attempted questions")
        if self.baseline_accuracy_percentage is not None and self.baseline_attempted_count == 0:
            raise ValueError("baseline accuracy requires attempted questions")
        if self.follow_up_accuracy_percentage is not None and self.follow_up_attempted_count == 0:
            raise ValueError("follow-up accuracy requires attempted questions")
        if self.trend is LearningTrend.INSUFFICIENT_DATA:
            if self.delta_percentage_points is not None:
                raise ValueError("insufficient-data trend cannot contain a delta")
        elif self.delta_percentage_points is None:
            raise ValueError("available trend requires a delta")


@dataclass(frozen=True)
class StudyOutcomeFeedbackReport:
    """Evidence-linked, non-causal outcome summary for one learner and one test."""

    learner_id: str
    schedule_id: str
    assessment_session_id: str
    assessed_at: datetime
    outcomes: tuple[StudyTaskOutcome, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        for name in ("learner_id", "schedule_id", "assessment_session_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if len(self.schedule_id) != 64:
            raise ValueError("schedule_id must be a 64-character fingerprint")
        try:
            int(self.schedule_id, 16)
        except ValueError as exc:
            raise ValueError("schedule_id must be hexadecimal") from exc
        for name in ("assessed_at", "generated_at"):
            value = getattr(self, name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.generated_at < self.assessed_at:
            raise ValueError("report cannot be generated before the assessment completed")
        task_ids = tuple(item.task_id for item in self.outcomes)
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("task outcomes must be unique per task")
        for item in self.outcomes:
            if item.assessment_session_id != self.assessment_session_id:
                raise ValueError("task outcome references a different assessment")
            if item.assessed_at != self.assessed_at:
                raise ValueError("task outcome assessment timestamp does not match report")

    @property
    def linked_task_count(self) -> int:
        return sum(
            item.evidence_kind is not OutcomeEvidenceKind.NO_RELATED_EVIDENCE
            for item in self.outcomes
        )

    @property
    def comparison_count(self) -> int:
        return sum(
            item.trend is not LearningTrend.INSUFFICIENT_DATA
            for item in self.outcomes
        )


__all__ = [
    "OutcomeEvidenceKind",
    "StudyOutcomeFeedbackReport",
    "StudyTaskOutcome",
]
