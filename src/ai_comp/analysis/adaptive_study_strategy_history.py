from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from statistics import fmean

from ai_comp.domain.adaptive_study_strategy import StudyStrategyAction
from ai_comp.domain.adaptive_study_strategy_audit import (
    AdaptiveStudyStrategyAudit,
    AdaptiveStudyStrategyAuditRepository,
)
from ai_comp.domain.adaptive_study_strategy_history import (
    AdaptiveStudyStrategyHistoryReport,
    ConceptStrategyHistory,
    StrategyAuditHistoryEntry,
    StrategyHistoryScopeKind,
)
from ai_comp.domain.learning_history import LearningTrend


class AdaptiveStudyStrategyHistoryService:
    """Builds descriptive learner-scoped comparisons from durable audit snapshots."""

    def __init__(self, repository: AdaptiveStudyStrategyAuditRepository) -> None:
        self.repository = repository

    def build_report(
        self,
        learner_id: str,
        *,
        limit: int = 50,
        generated_at: datetime | None = None,
    ) -> AdaptiveStudyStrategyHistoryReport:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        report_time = generated_at or datetime.now(timezone.utc)
        if report_time.tzinfo is None or report_time.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")

        audits = self.repository.list_for_learner(learner_id, limit=limit)
        if any(audit.learner_id != learner_id for audit in audits):
            raise ValueError("audit repository returned another learner's history")
        audit_ids = tuple(audit.audit_id for audit in audits)
        if len(audit_ids) != len(set(audit_ids)):
            raise ValueError("audit repository returned duplicate IDs")
        if any(audit.recorded_at > report_time for audit in audits):
            raise ValueError("generated_at cannot precede stored audit history")

        ordered = tuple(sorted(audits, key=lambda row: (row.recorded_at, row.audit_id), reverse=True))
        entries = tuple(self._entry(audit) for audit in ordered)
        scopes = self._scope_history(ordered)
        return AdaptiveStudyStrategyHistoryReport(
            learner_id=learner_id,
            entries=entries,
            scopes=scopes,
            generated_at=report_time,
        )

    @staticmethod
    def _entry(audit: AdaptiveStudyStrategyAudit) -> StrategyAuditHistoryEntry:
        adjustments = audit.strategy_report.adjustments
        baseline = [item.baseline_accuracy_percentage for item in adjustments if item.baseline_accuracy_percentage is not None]
        follow_up = [item.follow_up_accuracy_percentage for item in adjustments if item.follow_up_accuracy_percentage is not None]
        deltas = [item.delta_percentage_points for item in adjustments if item.delta_percentage_points is not None]
        evidence_limited = sum(item.action is StudyStrategyAction.COLLECT_MORE_EVIDENCE for item in adjustments)
        return StrategyAuditHistoryEntry(
            audit_id=audit.audit_id,
            assessment_session_id=audit.assessment_session_id,
            source_schedule_id=audit.source_schedule_id,
            resulting_schedule_id=audit.resulting_schedule_id,
            recorded_at=audit.recorded_at,
            adjustment_count=len(adjustments),
            adapted_task_count=len(adjustments) - evidence_limited,
            evidence_limited_count=evidence_limited,
            baseline_accuracy_percentage=fmean(baseline) if baseline else None,
            follow_up_accuracy_percentage=fmean(follow_up) if follow_up else None,
            delta_percentage_points=fmean(deltas) if deltas else None,
            actions=tuple(item.action for item in adjustments),
            trends=tuple(item.source_trend for item in adjustments),
        )

    @staticmethod
    def _scope_history(
        audits: tuple[AdaptiveStudyStrategyAudit, ...],
    ) -> tuple[ConceptStrategyHistory, ...]:
        grouped: dict[tuple[StrategyHistoryScopeKind, tuple[str, ...], object], list[dict[str, object]]] = defaultdict(list)
        for audit in audits:
            source_tasks = {
                task.task_id: task
                for day in audit.source_schedule.days
                for task in day.tasks
            }
            result_tasks = tuple(
                task for day in audit.resulting_schedule.days for task in day.tasks
            )
            for adjustment in audit.strategy_report.adjustments:
                source_task = source_tasks[adjustment.task_id]
                concept_ids = tuple(sorted(source_task.concept_ids))
                question_ids = tuple(sorted(source_task.question_ids))
                if concept_ids:
                    scope_kind = StrategyHistoryScopeKind.CONCEPTS
                    scope_ids = concept_ids
                elif question_ids:
                    scope_kind = StrategyHistoryScopeKind.QUESTIONS
                    scope_ids = question_ids
                else:
                    continue

                overlapping = [
                    task for task in result_tasks
                    if set(concept_ids).intersection(task.concept_ids)
                    or set(question_ids).intersection(task.question_ids)
                ]
                applied_priority = (
                    max(task.priority_score for task in overlapping)
                    if overlapping else None
                )
                grouped[(scope_kind, scope_ids, adjustment.task_kind)].append({
                    "audit_id": audit.audit_id,
                    "assessment_session_id": audit.assessment_session_id,
                    "recorded_at": audit.recorded_at,
                    "action": adjustment.action,
                    "trend": adjustment.source_trend,
                    "baseline": adjustment.baseline_accuracy_percentage,
                    "follow_up": adjustment.follow_up_accuracy_percentage,
                    "delta": adjustment.delta_percentage_points,
                    "recommended_priority_delta": adjustment.priority_delta,
                    "applied_priority_delta": (
                        applied_priority - adjustment.current_priority_score
                        if applied_priority is not None else None
                    ),
                })

        result = []
        for (scope_kind, scope_ids, task_kind), rows in grouped.items():
            rows.sort(key=lambda row: (row["recorded_at"], row["audit_id"]), reverse=True)
            trends = [row["trend"] for row in rows]
            baseline = [row["baseline"] for row in rows if row["baseline"] is not None]
            follow_up = [row["follow_up"] for row in rows if row["follow_up"] is not None]
            delta = [row["delta"] for row in rows if row["delta"] is not None]
            recommended = [row["recommended_priority_delta"] for row in rows]
            applied = [row["applied_priority_delta"] for row in rows if row["applied_priority_delta"] is not None]
            result.append(ConceptStrategyHistory(
                scope_kind=scope_kind,
                scope_ids=scope_ids,
                task_kind=task_kind,
                decision_count=len(rows),
                assessment_count=len({row["assessment_session_id"] for row in rows}),
                improving_count=sum(trend is LearningTrend.IMPROVING for trend in trends),
                declining_count=sum(trend is LearningTrend.DECLINING for trend in trends),
                stable_count=sum(trend is LearningTrend.STABLE for trend in trends),
                insufficient_data_count=sum(trend is LearningTrend.INSUFFICIENT_DATA for trend in trends),
                mean_baseline_accuracy_percentage=fmean(baseline) if baseline else None,
                mean_follow_up_accuracy_percentage=fmean(follow_up) if follow_up else None,
                mean_delta_percentage_points=fmean(delta) if delta else None,
                mean_recommended_priority_delta=fmean(recommended) if recommended else None,
                mean_applied_priority_delta=fmean(applied) if applied else None,
                latest_action=rows[0]["action"],
                latest_recorded_at=rows[0]["recorded_at"],
            ))
        return tuple(sorted(
            result,
            key=lambda item: (
                -item.decision_count,
                item.scope_kind.value,
                item.scope_ids,
                item.task_kind.value,
            ),
        ))


__all__ = ["AdaptiveStudyStrategyHistoryService"]
