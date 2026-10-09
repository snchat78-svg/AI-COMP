from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai_comp.analysis.adaptive_study_strategy_history import AdaptiveStudyStrategyHistoryService
from ai_comp.domain.adaptive_study_strategy import AdaptiveStudyStrategyReport, StudyStrategyAction, StudyTaskStrategyAdjustment
from ai_comp.domain.adaptive_study_strategy_audit import AdaptiveStudyStrategyAudit
from ai_comp.domain.adaptive_study_strategy_history import StrategyHistoryScopeKind
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_outcome_feedback import OutcomeEvidenceKind
from ai_comp.domain.study_schedule import ScheduledStudyTask, StudyDayPlan, StudySchedule, StudyTaskKind
from ai_comp.domain.study_schedule_execution import StudyTaskExecutionStatus


NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


class InMemoryAuditRepository:
    def __init__(self, audits=()):
        self.audits = {audit.audit_id: audit for audit in audits}

    def get_audit(self, audit_id):
        return self.audits.get(audit_id)

    def save_audit(self, audit):
        self.audits[audit.audit_id] = audit
        return audit

    def list_for_learner(self, learner_id, *, limit=50):
        return tuple(sorted(
            (item for item in self.audits.values() if item.learner_id == learner_id),
            key=lambda item: (item.recorded_at, item.audit_id),
            reverse=True,
        )[:limit])


def make_audit(index: int, *, trend: LearningTrend, base: float, follow: float, delta: float, priority: float):
    source_time = NOW - timedelta(days=10)
    source_day = NOW.date() - timedelta(days=1)
    source_task = ScheduledStudyTask(
        task_id=f"task-source-{index}",
        kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        scheduled_date=source_day,
        title="Study science",
        estimated_minutes=20,
        priority_score=0.60,
        reason="Source topic score.",
        concept_ids=("science",),
    )
    source = StudySchedule(
        learner_id="learner-1",
        start_date=source_day,
        end_date=source_day,
        exam_date=None,
        days=(StudyDayPlan(source_day, 30, (source_task,)),),
        unscheduled_work=(),
        generated_at=source_time,
    )
    if trend is LearningTrend.DECLINING:
        action, interval = StudyStrategyAction.REINFORCE_WEAK_AREA, 1
    elif trend is LearningTrend.IMPROVING:
        action, interval = StudyStrategyAction.CONTINUE_TARGETED_PRACTICE, 5
    else:
        action, interval = StudyStrategyAction.MAINTAIN_AND_RETEST, 3
    adjustment = StudyTaskStrategyAdjustment(
        task_id=source_task.task_id,
        task_kind=source_task.kind,
        execution_status=StudyTaskExecutionStatus.COMPLETED,
        evidence_kind=OutcomeEvidenceKind.CONCEPT_OVERLAP,
        source_trend=trend,
        action=action,
        current_priority_score=0.60,
        recommended_priority_score=priority,
        suggested_revision_interval_days=interval,
        baseline_attempted_count=10,
        follow_up_attempted_count=10,
        baseline_accuracy_percentage=base,
        follow_up_accuracy_percentage=follow,
        delta_percentage_points=delta,
        reason="Evidence-based strategy decision.",
    )
    assessed = NOW + timedelta(days=index) - timedelta(hours=2)
    report = AdaptiveStudyStrategyReport(
        learner_id="learner-1",
        schedule_id=source.schedule_id,
        assessment_session_id=f"assessment-{index}",
        assessed_at=assessed,
        adjustments=(adjustment,),
        generated_at=assessed + timedelta(minutes=10),
    )
    result_day = NOW.date() + timedelta(days=index)
    result_task = ScheduledStudyTask(
        task_id=f"result-task-{index}",
        kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        scheduled_date=result_day,
        title="Adaptive science work",
        estimated_minutes=20,
        priority_score=priority,
        reason="Applied strategy.",
        concept_ids=("science",),
    )
    result = StudySchedule(
        learner_id="learner-1",
        start_date=result_day,
        end_date=result_day,
        exam_date=None,
        days=(StudyDayPlan(result_day, 30, (result_task,)),),
        unscheduled_work=(),
        generated_at=NOW + timedelta(days=index),
    )
    return AdaptiveStudyStrategyAudit(
        audit_id=f"audit-{index}",
        source_schedule=source,
        strategy_report=report,
        resulting_schedule=result,
        recorded_at=result.generated_at,
    )


def test_history_compares_topic_strategy_trends_across_prior_audits():
    audits = (
        make_audit(0, trend=LearningTrend.DECLINING, base=70, follow=60, delta=-10, priority=0.75),
        make_audit(1, trend=LearningTrend.IMPROVING, base=60, follow=80, delta=20, priority=0.60),
        make_audit(2, trend=LearningTrend.STABLE, base=60, follow=62, delta=2, priority=0.65),
    )
    service = AdaptiveStudyStrategyHistoryService(InMemoryAuditRepository(audits))
    report = service.build_report("learner-1", generated_at=NOW + timedelta(days=3))

    assert report.audit_count == 3
    assert report.decision_count == 3
    assert report.adapted_task_count == 3
    assert report.evidence_limited_count == 0
    assert report.entries[0].audit_id == "audit-2"
    assert report.entries[0].delta_percentage_points == pytest.approx(2.0)

    assert len(report.scopes) == 1
    scope = report.scopes[0]
    assert scope.scope_kind is StrategyHistoryScopeKind.CONCEPTS
    assert scope.scope_ids == ("science",)
    assert scope.decision_count == 3
    assert scope.assessment_count == 3
    assert (scope.improving_count, scope.declining_count, scope.stable_count) == (1, 1, 1)
    assert scope.mean_baseline_accuracy_percentage == pytest.approx(190 / 3)
    assert scope.mean_follow_up_accuracy_percentage == pytest.approx(202 / 3)
    assert scope.mean_delta_percentage_points == pytest.approx(4.0)
    assert scope.mean_recommended_priority_delta == pytest.approx(0.20 / 3)
    assert scope.mean_applied_priority_delta == pytest.approx(0.20 / 3)


def test_history_is_learner_scoped_bounded_and_requires_aware_clock():
    repository = InMemoryAuditRepository((
        make_audit(0, trend=LearningTrend.DECLINING, base=70, follow=60, delta=-10, priority=0.75),
    ))
    service = AdaptiveStudyStrategyHistoryService(repository)

    with pytest.raises(ValueError, match="limit"):
        service.build_report("learner-1", limit=0, generated_at=NOW + timedelta(days=1))
    with pytest.raises(ValueError, match="timezone-aware"):
        service.build_report("learner-1", generated_at=datetime(2026, 10, 9))
    with pytest.raises(ValueError, match="cannot precede"):
        service.build_report("learner-1", generated_at=NOW - timedelta(days=1))


def test_empty_history_returns_empty_report():
    report = AdaptiveStudyStrategyHistoryService(InMemoryAuditRepository()).build_report(
        "learner-1", generated_at=NOW
    )
    assert report.audit_count == report.decision_count == 0
    assert report.entries == ()
    assert report.scopes == ()
