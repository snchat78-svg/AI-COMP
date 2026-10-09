from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai_comp.analysis.learning_progress import LearningProgressService
from ai_comp.domain.adaptive_difficulty import (
    AdaptiveAction,
    AdaptiveDifficultyDecision,
    AdaptiveDifficultyProfile,
    MasteryStatus,
)
from ai_comp.domain.learning_history import (
    LearnerLearningHistory,
    LearnerTopicPerformance,
    LearningAttemptRecord,
    LearningTrend,
    LongTermPerformanceBand,
)
from ai_comp.domain.question_intelligence import DifficultyLevel
from ai_comp.domain.question_learning import (
    LearnerQuestionAttemptRecord,
    LearnerQuestionHistory,
    QuestionOutcomeKind,
)


NOW = datetime(2026, 10, 9, tzinfo=timezone.utc)


def make_attempt(index: int, percentage: float) -> LearningAttemptRecord:
    correct = round(percentage / 10)
    return LearningAttemptRecord(
        attempt_id=f"attempt-{index}",
        learner_id="learner-1",
        test_id=f"test-{index}",
        session_id=f"session-{index}",
        total_questions=10,
        attempted_questions=10,
        correct_answers=correct,
        incorrect_answers=10 - correct,
        unattempted_questions=0,
        raw_score=float(correct),
        percentage=percentage,
        accuracy=correct / 10,
        completed_at=NOW + timedelta(days=index),
    )


def make_topic(
    concept_id: str,
    *,
    accuracy: float,
    recent_accuracy: float,
    trend: LearningTrend,
    priority_score: float,
    weak_streak: int = 0,
) -> LearnerTopicPerformance:
    performance = (
        LongTermPerformanceBand.WEAK
        if accuracy < 0.50
        else LongTermPerformanceBand.AVERAGE
        if accuracy < 0.75
        else LongTermPerformanceBand.STRONG
    )
    return LearnerTopicPerformance(
        concept_id=concept_id,
        test_count=2,
        question_count=10,
        attempted_count=10,
        correct_count=round(accuracy * 10),
        incorrect_count=10 - round(accuracy * 10),
        unattempted_count=0,
        accuracy=accuracy,
        recent_accuracy=recent_accuracy,
        performance=performance,
        trend=trend,
        weak_streak=weak_streak,
        priority_score=priority_score,
    )


def make_question_outcome(
    outcome_id: str,
    question_id: str,
    outcome: QuestionOutcomeKind,
) -> LearnerQuestionAttemptRecord:
    correct = outcome is QuestionOutcomeKind.CORRECT
    unattempted = outcome is QuestionOutcomeKind.UNATTEMPTED
    return LearnerQuestionAttemptRecord(
        outcome_id=outcome_id,
        attempt_id=f"attempt-{outcome_id}",
        learner_id="learner-1",
        test_id="test-q",
        session_id=f"session-{outcome_id}",
        question_id=question_id,
        concept_ids=("science",),
        difficulty="MEDIUM",
        selected_option_key=None if unattempted else ("B" if correct else "A"),
        correct_option_key="B",
        outcome=outcome,
        completed_at=NOW,
    )


def histories(
    percentages: tuple[float, ...],
    *,
    topics: tuple[LearnerTopicPerformance, ...] = (),
    outcomes: tuple[LearnerQuestionAttemptRecord, ...] = (),
):
    attempts = tuple(make_attempt(i + 1, score) for i, score in enumerate(percentages))
    learning = LearnerLearningHistory(
        learner_id="learner-1",
        attempts=attempts,
        topic_performance=topics,
        generated_at=NOW,
    )
    question = LearnerQuestionHistory(
        learner_id="learner-1",
        outcomes=outcomes,
        question_performance=(),
        revision_candidates=(),
        repeated_concept_alerts=(),
        generated_at=NOW,
    )
    return learning, question


