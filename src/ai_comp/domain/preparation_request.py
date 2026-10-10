from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.test_engine import TestSpecification


class PreparationRequestStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class PreparationTestRequest:
    """Validated preparation settings resolved for one authenticated learner."""

    learner_id: str
    specification: TestSpecification
    mode: PersonalizedPreparationMode = PersonalizedPreparationMode.ADAPTIVE
    concept_ids: tuple[str, ...] = ()
    exclude_question_ids: tuple[str, ...] = ()
    as_of: datetime | None = None
    exam_id: str | None = None
    subject_id: str | None = None

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        if len(set(self.concept_ids)) != len(self.concept_ids):
            raise ValueError("concept_ids must be unique")
        if any(not item.strip() for item in self.concept_ids):
            raise ValueError("concept_ids must not be empty")
        if len(set(self.exclude_question_ids)) != len(self.exclude_question_ids):
            raise ValueError("exclude_question_ids must be unique")
        if any(not item.strip() for item in self.exclude_question_ids):
            raise ValueError("exclude_question_ids must not be empty")
        for name, value in (("exam_id", self.exam_id), ("subject_id", self.subject_id)):
            if value is not None and (not value.strip() or value != value.strip()):
                raise ValueError(f"{name} must be a non-empty trimmed string when supplied")
        if self.as_of is not None and (
            self.as_of.tzinfo is None or self.as_of.utcoffset() is None
        ):
            raise ValueError("as_of must be timezone-aware when supplied")


@dataclass(frozen=True)
class PreparationTestRequestRecord:
    request_id: str
    request: PreparationTestRequest
    status: PreparationRequestStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        for name in ("created_at", "updated_at"):
            value = getattr(self, name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")


__all__ = [
    "PreparationRequestStatus",
    "PreparationTestRequest",
    "PreparationTestRequestRecord",
]
