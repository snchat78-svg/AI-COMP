from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from collections.abc import Sequence

from ai_comp.analysis.adaptive_test_composition import AdaptiveTestCompositionService
from ai_comp.domain.adaptive_test_composition import AdaptiveTestCompositionPlan
from ai_comp.domain.learning_history import LearnerLearningHistory
from ai_comp.domain.material_generation import GeneratedMCQ
from ai_comp.domain.question_intelligence import RankedQuestionCandidate
from ai_comp.domain.question_learning import LearnerQuestionHistory
from ai_comp.domain.test_engine import (
    ScoringPolicy,
    TestSession,
    TestSpecification,
)
from ai_comp.test_engine import TestEngine


@dataclass(frozen=True)
class AdaptiveTestSessionResult:
    """Immutable handoff containing the composition explanation and created session."""

    learner_id: str
    composition_plan: AdaptiveTestCompositionPlan
    specification: TestSpecification
    session: TestSession

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        if self.session.test_id != self.specification.test_id:
            raise ValueError("session and specification test IDs do not match")
        if self.specification.question_count != len(
            self.composition_plan.question_ids
        ):
            raise ValueError("composition and specification question counts differ")
        if set(self.session.question_ids) != set(self.composition_plan.question_ids):
            raise ValueError("session questions do not match the composition plan")
        if len(self.session.question_ids) != self.specification.question_count:
            raise ValueError("session question count does not match specification")


class AdaptiveTestSessionService:
    """Orchestrates learner-aware composition and safe handoff to Phase 6.7 TestEngine."""

    def __init__(
        self,
        *,
        composition_service: AdaptiveTestCompositionService | None = None,
        test_engine: TestEngine | None = None,
    ) -> None:
        self.composition_service = (
            composition_service or AdaptiveTestCompositionService()
        )
        self.test_engine = test_engine or TestEngine()

    def create_session(
        self,
        learner_id: str,
        *,
        test_id: str,
        title: str,
        session_id: str,
        question_count: int,
        duration_seconds: int,
        learning_history: LearnerLearningHistory,
        question_history: LearnerQuestionHistory,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        scoring: ScoringPolicy | None = None,
        shuffle_questions: bool = False,
        shuffle_seed: int | None = None,
        exclude_question_ids: Sequence[str] = (),
        as_of: datetime | None = None,
    ) -> AdaptiveTestSessionResult:
        specification = TestSpecification(
            test_id=test_id,
            title=title,
            question_count=question_count,
            duration_seconds=duration_seconds,
            scoring=scoring or ScoringPolicy(),
            shuffle_questions=shuffle_questions,
            shuffle_seed=shuffle_seed,
        )

        plan = self.composition_service.compose(
            learner_id,
            question_count=question_count,
            learning_history=learning_history,
            question_history=question_history,
            candidates=candidates,
            questions=questions,
            exclude_question_ids=exclude_question_ids,
            as_of=as_of,
        )

        question_by_id: dict[str, GeneratedMCQ] = {}
        for question in questions:
            if question.generated_question_id in question_by_id:
                raise ValueError("duplicate generated question ID")
            question_by_id[question.generated_question_id] = question

        try:
            selected_questions = tuple(
                question_by_id[question_id]
                for question_id in plan.question_ids
            )
        except KeyError as exc:
            raise ValueError(
                f"composed question is missing from input: {exc.args[0]}"
            ) from exc

        session = self.test_engine.create_session(
            specification,
            plan.ranked_candidates,
            selected_questions,
            session_id=session_id,
        )
        return AdaptiveTestSessionResult(
            learner_id=learner_id,
            composition_plan=plan,
            specification=specification,
            session=session,
        )

    def start(self, session_id: str) -> TestSession:
        """Start a created session; creation intentionally does not start the timer."""
        return self.test_engine.start(session_id)


__all__ = [
    "AdaptiveTestSessionResult",
    "AdaptiveTestSessionService",
]