def profile() -> AdaptiveDifficultyProfile:
    decision = AdaptiveDifficultyDecision(
        concept_id="science",
        test_count=2,
        accuracy=0.4,
        recent_accuracy=0.3,
        trend=LearningTrend.DECLINING,
        weak_streak=2,
        mastery=MasteryStatus.LEARNING,
        action=AdaptiveAction.REMEDIATE,
        recommended_difficulty=DifficultyLevel.EASY,
        retention_due_count=1,
        priority_score=0.9,
        reason="persistent weakness requires remediation",
    )
    return AdaptiveDifficultyProfile(
        learner_id="learner-1",
        decisions=(decision,),
        recommended_difficulty=DifficultyLevel.EASY,
        retention_due_question_ids=("q-due",),
        generated_at=NOW,
    )


def test_progress_report_compares_recent_results_with_previous_window():
    learning, question = histories((40.0, 50.0, 70.0, 80.0))
    report = LearningProgressService(comparison_window_size=2).analyze(
        "learner-1", learning, question, generated_at=NOW,
    )

    assert report.completed_test_count == 4
    assert report.total_questions == 40
    assert report.current_test_percentage == 80.0
    assert report.baseline_average_percentage == 45.0
    assert report.recent_average_percentage == 75.0
    assert report.delta_percentage_points == 30.0
    assert report.trend is LearningTrend.IMPROVING
    assert report.baseline_test_count == report.recent_test_count == 2


def test_progress_report_marks_small_change_stable_and_handles_question_accuracy():
    outcomes = (
        make_question_outcome("o1", "q1", QuestionOutcomeKind.CORRECT),
        make_question_outcome("o2", "q2", QuestionOutcomeKind.INCORRECT),
        make_question_outcome("o3", "q3", QuestionOutcomeKind.UNATTEMPTED),
    )
    learning, question = histories((60.0, 62.0), outcomes=outcomes)
    report = LearningProgressService().analyze(
        "learner-1", learning, question, generated_at=NOW,
    )

    assert report.trend is LearningTrend.STABLE
    assert report.delta_percentage_points == 2.0
    assert report.question_outcome_count == 3
    assert report.question_attempt_count == 2
    assert report.question_correct_count == 1
    assert report.question_accuracy == 0.5


def test_progress_report_orders_topics_and_attaches_existing_adaptive_decisions():
    topics = (
        make_topic(
            "history", accuracy=0.8, recent_accuracy=0.8,
            trend=LearningTrend.STABLE, priority_score=0.2,
        ),
        make_topic(
            "science", accuracy=0.4, recent_accuracy=0.3,
            trend=LearningTrend.DECLINING, priority_score=0.9, weak_streak=2,
        ),
    )
    learning, question = histories((40.0, 50.0), topics=topics)
    report = LearningProgressService().analyze(
        "learner-1", learning, question, adaptive_profile=profile(), generated_at=NOW,
    )

    assert tuple(topic.concept_id for topic in report.topics) == ("science", "history")
    assert report.topics[0].mastery is MasteryStatus.LEARNING
    assert report.topics[0].recommended_action is AdaptiveAction.REMEDIATE
    assert report.retention_due_question_ids == ("q-due",)


def test_progress_report_without_two_completed_tests_has_insufficient_data():
    learning, question = histories((75.0,))
    report = LearningProgressService().analyze(
        "learner-1", learning, question, generated_at=NOW,
    )

    assert report.trend is LearningTrend.INSUFFICIENT_DATA
    assert report.baseline_average_percentage is None
    assert report.recent_average_percentage is None
    assert report.delta_percentage_points is None
    assert report.current_test_percentage == 75.0


def test_progress_report_rejects_cross_learner_history_and_naive_time():
    learning, question = histories((40.0, 60.0))
    wrong_learning = LearnerLearningHistory(
        learner_id="learner-2",
        attempts=learning.attempts,
        topic_performance=learning.topic_performance,
        generated_at=NOW,
    )
    service = LearningProgressService()

    with pytest.raises(ValueError, match="learning history learner does not match"):
        service.analyze("learner-1", wrong_learning, question, generated_at=NOW)
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        service.analyze("learner-1", learning, question, generated_at=datetime(2026, 10, 9))
