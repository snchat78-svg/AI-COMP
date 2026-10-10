from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import replace

import pytest

from ai_comp.analysis.adaptive_study_strategy_feedback import (
    AdaptiveStudyStrategyFeedbackPolicy,
    AdaptiveStudyStrategyFeedbackService,
)
from ai_comp.domain.adaptive_study_strategy import StudyStrategyAction
from ai_comp.domain.adaptive_study_strategy_feedback import StrategyFeedbackKind
from ai_comp.domain.adaptive_study_strategy_history import (
    AdaptiveStudyStrategyHistoryReport,
    ConceptStrategyHistory,
    StrategyHistoryScopeKind,
)
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.study_schedule import StudyTaskKind


NOW = datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc)


def make_scope(**changes):
    values = dict(
        scope_kind=StrategyHistoryScopeKind.CONCEPTS,
        scope_ids=("science",),
        task_kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        decision_count=3,
        assessment_count=3,
        improving_count=0,
        declining_count=2,
        stable_count=1,
        insufficient_data_count=0,
        mean_baseline_accuracy_percentage=70.0,
        mean_follow_up_accuracy_percentage=60.0,
        mean_delta_percentage_points=-10.0,
        mean_recommended_priority_delta=0.12,
        mean_applied_priority_delta=0.12,
        latest_action=StudyStrategyAction.REINFORCE_WEAK_AREA,
        latest_recorded_at=NOW - timedelta(hours=1),
    )
    values.update(changes)
    return ConceptStrategyHistory(**values)


def make_history(*scopes):
    return AdaptiveStudyStrategyHistoryReport(
        learner_id="learner-1",
        entries=(),
        scopes=tuple(scopes),
        generated_at=NOW,
    )


def test_repeated_decline_after_reinforcement_suggests_changing_approach():
    report = AdaptiveStudyStrategyFeedbackService().build_report(
        make_history(make_scope()),
        generated_at=NOW + timedelta(minutes=1),
    )

    assert report.learner_id == "learner-1"
    assert report.source_audit_count == 0
    assert report.evaluated_scope_count == 1
    assert report.not_actionable_scope_count == 0
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.kind is StrategyFeedbackKind.CHANGE_APPROACH
    assert finding.scope_ids == ("science",)
    assert finding.priority_score == pytest.approx(0.88)
    assert "does not prove" in finding.reason


@pytest.mark.parametrize(
    "changes",
    [
        {"assessment_count": 2},
        {"decision_count": 2, "assessment_count": 2, "declining_count": 2, "stable_count": 0},
        {"declining_count": 1, "stable_count": 2},
        {"mean_delta_percentage_points": -4.9},
        {"improving_count": 2, "declining_count": 1, "stable_count": 0},
        {"latest_action": StudyStrategyAction.CONTINUE_TARGETED_PRACTICE},
    ],
)
def test_insufficient_or_mixed_pattern_does_not_trigger_change_prompt(changes):
    scope = make_scope(**changes)
    report = AdaptiveStudyStrategyFeedbackService().build_report(
        make_history(scope),
        generated_at=NOW + timedelta(minutes=1),
    )

    assert report.findings == ()
    assert report.not_actionable_scope_count == 1


def test_feedback_service_validates_policy_and_report_clock():
    with pytest.raises(ValueError, match="minimum_assessment_count"):
        AdaptiveStudyStrategyFeedbackPolicy(minimum_assessment_count=0)

    service = AdaptiveStudyStrategyFeedbackService()
    with pytest.raises(ValueError, match="timezone-aware"):
        service.build_report(make_history(make_scope()), generated_at=datetime(2026, 10, 10))
    with pytest.raises(ValueError, match="cannot precede"):
        service.build_report(
            make_history(make_scope()),
            generated_at=NOW - timedelta(seconds=1),
        )


def test_feedback_report_does_not_cross_learner_context():
    history = replace(make_history(make_scope()), learner_id="learner-2")
    report = AdaptiveStudyStrategyFeedbackService().build_report(
        history, generated_at=NOW + timedelta(minutes=1)
    )
    assert report.learner_id == "learner-2"
