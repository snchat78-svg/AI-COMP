from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ai_comp.domain.adaptive_difficulty import AdaptiveDifficultyDecision
from ai_comp.domain.learning_recommendation import LearningRecommendation
from ai_comp.domain.learning_history import LearnerLearningHistory
from ai_comp.domain.question_intelligence import RankedQuestionCandidate, DifficultyLevel
from ai_comp.domain.question_learning import LearnerQuestionHistory
from ai_comp.domain.test_engine import ScoringPolicy, TestSpecification


class PersonalizedPreparationMode(str, Enum):
    ADAPTIVE = "ADAPTIVE"
    REVISION = "REVISION"
    WEAK_TOPICS = "WEAK_TOPICS"
    MIXED = "MIXED"


@dataclass(frozen=True)
class PersonalizedPreparationPolicy:
    """Deterministic orchestration policy for Phase 8 personalized preparation."""

    revision_ratio: float = 0.40
    weak_topic_ratio: float = 0.75
    easy_accuracy_threshold: float = 0.25

    def __post_init__(self) -> None:
        for name, value in (
            ("revision_ratio", self.revision_ratio),
            ("weak_topic_ratio", self.weak_topic_ratio),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if not 0.0 <= self.easy_accuracy_threshold <= 0.50:
            raise ValueError("easy_accuracy_threshold must be between 0 and 0.50")


@dataclass(frozen=True)
class PersonalizedPreparationPlan:
    learner_id: str
    test_specification: TestSpecification
    mode: PersonalizedPreparationMode
    recommended_difficulty: DifficultyLevel | None
    question_ids: tuple[str, ...]
    ranked_candidates: tuple[RankedQuestionCandidate, ...]
    focus_concept_ids: tuple[str, ...]
    revision_question_ids: tuple[str, ...]
    recommendations: tuple[LearningRecommendation, ...]
    reason: str
    adaptive_decisions: tuple[AdaptiveDifficultyDecision, ...] = ()
    retention_due_question_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        if not self.question_ids:
            raise ValueError("personalized preparation requires questions")
        if self.test_specification.question_count != len(self.question_ids):
            raise ValueError("test specification question count does not match plan")
        if tuple(candidate.question_id for candidate in self.ranked_candidates) != self.question_ids:
            raise ValueError("ranked candidates must match question IDs")
        if len(set(self.question_ids)) != len(self.question_ids):
            raise ValueError("question IDs must be unique")
        if not set(self.revision_question_ids).issubset(self.question_ids):
            raise ValueError("revision question IDs must be selected")
        if any(not concept.strip() for concept in self.focus_concept_ids):
            raise ValueError("focus concept IDs must not be empty")
        if not self.reason.strip():
            raise ValueError("reason is required")
        if len(set(self.retention_due_question_ids)) != len(self.retention_due_question_ids):
            raise ValueError("retention due question IDs must be unique")
        if not set(self.retention_due_question_ids).issubset(self.question_ids):
            raise ValueError("retention due question IDs must be selected")
        decision_ids = [decision.concept_id for decision in self.adaptive_decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("adaptive decisions must have unique concepts")
