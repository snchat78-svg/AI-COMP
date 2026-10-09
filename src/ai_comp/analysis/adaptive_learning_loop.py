from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from collections.abc import Sequence

from ai_comp.analysis.adaptive_test_session import (
    AdaptiveTestSessionResult,
    AdaptiveTestSessionService,
)
from ai_comp.domain.adaptive_difficulty import AdaptiveDifficultyProfile
from ai_comp.domain.learning_history import LearnerLearningHistory
from ai_comp.domain.material_generation import GeneratedMCQ
from ai_comp.domain.question_intelligence import RankedQuestionCandidate
from ai_comp.domain.question_learning import LearnerQuestionHistory
from ai_comp.domain.test_engine import ScoringPolicy


@dataclass(frozen=True)
class AdaptiveLearningLoopResult:
    """A completed feedback snapshot plus the next personalized test session."""

    learner_id: str
    completed_session_id: str
    completed_test_percentage: float
    weak_concept_ids: tuple[str, ...]
    adaptive_profile: AdaptiveDifficultyProfile
    next_test: AdaptiveTestSessionResult

    def __post_init__(self) -> None:
        if not self.learner_id.strip() or not self.completed_session_id.strip():
            raise ValueError("learner and completed session IDs are required")
        if not 0.0 <= self.completed_test_percentage <= 100.0:
            raise ValueError("completed test percentage must be between 0 and 100")
        if len(set(self.weak_concept_ids)) != len(self.weak_concept_ids):
            raise ValueError("weak concept IDs must be unique")
        if self.adaptive_profile.learner_id != self.learner_id:
            raise ValueError("adaptive profile learner does not match")
        if self.next_test.learner_id != self.learner_id:
            raise ValueError("next test learner does not match")
        if set(self.weak_concept_ids) - {
            decision.concept_id for decision in self.adaptive_profile.decisions
        }:
            raise ValueError("weak concepts must be represented in adaptive profile")


class AdaptiveLearningLoopService:
    """Builds the next adaptive test directly from the completed feedback snapshot.

    This orchestration layer consumes the existing persisted-history views and
    delegates composition/session creation to Phase 6.14/6.15 services. It does
    not write history itself or start the next test timer.
    """

    def __init__(
        self,
        *,
        adaptive_session_service: AdaptiveTestSessionService | None = None,
    ) -> None:
        self.adaptive_session_service = (
            adaptive_session_service or AdaptiveTestSessionService()
        )

    def create_next_test(
        self,
        learner_id: str,
        *,
        completed_feedback,
        test_id: str,
        title: str,
        session_id: str,
        question_count: int,
        duration_seconds: int,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        scoring: ScoringPolicy | None = None,
        shuffle_questions: bool = False,
        shuffle_seed: int | None = None,
        exclude_question_ids: Sequence[str] = (),
        as_of: datetime | None = None,
    ) -> AdaptiveLearningLoopResult:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if completed_feedback.learner_id != learner_id:
            raise ValueError("completed feedback learner does not match")
        if completed_feedback.session.status.value not in {"SUBMITTED", "EXPIRED"}:
            raise ValueError("adaptive follow-up requires a completed test")
        if completed_feedback.result.session_id != completed_feedback.session.session_id:
            raise ValueError("completed result does not match session")
        if completed_feedback.learning_history.learner_id != learner_id:
            raise ValueError("learning history learner does not match")
        if completed_feedback.question_history.learner_id != learner_id:
            raise ValueError("question history learner does not match")

        # Recompute from the just-updated histories using the same policy service
        # used by the composition layer, so the returned profile explains selection.
        profile = self.adaptive_session_service.composition_service.adaptive_difficulty_service.analyze(
            learner_id,
            completed_feedback.learning_history,
            completed_feedback.question_history,
            as_of=as_of,
        )
        weak_concept_ids = tuple(
            dict.fromkeys(item.concept_id for item in completed_feedback.analysis.weak_topics)
        )
        decisions = {item.concept_id for item in profile.decisions}
        # A weak topic may be absent from long-term history when there is not enough
        # persisted evidence; do not fabricate a decision or claim it drove adaptation.
        represented_weak_concepts = tuple(
            concept_id for concept_id in weak_concept_ids if concept_id in decisions
        )

        next_test = self.adaptive_session_service.create_session(
            learner_id,
            test_id=test_id,
            title=title,
            session_id=session_id,
            question_count=question_count,
            duration_seconds=duration_seconds,
            learning_history=completed_feedback.learning_history,
            question_history=completed_feedback.question_history,
            candidates=candidates,
            questions=questions,
            scoring=scoring,
            shuffle_questions=shuffle_questions,
            shuffle_seed=shuffle_seed,
            exclude_question_ids=exclude_question_ids,
            as_of=as_of,
        )
        return AdaptiveLearningLoopResult(
            learner_id=learner_id,
            completed_session_id=completed_feedback.session.session_id,
            completed_test_percentage=completed_feedback.result.percentage,
            weak_concept_ids=represented_weak_concepts,
            adaptive_profile=profile,
            next_test=next_test,
        )


__all__ = ["AdaptiveLearningLoopResult", "AdaptiveLearningLoopService"]
