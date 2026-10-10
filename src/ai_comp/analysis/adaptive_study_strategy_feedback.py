from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ai_comp.domain.adaptive_study_strategy import StudyStrategyAction
from ai_comp.domain.adaptive_study_strategy_feedback import (
    AdaptiveStudyStrategyFeedbackReport,
    StrategyFeedbackKind,
    StudyStrategyFeedbackFinding,
)
from ai_comp.domain.adaptive_study_strategy_history import AdaptiveStudyStrategyHistoryReport


@dataclass(frozen=True)
class AdaptiveStudyStrategyFeedbackPolicy:
    """Conservative thresholds for flagging repeated declines after reinforcement."""

    minimum_assessment_count: int = 3
    minimum_decision_count: int = 3
    minimum_declining_count: int = 2
    maximum_mean_delta_percentage_points: float = -5.0
    priority_score: float = 0.88

    def __post_init__(self) -> None:
        for name in (
            "minimum_assessment_count",
            "minimum_decision_count",
            "minimum_declining_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if not -100.0 <= self.maximum_mean_delta_percentage_points < 0.0:
            raise ValueError("maximum mean delta must be between -100 and 0")
        if not 0.0 <= self.priority_score <= 1.0:
            raise ValueError("priority_score must be between 0 and 1")


class AdaptiveStudyStrategyFeedbackService:
    """Finds conservative feedback signals from immutable, learner-scoped history.

    A signal suggests trying a different study approach; it does not claim that
    an earlier strategy caused the score change. Insufficient or mixed evidence
    deliberately produces no strategy-change finding.
    """

    def __init__(
        self,
        *,
        policy: AdaptiveStudyStrategyFeedbackPolicy | None = None,
    ) -> None:
        self.policy = policy or AdaptiveStudyStrategyFeedbackPolicy()

    def build_report(
        self,
        history_report: AdaptiveStudyStrategyHistoryReport,
        *,
        generated_at: datetime | None = None,
    ) -> AdaptiveStudyStrategyFeedbackReport:
        report_time = generated_at or datetime.now(timezone.utc)
        if report_time.tzinfo is None or report_time.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        if report_time < history_report.generated_at:
            raise ValueError("generated_at cannot precede strategy history report")

        findings = []
        for scope in history_report.scopes:
            delta = scope.mean_delta_percentage_points
            policy = self.policy
            enough_observations = (
                scope.assessment_count >= policy.minimum_assessment_count
                and scope.decision_count >= policy.minimum_decision_count
            )
            repeated_decline = (
                scope.declining_count >= policy.minimum_declining_count
                and scope.declining_count > scope.improving_count
                and delta is not None
                and delta <= policy.maximum_mean_delta_percentage_points
            )
            latest_was_reinforcement = (
                scope.latest_action is StudyStrategyAction.REINFORCE_WEAK_AREA
            )
            if not (enough_observations and repeated_decline and latest_was_reinforcement):
                continue

            scope_label = (
                "concept(s)" if scope.scope_kind.value == "CONCEPTS" else "question(s)"
            )
            findings.append(StudyStrategyFeedbackFinding(
                scope_kind=scope.scope_kind,
                scope_ids=scope.scope_ids,
                task_kind=scope.task_kind,
                decision_count=scope.decision_count,
                assessment_count=scope.assessment_count,
                declining_count=scope.declining_count,
                improving_count=scope.improving_count,
                mean_delta_percentage_points=delta,
                latest_action=scope.latest_action,
                kind=StrategyFeedbackKind.CHANGE_APPROACH,
                priority_score=policy.priority_score,
                reason=(
                    f"Across {scope.assessment_count} distinct assessments for "
                    f"{scope_label} {', '.join(scope.scope_ids)}, linked accuracy "
                    f"declined in {scope.declining_count} decision(s) and changed "
                    f"by {delta:.2f} percentage points on average. The latest "
                    "recorded action was reinforcement. Consider changing the "
                    "study method and checking results on comparable tests; this "
                    "pattern is observational and does not prove the strategy "
                    "caused the decline."
                ),
            ))

        findings.sort(key=lambda item: (
            -item.priority_score,
            item.scope_kind.value,
            item.scope_ids,
            item.task_kind.value,
        ))
        return AdaptiveStudyStrategyFeedbackReport(
            learner_id=history_report.learner_id,
            source_audit_count=history_report.audit_count,
            evaluated_scope_count=len(history_report.scopes),
            not_actionable_scope_count=len(history_report.scopes) - len(findings),
            findings=tuple(findings),
            generated_at=report_time,
        )


__all__ = [
    "AdaptiveStudyStrategyFeedbackPolicy",
    "AdaptiveStudyStrategyFeedbackService",
]
