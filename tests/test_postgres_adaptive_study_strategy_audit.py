from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from ai_comp.analysis.adaptive_study_strategy_audit import AdaptiveStudyStrategyAuditService
from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner
from ai_comp.database.postgres_adaptive_study_strategy_audit import PostgresAdaptiveStudyStrategyAuditRepository
from ai_comp.domain.adaptive_study_strategy import AdaptiveStudyStrategyReport, StudyStrategyAction, StudyTaskStrategyAdjustment
from ai_comp.domain.adaptive_study_strategy_audit import AdaptiveStudyStrategyAuditConflictError
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_outcome_feedback import OutcomeEvidenceKind
from ai_comp.domain.study_schedule import ScheduledStudyTask, StudyDayPlan, StudySchedule, StudyTaskKind
from ai_comp.domain.study_schedule_execution import StudyTaskExecutionStatus


pytestmark = pytest.mark.integration
NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


def test_postgres_strategy_audit_round_trip_and_idempotent_conflict():
    dsn = os.getenv("AI_COMP_DATABASE_URL", "").strip()
    if not dsn:
        pytest.skip("AI_COMP_DATABASE_URL is not configured")

    with connect_postgres(dsn) as connection:
        migration_dir = Path(__file__).resolve().parents[1] / "database" / "migrations"
        MigrationRunner(migration_dir).apply(connection)
        service = AdaptiveStudyStrategyAuditService(
            PostgresAdaptiveStudyStrategyAuditRepository(connection)
        )

        task_date = NOW.date() - timedelta(days=1)
        source_task = ScheduledStudyTask(
            task_id="audit-source-task",
            kind=StudyTaskKind.STUDY_WEAK_TOPIC,
            scheduled_date=task_date,
            title="Science revision",
            estimated_minutes=20,
            priority_score=0.60,
            reason="Prior learner-performance evidence.",
            concept_ids=("science",),
        )
        source = StudySchedule(
            learner_id=f"phase625-{uuid4()}",
            start_date=task_date,
            end_date=task_date,
            exam_date=None,
            days=(StudyDayPlan(task_date, 30, (source_task,)),),
            unscheduled_work=(),
            generated_at=NOW - timedelta(days=2),
        )
        adjustment = StudyTaskStrategyAdjustment(
            task_id=source_task.task_id,
            task_kind=source_task.kind,
            execution_status=StudyTaskExecutionStatus.COMPLETED,
            evidence_kind=OutcomeEvidenceKind.CONCEPT_OVERLAP,
            source_trend=LearningTrend.DECLINING,
            action=StudyStrategyAction.REINFORCE_WEAK_AREA,
            current_priority_score=0.60,
            recommended_priority_score=0.75,
            suggested_revision_interval_days=1,
            baseline_attempted_count=10,
            follow_up_attempted_count=10,
            baseline_accuracy_percentage=70.0,
            follow_up_accuracy_percentage=60.0,
            delta_percentage_points=-10.0,
            reason="Linked accuracy declined.",
        )
        report = AdaptiveStudyStrategyReport(
            learner_id=source.learner_id,
            schedule_id=source.schedule_id,
            assessment_session_id="audit-assessment-1",
            assessed_at=NOW - timedelta(hours=2),
            adjustments=(adjustment,),
            generated_at=NOW - timedelta(hours=1),
        )
        result_task = ScheduledStudyTask(
            task_id="audit-next-task",
            kind=StudyTaskKind.STUDY_WEAK_TOPIC,
            scheduled_date=NOW.date(),
            title="Science reinforcement",
            estimated_minutes=20,
            priority_score=0.75,
            reason="Adaptive strategy applied.",
            concept_ids=("science",),
        )
        result = StudySchedule(
            learner_id=source.learner_id,
            start_date=NOW.date(),
            end_date=NOW.date(),
            exam_date=None,
            days=(StudyDayPlan(NOW.date(), 30, (result_task,)),),
            unscheduled_work=(),
            generated_at=NOW,
        )
        audit_id = f"strategy-audit-{uuid4()}"
        first = service.record_applied_strategy(
            audit_id, source_schedule=source, strategy_report=report, resulting_schedule=result
        )
        second = service.record_applied_strategy(
            audit_id, source_schedule=source, strategy_report=report, resulting_schedule=result
        )
        assert first == second
        assert service.get_audit(audit_id) == first
        assert service.list_for_learner(source.learner_id) == (first,)

        conflicting_task = ScheduledStudyTask(
            task_id="audit-next-task",
            kind=StudyTaskKind.STUDY_WEAK_TOPIC,
            scheduled_date=NOW.date(),
            title="Science reinforcement",
            estimated_minutes=20,
            priority_score=0.55,
            reason="Conflicting retry payload.",
            concept_ids=("science",),
        )
        conflicting_result = StudySchedule(
            learner_id=source.learner_id,
            start_date=NOW.date(),
            end_date=NOW.date(),
            exam_date=None,
            days=(StudyDayPlan(NOW.date(), 30, (conflicting_task,)),),
            unscheduled_work=(),
            generated_at=NOW,
        )
        with pytest.raises(AdaptiveStudyStrategyAuditConflictError, match="different evidence"):
            service.record_applied_strategy(
                audit_id, source_schedule=source, strategy_report=report,
                resulting_schedule=conflicting_result,
            )
