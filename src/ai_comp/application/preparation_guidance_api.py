from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any

from ai_comp.analysis.adaptive_study_strategy_history import AdaptiveStudyStrategyHistoryService
from ai_comp.analysis.preparation_guidance import PreparationGuidanceService
from ai_comp.domain.adaptive_study_strategy_feedback import AdaptiveStudyStrategyFeedbackReport
from ai_comp.domain.adaptive_study_strategy_history import AdaptiveStudyStrategyHistoryReport
from ai_comp.domain.learning_history import LearnerLearningHistory
from ai_comp.domain.material_generation import GeneratedMCQ
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.preparation_guidance import PreparationGuidance
from ai_comp.domain.question_intelligence import RankedQuestionCandidate
from ai_comp.domain.question_learning import LearnerQuestionHistory
from ai_comp.domain.test_analysis import TestAnalysis
from ai_comp.domain.test_engine import ScoringPolicy


def to_json_value(value: Any) -> Any:
    """Convert supported domain values to standard JSON-compatible primitives.

    Enum values use their stable wire string and dates use ISO-8601. This helper
    rejects unknown objects rather than leaking repr() strings into API payloads.
    """
    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: to_json_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("JSON payload mappings must use string keys")
        return {key: to_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_json_value(item) for item in value]
    raise TypeError(f"unsupported API payload value: {type(value).__name__}")


@dataclass(frozen=True)
class PreparationGuidanceAPIResponse:
    """Versioned API response envelope; independent of any HTTP framework."""

    learner_id: str
    guidance: PreparationGuidance
    strategy_history: AdaptiveStudyStrategyHistoryReport
    strategy_feedback: AdaptiveStudyStrategyFeedbackReport
    generated_at: datetime
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.learner_id.strip():
            raise ValueError("learner_id is required")
        if self.guidance.learner_id != self.learner_id:
            raise ValueError("guidance learner does not match response")
        if self.strategy_history.learner_id != self.learner_id:
            raise ValueError("strategy history learner does not match response")
        if self.strategy_feedback.learner_id != self.learner_id:
            raise ValueError("strategy feedback learner does not match response")
        if self.guidance.strategy_feedback_report != self.strategy_feedback:
            raise ValueError("response feedback must match guidance feedback")
        if self.guidance.generated_at != self.generated_at:
            raise ValueError("response clock must match guidance clock")
        if self.strategy_history.generated_at > self.generated_at:
            raise ValueError("response clock cannot precede strategy history")
        if self.strategy_feedback.generated_at != self.generated_at:
            raise ValueError("feedback clock must match response clock")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        if self.schema_version != "1.0":
            raise ValueError("unsupported schema_version")

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-compatible response dictionary for a transport adapter."""
        history_payload = to_json_value(self.strategy_history)
        # These are stable read-model aggregates implemented as domain properties,
        # so expose them explicitly instead of assuming they are dataclass fields.
        history_payload["summary"] = {
            "audit_count": self.strategy_history.audit_count,
            "decision_count": self.strategy_history.decision_count,
            "adapted_task_count": self.strategy_history.adapted_task_count,
            "evidence_limited_count": self.strategy_history.evidence_limited_count,
            "scope_count": len(self.strategy_history.scopes),
        }
        return {
            "schema_version": self.schema_version,
            "learner_id": self.learner_id,
            "generated_at": self.generated_at.isoformat(),
            "guidance": to_json_value(self.guidance),
            "strategy_history": history_payload,
            "strategy_feedback": to_json_value(self.strategy_feedback),
        }


class PreparationGuidanceAPIService:
    """Application boundary joining durable strategy history with preparation guidance.

    A future HTTP route can call build_response() and return to_payload(). This
    layer intentionally does not own HTTP status codes, auth middleware, or routing.
    """

    def __init__(
        self,
        *,
        strategy_history_service: AdaptiveStudyStrategyHistoryService,
        guidance_service: PreparationGuidanceService | None = None,
    ) -> None:
        self.strategy_history_service = strategy_history_service
        self.guidance_service = guidance_service or PreparationGuidanceService()

    def build_response(
        self,
        learner_id: str,
        *,
        test_id: str,
        title: str,
        question_count: int,
        duration_seconds: int,
        history: LearnerLearningHistory,
        question_history: LearnerQuestionHistory,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        history_limit: int = 50,
        current_analysis: TestAnalysis | None = None,
        mode: PersonalizedPreparationMode = PersonalizedPreparationMode.ADAPTIVE,
        scoring: ScoringPolicy | None = None,
        shuffle_questions: bool = False,
        shuffle_seed: int | None = None,
        exclude_question_ids: Sequence[str] = (),
        as_of: datetime | None = None,
        generated_at: datetime | None = None,
    ) -> PreparationGuidanceAPIResponse:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        report_time = generated_at or datetime.now(timezone.utc)
        if report_time.tzinfo is None or report_time.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")

        # One fixed clock keeps the strategy history, feedback, guidance and API
        # envelope internally consistent for deterministic tests and client display.
        strategy_history = self.strategy_history_service.build_report(
            learner_id,
            limit=history_limit,
            generated_at=report_time,
        )
        guidance = self.guidance_service.build_guidance(
            learner_id,
            test_id=test_id,
            title=title,
            question_count=question_count,
            duration_seconds=duration_seconds,
            history=history,
            question_history=question_history,
            candidates=candidates,
            questions=questions,
            current_analysis=current_analysis,
            mode=mode,
            scoring=scoring,
            shuffle_questions=shuffle_questions,
            shuffle_seed=shuffle_seed,
            exclude_question_ids=exclude_question_ids,
            as_of=as_of,
            strategy_history_report=strategy_history,
            generated_at=report_time,
        )
        feedback = guidance.strategy_feedback_report
        if feedback is None:
            raise RuntimeError("strategy feedback was not produced for supplied history")
        return PreparationGuidanceAPIResponse(
            learner_id=learner_id,
            guidance=guidance,
            strategy_history=strategy_history,
            strategy_feedback=feedback,
            generated_at=report_time,
        )


__all__ = [
    "PreparationGuidanceAPIResponse",
    "PreparationGuidanceAPIService",
    "to_json_value",
]
