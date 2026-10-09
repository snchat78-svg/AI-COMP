from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from ai_comp.analysis.adaptive_study_strategy import (
    AdaptiveStudyStrategyPolicy,
    AdaptiveStudyStrategyService,
)
from ai_comp.domain.adaptive_study_strategy import StudyStrategyAction
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_outcome_feedback import (
    OutcomeEvidenceKind,
    StudyOutcomeFeedbackReport,
    StudyTaskOutcome,
)
from ai_comp.domain.study_schedule import (
    ScheduledStudyTask,
    StudyDayPlan,
    StudySchedule,
    StudyTaskKind,
)
from ai_comp.domain.study_schedule_execution import StudyTaskExecutionStatus


NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


def make_schedule(priority: float = 0.70) -> StudySchedule:
    task = ScheduledStudyTask(
        task_id="task-science",
        kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        scheduled_date=TODAY - timedelta(days=1),
        title="Review science",
        estimated_minutes=25,
        priority_score=priority,
        reason="Prior learner-performance evidence.",
        concept_ids=("science",),
        question_ids=("q1", "q2"),
    )
    return StudySchedule(
        learner_id="learner-1",
        start_date=TODAY - timedelta(days=1),
        end_date=TODAY - timedelta(days=1),
        exam_date=None,
        days=(StudyDayPlan(TODAY - timedelta(days=1), 30, (task,)),),
        unscheduled_work=(),
        generated_at=NOW - timedelta(days=2),
    )


def make_outcome(
    *,
    trend: LearningTrend = LearningTrend.DECLINING,
    evidence: OutcomeEvidenceKind = OutcomeEvidenceKind.CONCEPT_OVERLAP,
    status: StudyTaskExecutionStatus = StudyTaskExecutionStatus.COMPLETED,
    baseline_count: int = 10,
    follow_up_count: int = 10,
    baseline_accuracy: float | None = 50.0,
    follow_up_accuracy: float | None = 40.0,
    delta: float | None = -10.0,
) -> StudyTaskOutcome:
    if trend is LearningTrend.INSUFFICIENT_DATA:
        delta = None
        baseline_count = min(baseline_count, 1)
        follow_up_count = min(follow_up_count, 1)
    elif trend is LearningTrend.IMPROVING:
        delta = delta if delta is not None else 10.0
    elif trend is LearningTrend.STABLE:
        delta = delta if delta is not None else 0.0

    question_count = max(1, follow_up_count)
    correct_count = round(
        question_count * (follow_up_accuracy or 0.0) / 100.0
    )
    attempted_count = question_count
    incorrect_count = attempted_count - correct_count
    return StudyTaskOutcome(
        task_id="task-science",
        task_kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        execution_event_ids=("event-1",),
        execution_status=status,
        evidence_kind=evidence,
        assessment_session_id="assessment-1",
        assessed_at=NOW,
        related_question_ids=tuple(f"followup-q{i}" for i in range(question_count))
        if evidence is not OutcomeEvidenceKind.NO_RELATED_EVIDENCE else (),
        related_concept_ids=("science",)
        if evidence is not OutcomeEvidenceKind.NO_RELATED_EVIDENCE else (),
        question_count=question_count,
        attempted_count=attempted_count,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unattempted_count=0,
        accuracy_percentage=(
            100.0 * correct_count / attempted_count if attempted_count else None
        ),
        baseline_attempted_count=baseline_count,
        baseline_accuracy_percentage=baseline_accuracy if baseline_count else None,
        follow_up_attempted_count=follow_up_count,
        follow_up_accuracy_percentage=follow_up_accuracy if follow_up_count else None,
        delta_percentage_points=delta,
        trend=trend,
        interpretation="Test evidence is descriptive and not causal.",
    )


def make_feedback_report(
    schedule: StudySchedule,
    outcome: StudyTaskOutcome,
) -> StudyOutcomeFeedbackReport:
    return StudyOutcomeFeedbackReport(
        learner_id=schedule.learner_id,
        schedule_id=schedule.schedule_id,
        assessment_session_id="assessment-1",
        assessed_at=NOW,
        outcomes=(outcome,),
        generated_at=NOW + timedelta(minutes=1),
    )


def run_strategy(
    schedule: StudySchedule,
    outcome: StudyTaskOutcome,
    *,
    service: AdaptiveStudyStrategyService | None = None,
):
    return (service or AdaptiveStudyStrategyService()).update_strategy(
        schedule,
        make_feedback_report(schedule, outcome),
        generated_at=NOW + timedelta(minutes=2),
    )


def test_declining_evidence_raises_priority_conservatively_and_shortens_interval():
    schedule = make_schedule()
    report = run_strategy(schedule, make_outcome())

    adjustment = report.adjustments[0]
    assert adjustment.action is StudyStrategyAction.REINFORCE_WEAK_AREA
    assert adjustment.recommended_priority_score > adjustment.current_priority_score
    assert adjustment.recommended_priority_score <= 1.0
    assert adjustment.suggested_revision_interval_days == 1
    assert adjustment.delta_percentage_points == -10.0
    assert report.adapted_task_count == 1


def test_improving_and_high_follow_up_accuracy_spaces_revision():
    schedule = make_schedule()
    outcome = make_outcome(
        trend=LearningTrend.IMPROVING,
        baseline_accuracy=70.0,
        follow_up_accuracy=90.0,
        delta=20.0,
    )

    adjustment = run_strategy(schedule, outcome).adjustments[0]
    assert adjustment.action is StudyStrategyAction.SPACE_REVISION
    assert adjustment.recommended_priority_score < adjustment.current_priority_score
    assert adjustment.suggested_revision_interval_days == 7


