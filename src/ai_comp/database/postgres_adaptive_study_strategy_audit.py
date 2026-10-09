from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.adaptive_study_strategy import (
    AdaptiveStudyStrategyReport,
    StudyStrategyAction,
    StudyTaskStrategyAdjustment,
)
from ai_comp.domain.adaptive_study_strategy_audit import (
    AdaptiveStudyStrategyAudit,
    AdaptiveStudyStrategyAuditConflictError,
)
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_outcome_feedback import OutcomeEvidenceKind
from ai_comp.domain.study_schedule import (
    ScheduledStudyTask, StudyDayPlan, StudySchedule, StudyTaskKind,
    UnscheduledStudyWork,
)
from ai_comp.domain.study_schedule_execution import StudyTaskExecutionStatus


def _datetime(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("stored audit timestamp must be timezone-aware")
    return result


def _schedule_to_dict(schedule: StudySchedule) -> dict[str, Any]:
    return {
        "learner_id": schedule.learner_id,
        "start_date": schedule.start_date.isoformat(),
        "end_date": schedule.end_date.isoformat(),
        "exam_date": schedule.exam_date.isoformat() if schedule.exam_date else None,
        "generated_at": schedule.generated_at.isoformat(),
        "days": [
            {
                "study_date": day.study_date.isoformat(),
                "available_minutes": day.available_minutes,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "kind": task.kind.value,
                        "scheduled_date": task.scheduled_date.isoformat(),
                        "title": task.title,
                        "estimated_minutes": task.estimated_minutes,
                        "priority_score": task.priority_score,
                        "reason": task.reason,
                        "concept_ids": list(task.concept_ids),
                        "question_ids": list(task.question_ids),
                        "deadline_date": task.deadline_date.isoformat() if task.deadline_date else None,
                    }
                    for task in day.tasks
                ],
            }
            for day in schedule.days
        ],
        "unscheduled_work": [
            {
                "work_id": item.work_id,
                "kind": item.kind.value,
                "title": item.title,
                "remaining_minutes": item.remaining_minutes,
                "priority_score": item.priority_score,
                "reason": item.reason,
                "unscheduled_reason": item.unscheduled_reason,
                "concept_ids": list(item.concept_ids),
                "question_ids": list(item.question_ids),
                "deadline_date": item.deadline_date.isoformat() if item.deadline_date else None,
                "available_from_date": item.available_from_date.isoformat() if item.available_from_date else None,
            }
            for item in schedule.unscheduled_work
        ],
    }


def _schedule_from_dict(payload: Mapping[str, Any]) -> StudySchedule:
    days = tuple(
        StudyDayPlan(
            study_date=date.fromisoformat(day["study_date"]),
            available_minutes=int(day["available_minutes"]),
            tasks=tuple(
                ScheduledStudyTask(
                    task_id=task["task_id"],
                    kind=StudyTaskKind(task["kind"]),
                    scheduled_date=date.fromisoformat(task["scheduled_date"]),
                    title=task["title"],
                    estimated_minutes=int(task["estimated_minutes"]),
                    priority_score=float(task["priority_score"]),
                    reason=task["reason"],
                    concept_ids=tuple(task["concept_ids"]),
                    question_ids=tuple(task["question_ids"]),
                    deadline_date=date.fromisoformat(task["deadline_date"]) if task["deadline_date"] else None,
                )
                for task in day["tasks"]
            ),
        )
        for day in payload["days"]
    )
    unallocated = tuple(
        UnscheduledStudyWork(
            work_id=item["work_id"],
            kind=StudyTaskKind(item["kind"]),
            title=item["title"],
            remaining_minutes=int(item["remaining_minutes"]),
            priority_score=float(item["priority_score"]),
            reason=item["reason"],
            unscheduled_reason=item["unscheduled_reason"],
            concept_ids=tuple(item["concept_ids"]),
            question_ids=tuple(item["question_ids"]),
            deadline_date=date.fromisoformat(item["deadline_date"]) if item["deadline_date"] else None,
            available_from_date=date.fromisoformat(item["available_from_date"]) if item["available_from_date"] else None,
        )
        for item in payload["unscheduled_work"]
    )
    return StudySchedule(
        learner_id=payload["learner_id"],
        start_date=date.fromisoformat(payload["start_date"]),
        end_date=date.fromisoformat(payload["end_date"]),
        exam_date=date.fromisoformat(payload["exam_date"]) if payload["exam_date"] else None,
        days=days,
        unscheduled_work=unallocated,
        generated_at=_datetime(payload["generated_at"]),
    )


