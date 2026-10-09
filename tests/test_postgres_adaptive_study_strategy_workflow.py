from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from ai_comp.analysis.adaptive_study_strategy_audit import AdaptiveStudyStrategyAuditService
from ai_comp.analysis.adaptive_study_strategy_history import AdaptiveStudyStrategyHistoryService
from ai_comp.analysis.adaptive_study_strategy_workflow import AdaptiveStudyStrategyWorkflow
from ai_comp.analysis.study_schedule_execution import StudyScheduleExecutionService
from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner
from ai_comp.database.postgres_adaptive_study_strategy_audit import PostgresAdaptiveStudyStrategyAuditRepository
from ai_comp.database.postgres_study_schedule_execution import PostgresStudyTaskExecutionRepository
from ai_comp.domain.adaptive_study_strategy import AdaptiveStudyStrategyReport, StudyStrategyAction, StudyTaskStrategyAdjustment
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_outcome_feedback import OutcomeEvidenceKind
from ai_comp.domain.study_schedule import ScheduledStudyTask, StudyDayPlan, StudySchedule, StudyTaskKind
from ai_comp.domain.study_schedule_execution import StudyTaskExecution, StudyTaskExecutionStatus


pytestmark = pytest.mark.integration
NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


def test_postgres_workflow_applies_strategy_persists_audit_and_retrieves_history():
    dsn = os.getenv("AI_COMP_DATABASE_URL", "").strip()
    if not dsn:
        pytest.skip("AI_COMP_DATABASE_URL is not configured")

    with connect_postgres(dsn) as connection:
        migrations = Path(__file__).resolve().parents[1] / "database" / "migrations"
        MigrationRunner(migrations).apply(connection)
        execution_repository = PostgresStudyTaskExecutionRepository(connection)
        audit_repository = PostgresAdaptiveStudyStrategyAuditRepository(connection)
        schedule_service = StudyScheduleExecutionService(execution_repository)
        audit_service = AdaptiveStudyStrategyAuditService(audit_repository)
        workflow = AdaptiveStudyStrategyWorkflow(schedule_service, audit_service)

        learner_id = f"phase626-{uuid4()}"
        yesterday = TODAY - timedelta(days=1)
        source_task = ScheduledStudyTask(
            task_id="phase626-source",
            kind=StudyTaskKind.STUDY_WEAK_TOPIC,
            scheduled_date=yesterday,
            title="Science source task",
            estimated_minutes=20,
            priority_score=0.60,
            reason="Existing learner topic evidence.",
            concept_ids=("science",),
        )
        next_task = ScheduledStudyTask(
            task_id="phase626-next",
            kind=StudyTaskKind.STUDY_WEAK_TOPIC,
            scheduled_date=TODAY + timedelta(days=1),
            title="Science next task",
            estimated_minutes=20,
            priority_score=0.40,
            reason="Pending science practice.",
            concept_ids=("science",),
        )
        schedule = StudySchedule(
            learner_id=learner_id,
            start_date=yesterday,
            end_date=TODAY + timedelta(days=1),
            exam_date=None,
            days=(
                StudyDayPlan(yesterday, 30, (source_task,)),
                StudyDayPlan(TODAY, 30, ()),
                StudyDayPlan(TODAY + timedelta(days=1), 30, (next_task,)),
            ),
            unscheduled_work=(),
            generated_at=NOW - timedelta(days=2),
        )
        schedule_service.record_execution(
            schedule,
            StudyTaskExecution(
                event_id=f"phase626-completed-{uuid4()}",
                schedule_id=schedule.schedule_id,
                learner_id=learner_id,
                task_id=source_task.task_id,
                status=StudyTaskExecutionStatus.COMPLETED,
                occurred_at=NOW - timedelta(hours=3),
                actual_minutes=20,
            ),
        )
        adjustment = StudyTaskStrategyAdjustment(
            task_id=source_task.task_id,
            task_kind=source_task.kind,
            execution_status=StudyTaskExecutionStatus.COMPLETED,
            evidence_kind=OutcomeEvidenceKind.CONCEPT_OVERLAP,
            source_trend=LearningTrend.DECLINING,
            action=StudyStrategyAction.REINFORCE_WEAK_AREA,
            current_priority_score=0.60,
            recommended_priority_score=0.80,
            suggested_revision_interval_days=3,
            baseline_attempted_count=10,
            follow_up_attempted_count=10,
            baseline_accuracy_percentage=70.0,
            follow_up_accuracy_percentage=60.0,
            delta_percentage_points=-10.0,
            reason="Linked score declined; reinforce science.",
        )
        strategy_report = AdaptiveStudyStrategyReport(
            learner_id=learner_id,
            schedule_id=schedule.schedule_id,
            assessment_session_id=f"phase626-assessment-{uuid4()}",
            assessed_at=NOW - timedelta(hours=2),
            adjustments=(adjustment,),
            generated_at=NOW - timedelta(hours=1),
        )

        result = workflow.apply_and_record(
            f"phase626-audit-{uuid4()}",
            source_schedule=schedule,
            strategy_report=strategy_report,
            daily_minutes=30,
            start_date=TODAY,
            as_of=NOW,
        )
        assert result.schedule == result.audit.resulting_schedule
        planned = tuple(task for day in result.schedule.days for task in day.tasks)
        assert len(planned) == 1
        assert planned[0].priority_score == pytest.approx(0.80)
        assert planned[0].scheduled_date == TODAY + timedelta(days=3)

        persisted = audit_service.get_audit(result.audit.audit_id)
        assert persisted == result.audit
        history = AdaptiveStudyStrategyHistoryService(audit_repository).build_report(
            learner_id, generated_at=NOW + timedelta(seconds=1)
        )
        assert history.audit_count == 1
        assert history.decision_count == 1
        assert history.scopes[0].scope_ids == ("science",)
        assert history.scopes[0].declining_count == 1
        assert history.scopes[0].mean_applied_priority_delta == pytest.approx(0.20)