def test_improvement_below_consolidation_threshold_keeps_focus():
    schedule = make_schedule()
    outcome = make_outcome(
        trend=LearningTrend.IMPROVING,
        baseline_accuracy=50.0,
        follow_up_accuracy=70.0,
        delta=20.0,
    )

    adjustment = run_strategy(schedule, outcome).adjustments[0]
    assert adjustment.action is StudyStrategyAction.CONTINUE_TARGETED_PRACTICE
    assert adjustment.recommended_priority_score == adjustment.current_priority_score
    assert adjustment.suggested_revision_interval_days == 5


def test_stable_evidence_keeps_priority_and_uses_regular_retest_interval():
    schedule = make_schedule()
    outcome = make_outcome(
        trend=LearningTrend.STABLE,
        baseline_accuracy=60.0,
        follow_up_accuracy=62.0,
        delta=2.0,
    )

    adjustment = run_strategy(schedule, outcome).adjustments[0]
    assert adjustment.action is StudyStrategyAction.MAINTAIN_AND_RETEST
    assert adjustment.recommended_priority_score == adjustment.current_priority_score
    assert adjustment.suggested_revision_interval_days == 3


def test_insufficient_sample_does_not_change_priority_or_suggest_interval():
    schedule = make_schedule()
    outcome = make_outcome(trend=LearningTrend.INSUFFICIENT_DATA)

    report = run_strategy(schedule, outcome)
    adjustment = report.adjustments[0]
    assert adjustment.action is StudyStrategyAction.COLLECT_MORE_EVIDENCE
    assert adjustment.recommended_priority_score == adjustment.current_priority_score
    assert adjustment.suggested_revision_interval_days is None
    assert report.adapted_task_count == 0
    assert report.evidence_limited_count == 1


@pytest.mark.parametrize(
    "status",
    [StudyTaskExecutionStatus.SKIPPED, StudyTaskExecutionStatus.POSTPONED],
)
def test_skipped_or_postponed_work_cannot_trigger_strategy_update(status):
    schedule = make_schedule()
    outcome = make_outcome(status=status)
    adjustment = run_strategy(schedule, outcome).adjustments[0]

    assert adjustment.action is StudyStrategyAction.COLLECT_MORE_EVIDENCE
    assert adjustment.priority_delta == 0.0
    assert adjustment.suggested_revision_interval_days is None


def test_unlinked_evidence_is_not_used_even_with_large_claimed_delta():
    schedule = make_schedule()
    outcome = make_outcome(
        trend=LearningTrend.INSUFFICIENT_DATA,
        evidence=OutcomeEvidenceKind.NO_RELATED_EVIDENCE,
        baseline_accuracy=None,
        follow_up_accuracy=None,
    )

    adjustment = run_strategy(schedule, outcome).adjustments[0]
    assert adjustment.action is StudyStrategyAction.COLLECT_MORE_EVIDENCE
    assert adjustment.suggested_revision_interval_days is None
    assert adjustment.priority_delta == 0.0


def test_minimum_evidence_policy_can_hold_a_nominally_supported_trend():
    schedule = make_schedule()
    outcome = make_outcome(
        trend=LearningTrend.DECLINING,
        baseline_count=2,
        follow_up_count=2,
        baseline_accuracy=50.0,
        follow_up_accuracy=40.0,
        delta=-10.0,
    )
    service = AdaptiveStudyStrategyService(
        policy=AdaptiveStudyStrategyPolicy(
            minimum_baseline_attempts=3,
            minimum_follow_up_attempts=3,
        )
    )

    adjustment = run_strategy(schedule, outcome, service=service).adjustments[0]
    assert adjustment.action is StudyStrategyAction.COLLECT_MORE_EVIDENCE
    assert adjustment.priority_delta == 0.0
    assert adjustment.suggested_revision_interval_days is None


def test_service_rejects_cross_learner_or_wrong_schedule_report():
    schedule = make_schedule()
    report = make_feedback_report(schedule, make_outcome())
    service = AdaptiveStudyStrategyService()

    wrong_learner = StudyOutcomeFeedbackReport(
        learner_id="learner-2",
        schedule_id=schedule.schedule_id,
        assessment_session_id=report.assessment_session_id,
        assessed_at=report.assessed_at,
        outcomes=report.outcomes,
        generated_at=report.generated_at,
    )
    with pytest.raises(ValueError, match="learner does not match"):
        service.update_strategy(schedule, wrong_learner)

    other_schedule = make_schedule(priority=0.45)
    with pytest.raises(ValueError, match="fingerprint"):
        service.update_strategy(other_schedule, report)


def test_policy_rejects_bad_evidence_thresholds_and_unordered_intervals():
    with pytest.raises(ValueError, match="minimum_baseline_attempts"):
        AdaptiveStudyStrategyPolicy(minimum_baseline_attempts=0)
    with pytest.raises(ValueError, match="minimum priority change"):
        AdaptiveStudyStrategyPolicy(
            minimum_priority_change=0.2,
            maximum_priority_increase=0.1,
        )
    with pytest.raises(ValueError, match="ordered"):
        AdaptiveStudyStrategyPolicy(
            stable_revision_interval_days=6,
            improving_revision_interval_days=4,
        )


def test_strategy_report_requires_timezone_aware_and_post_assessment_time():
    schedule = make_schedule()
    report = make_feedback_report(schedule, make_outcome())
    service = AdaptiveStudyStrategyService()

    with pytest.raises(ValueError, match="timezone-aware"):
        service.update_strategy(schedule, report, generated_at=datetime(2026, 10, 9))
    with pytest.raises(ValueError, match="cannot precede"):
        service.update_strategy(schedule, report, generated_at=NOW - timedelta(seconds=1))