def _report_to_dict(report: AdaptiveStudyStrategyReport) -> dict[str, Any]:
    return {
        "learner_id": report.learner_id,
        "schedule_id": report.schedule_id,
        "assessment_session_id": report.assessment_session_id,
        "assessed_at": report.assessed_at.isoformat(),
        "generated_at": report.generated_at.isoformat(),
        "adjustments": [
            {
                "task_id": item.task_id,
                "task_kind": item.task_kind.value,
                "execution_status": item.execution_status.value,
                "evidence_kind": item.evidence_kind.value,
                "source_trend": item.source_trend.value,
                "action": item.action.value,
                "current_priority_score": item.current_priority_score,
                "recommended_priority_score": item.recommended_priority_score,
                "suggested_revision_interval_days": item.suggested_revision_interval_days,
                "baseline_attempted_count": item.baseline_attempted_count,
                "follow_up_attempted_count": item.follow_up_attempted_count,
                "baseline_accuracy_percentage": item.baseline_accuracy_percentage,
                "follow_up_accuracy_percentage": item.follow_up_accuracy_percentage,
                "delta_percentage_points": item.delta_percentage_points,
                "reason": item.reason,
            }
            for item in report.adjustments
        ],
    }


def _report_from_dict(payload: Mapping[str, Any]) -> AdaptiveStudyStrategyReport:
    adjustments = tuple(
        StudyTaskStrategyAdjustment(
            task_id=item["task_id"],
            task_kind=StudyTaskKind(item["task_kind"]),
            execution_status=StudyTaskExecutionStatus(item["execution_status"]),
            evidence_kind=OutcomeEvidenceKind(item["evidence_kind"]),
            source_trend=LearningTrend(item["source_trend"]),
            action=StudyStrategyAction(item["action"]),
            current_priority_score=float(item["current_priority_score"]),
            recommended_priority_score=float(item["recommended_priority_score"]),
            suggested_revision_interval_days=None if item["suggested_revision_interval_days"] is None else int(item["suggested_revision_interval_days"]),
            baseline_attempted_count=int(item["baseline_attempted_count"]),
            follow_up_attempted_count=int(item["follow_up_attempted_count"]),
            baseline_accuracy_percentage=None if item["baseline_accuracy_percentage"] is None else float(item["baseline_accuracy_percentage"]),
            follow_up_accuracy_percentage=None if item["follow_up_accuracy_percentage"] is None else float(item["follow_up_accuracy_percentage"]),
            delta_percentage_points=None if item["delta_percentage_points"] is None else float(item["delta_percentage_points"]),
            reason=item["reason"],
        )
        for item in payload["adjustments"]
    )
    return AdaptiveStudyStrategyReport(
        learner_id=payload["learner_id"],
        schedule_id=payload["schedule_id"],
        assessment_session_id=payload["assessment_session_id"],
        assessed_at=_datetime(payload["assessed_at"]),
        adjustments=adjustments,
        generated_at=_datetime(payload["generated_at"]),
    )


def _json_object(value: object) -> Mapping[str, Any]:
    result = json.loads(value) if isinstance(value, str) else value
    if not isinstance(result, Mapping):
        raise ValueError("stored audit JSONB value must be an object")
    return result


class PostgresAdaptiveStudyStrategyAuditRepository:
    """Append-only audit snapshots with payload-hash and idempotency conflict checks."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save_audit(self, audit: AdaptiveStudyStrategyAudit) -> AdaptiveStudyStrategyAudit:
        payload = {
            "audit_id": audit.audit_id,
            "recorded_at": audit.recorded_at.isoformat(),
            "source_schedule": _schedule_to_dict(audit.source_schedule),
            "strategy_report": _report_to_dict(audit.strategy_report),
            "resulting_schedule": _schedule_to_dict(audit.resulting_schedule),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        payload_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        try:
            with self._connection.transaction():
                inserted = self._connection.execute(
                    """
                    INSERT INTO adaptive_study_strategy_audits (
                        audit_id, learner_id, source_schedule_id, resulting_schedule_id,
                        assessment_session_id, recorded_at, payload_sha256,
                        source_schedule_snapshot, strategy_report_snapshot,
                        resulting_schedule_snapshot
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb)
                    ON CONFLICT (audit_id) DO NOTHING
                    RETURNING audit_id
                    """,
                    (
                        audit.audit_id, audit.learner_id, audit.source_schedule_id,
                        audit.resulting_schedule_id, audit.assessment_session_id,
                        audit.recorded_at, payload_sha256,
                        json.dumps(payload["source_schedule"], ensure_ascii=False),
                        json.dumps(payload["strategy_report"], ensure_ascii=False),
                        json.dumps(payload["resulting_schedule"], ensure_ascii=False),
                    ),
                ).fetchone()
                if inserted is None:
                    existing = self.get_audit(audit.audit_id)
                    if existing != audit:
                        raise AdaptiveStudyStrategyAuditConflictError(
                            "audit ID already exists with different evidence"
                        )
                    return existing

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
                    source_concepts = set(source_task.concept_ids)
                    source_questions = set(source_task.question_ids)
                    applied_priorities = [
                        task.priority_score for task in result_tasks
                        if source_concepts.intersection(task.concept_ids)
                        or source_questions.intersection(task.question_ids)
                    ]
                    applied_priority = max(applied_priorities) if applied_priorities else None
                    self._connection.execute(
                        """
                        INSERT INTO adaptive_study_strategy_audit_adjustments (
                            audit_id, task_id, task_kind, execution_status, evidence_kind,
                            source_trend, action, previous_priority_score,
                            recommended_priority_score, applied_priority_score,
                            suggested_revision_interval_days, baseline_attempted_count,
                            follow_up_attempted_count, baseline_accuracy_percentage,
                            follow_up_accuracy_percentage, delta_percentage_points, reason
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            audit.audit_id, adjustment.task_id, adjustment.task_kind.value,
                            adjustment.execution_status.value, adjustment.evidence_kind.value,
                            adjustment.source_trend.value, adjustment.action.value,
                            adjustment.current_priority_score,
                            adjustment.recommended_priority_score, applied_priority,
                            adjustment.suggested_revision_interval_days,
                            adjustment.baseline_attempted_count, adjustment.follow_up_attempted_count,
                            adjustment.baseline_accuracy_percentage,
                            adjustment.follow_up_accuracy_percentage,
                            adjustment.delta_percentage_points, adjustment.reason,
                        ),
                    )
            return audit
        except AdaptiveStudyStrategyAuditConflictError:
            raise
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to persist adaptive strategy audit") from exc

    def get_audit(self, audit_id: str) -> AdaptiveStudyStrategyAudit | None:
        try:
            row = self._connection.execute(
                """
                SELECT audit_id, recorded_at, source_schedule_snapshot,
                       strategy_report_snapshot, resulting_schedule_snapshot
                FROM adaptive_study_strategy_audits
                WHERE audit_id = %s
                """,
                (audit_id,),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to read adaptive strategy audit") from exc
        return None if row is None else self._row(row)

    def list_for_learner(
        self,
        learner_id: str,
        *,
        limit: int = 50,
    ) -> tuple[AdaptiveStudyStrategyAudit, ...]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        try:
            rows = self._connection.execute(
                """
                SELECT audit_id, recorded_at, source_schedule_snapshot,
                       strategy_report_snapshot, resulting_schedule_snapshot
                FROM adaptive_study_strategy_audits
                WHERE learner_id = %s
                ORDER BY recorded_at DESC, audit_id DESC
                LIMIT %s
                """,
                (learner_id, limit),
            ).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list adaptive strategy audits") from exc
        return tuple(self._row(row) for row in rows)

    @staticmethod
    def _row(row: Sequence[object]) -> AdaptiveStudyStrategyAudit:
        return AdaptiveStudyStrategyAudit(
            audit_id=str(row[0]),
            recorded_at=row[1],
            source_schedule=_schedule_from_dict(_json_object(row[2])),
            strategy_report=_report_from_dict(_json_object(row[3])),
            resulting_schedule=_schedule_from_dict(_json_object(row[4])),
        )


__all__ = ["PostgresAdaptiveStudyStrategyAuditRepository"]
