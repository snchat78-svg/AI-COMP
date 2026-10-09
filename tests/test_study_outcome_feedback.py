from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from ai_comp.analysis.study_outcome_feedback import (
    StudyOutcomeFeedbackPolicy,
    StudyOutcomeFeedbackService,
)
from ai_comp.domain.learning_history import (
    LearningAttemptRecord,
    LearnerLearningHistory,
    LearningTrend,
)
from ai_comp.domain.question_learning import (
    LearnerQuestionAttemptRecord,
    LearnerQuestionHistory,
    QuestionOutcomeKind,
)
from ai_comp.domain.study_schedule import (
    ScheduledStudyTask,
    StudyDayPlan,
    StudySchedule,
    StudyTaskKind,
)
from ai_comp.domain.study_schedule_execution import (
    StudyTaskExecution,
    StudyTaskExecutionConflictError,
    StudyTaskExecutionStatus,
)
from ai_comp.domain.study_outcome_feedback import OutcomeEvidenceKind
from ai_comp.domain.test_analysis import QuestionOutcome, TestAnalysis as Analysis
from ai_comp.domain.test_engine import TestSessionStatus
from ai_comp.analysis.completed_test_feedback import CompletedTestFeedback


NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


class InMemoryExecutionRepository:
    def __init__(self):
        self.events: dict[str, StudyTaskExecution] = {}

    def get_event(self, event_id):
        return self.events.get(event_id)

    def save_event(self, event):
        current = self.events.get(event.event_id)
        if current is not None and current != event:
            raise StudyTaskExecutionConflictError("conflicting event")
        self.events[event.event_id] = event

    def list_for_schedule(self, schedule_id, learner_id):
        return tuple(sorted(
            (
                item for item in self.events.values()
                if item.schedule_id == schedule_id and item.learner_id == learner_id
            ),
            key=lambda item: (item.occurred_at, item.event_id),
        ))


def make_schedule(*, concept="science", question_ids=("old-q1", "old-q2")):
    task = ScheduledStudyTask(
        task_id="study-task-1",
        kind=StudyTaskKind.REVIEW_PREVIOUS_MISTAKES,
        scheduled_date=TODAY - timedelta(days=1),
        title="Review prior work",
        estimated_minutes=10,
        priority_score=0.9,
        reason="Evidence-backed prior practice.",
        concept_ids=(concept,),
        question_ids=question_ids,
    )
    return StudySchedule(
        learner_id="learner-1",
        start_date=TODAY - timedelta(days=2),
        end_date=TODAY - timedelta(days=1),
        exam_date=None,
        days=(
            StudyDayPlan(TODAY - timedelta(days=2), 30, ()),
            StudyDayPlan(TODAY - timedelta(days=1), 30, (task,)),
        ),
        unscheduled_work=(),
        generated_at=NOW - timedelta(days=2),
    )


def make_event(
    schedule,
    *,
    event_id="executed-1",
    status=StudyTaskExecutionStatus.COMPLETED,
    occurred_at=None,
):
    return StudyTaskExecution(
        event_id=event_id,
        schedule_id=schedule.schedule_id,
        learner_id=schedule.learner_id,
        task_id="study-task-1",
        status=status,
        occurred_at=occurred_at or NOW - timedelta(hours=12),
        actual_minutes=10,
    )


def prior_record(index, *, concept="science", correct=False, completed_at=None):
    outcome = QuestionOutcomeKind.CORRECT if correct else QuestionOutcomeKind.INCORRECT
    return LearnerQuestionAttemptRecord(
        outcome_id=f"old-outcome-{index}",
        attempt_id=f"old-attempt-{index}",
        learner_id="learner-1",
        test_id=f"old-test-{index}",
        session_id=f"old-session-{index}",
        question_id=f"old-question-{index}",
        concept_ids=(concept,),
        difficulty="MEDIUM",
        selected_option_key="B" if correct else "A",
        correct_option_key="B",
        outcome=outcome,
        completed_at=completed_at or NOW - timedelta(days=5 - index),
    )


def make_feedback(*, current_question_ids=("new-q1", "new-q2"), concepts=("science", "science"),
                  correct=(True, True), assessment_time=NOW):
    outcomes = tuple(
        QuestionOutcome(
            question_id=question_id,
            concept_ids=(concept,),
            selected_option_key="B" if is_correct else "A",
            correct_option_key="B",
            attempted=True,
            correct=is_correct,
            difficulty="MEDIUM",
        )
        for question_id, concept, is_correct in zip(current_question_ids, concepts, correct)
    )
    correct_count = sum(correct)
    incorrect_count = len(correct) - correct_count
    analysis = Analysis(
        test_id="follow-up-test",
        session_id="follow-up-session",
        total_questions=len(outcomes),
        attempted_questions=len(outcomes),
        correct_answers=correct_count,
        incorrect_answers=incorrect_count,
        unattempted_questions=0,
        raw_score=float(correct_count),
        percentage=(100.0 * correct_count / len(outcomes)),
        accuracy=correct_count / len(outcomes),
        outcomes=outcomes,
        topic_performance=(),
        weak_topics=(),
    )
    attempt = LearningAttemptRecord(
        attempt_id="attempt-follow-up",
        learner_id="learner-1",
        test_id="follow-up-test",
        session_id="follow-up-session",
        total_questions=len(outcomes),
        attempted_questions=len(outcomes),
        correct_answers=correct_count,
        incorrect_answers=incorrect_count,
        unattempted_questions=0,
        raw_score=float(correct_count),
        percentage=(100.0 * correct_count / len(outcomes)),
        accuracy=correct_count / len(outcomes),
        completed_at=assessment_time,
    )
    current_history = tuple(
        LearnerQuestionAttemptRecord(
            outcome_id=f"followup-outcome-{index}",
            attempt_id=attempt.attempt_id,
            learner_id="learner-1",
            test_id="follow-up-test",
            session_id="follow-up-session",
            question_id=outcome.question_id,
            concept_ids=outcome.concept_ids,
            difficulty=outcome.difficulty,
            selected_option_key=outcome.selected_option_key,
            correct_option_key=outcome.correct_option_key,
            outcome=(
                QuestionOutcomeKind.CORRECT if outcome.correct
                else QuestionOutcomeKind.INCORRECT
            ),
            completed_at=assessment_time,
        )
        for index, outcome in enumerate(outcomes, start=1)
    )
    historical = tuple(
        prior_record(index, correct=index == 1, completed_at=NOW - timedelta(days=6-index))
        for index in range(1, 5)
    )
    learning_history = LearnerLearningHistory(
        learner_id="learner-1",
        attempts=(attempt,),
        topic_performance=(),
        generated_at=assessment_time,
    )
    question_history = LearnerQuestionHistory(
        learner_id="learner-1",
        outcomes=historical + current_history,
        question_performance=(),
        revision_candidates=(),
        repeated_concept_alerts=(),
        generated_at=assessment_time,
    )
    session = SimpleNamespace(
        session_id="follow-up-session",
        status=TestSessionStatus.SUBMITTED,
    )
    result = SimpleNamespace(session_id="follow-up-session")
    return CompletedTestFeedback(
        learner_id="learner-1",
        session=session,
        result=result,
        analysis=analysis,
        attempt=attempt,
        learning_history=learning_history,
        question_history=question_history,
    )


def test_follow_up_result_links_by_concept_and_compares_with_pre_study_baseline():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    repository.save_event(make_event(schedule))
    feedback = make_feedback(correct=(True, True))

    report = StudyOutcomeFeedbackService(repository).evaluate(
        schedule, feedback, generated_at=NOW + timedelta(minutes=1)
    )

    assert report.learner_id == "learner-1"
    assert report.assessment_session_id == "follow-up-session"
    assert report.linked_task_count == 1
    outcome = report.outcomes[0]
    assert outcome.evidence_kind is OutcomeEvidenceKind.CONCEPT_OVERLAP
    assert outcome.related_question_ids == ("new-q1", "new-q2")
    assert outcome.baseline_attempted_count == 4
    assert outcome.baseline_accuracy_percentage == pytest.approx(25.0)
    assert outcome.follow_up_attempted_count == 2
    assert outcome.follow_up_accuracy_percentage == pytest.approx(100.0)
    assert outcome.delta_percentage_points == pytest.approx(75.0)
    assert outcome.trend is LearningTrend.IMPROVING
    assert "not proof" in outcome.interpretation


def test_direct_question_overlap_has_priority_over_concept_overlap():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    repository.save_event(make_event(schedule))
    feedback = make_feedback(current_question_ids=("old-q1", "old-q2"))

    report = StudyOutcomeFeedbackService(repository).evaluate(
        schedule, feedback, generated_at=NOW + timedelta(minutes=1)
    )

    assert report.outcomes[0].evidence_kind is OutcomeEvidenceKind.DIRECT_QUESTION_MATCH
    assert report.outcomes[0].related_question_ids == ("old-q1", "old-q2")


def test_insufficient_baseline_or_follow_up_sample_does_not_invent_a_trend():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    repository.save_event(make_event(schedule))
    feedback = make_feedback(current_question_ids=("new-q1",), concepts=("science",), correct=(True,))

    report = StudyOutcomeFeedbackService(
        repository,
        policy=StudyOutcomeFeedbackPolicy(
            minimum_baseline_attempts=4,
            minimum_follow_up_attempts=2,
        ),
    ).evaluate(schedule, feedback, generated_at=NOW + timedelta(minutes=1))

    outcome = report.outcomes[0]
    assert outcome.trend is LearningTrend.INSUFFICIENT_DATA
    assert outcome.delta_percentage_points is None
    assert outcome.follow_up_accuracy_percentage == pytest.approx(100.0)


def test_skipped_or_postponed_task_is_not_attributed_as_study():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    repository.save_event(make_event(schedule, status=StudyTaskExecutionStatus.SKIPPED))
    report = StudyOutcomeFeedbackService(repository).evaluate(
        schedule, make_feedback(), generated_at=NOW + timedelta(minutes=1)
    )

    assert report.outcomes[0].execution_status is StudyTaskExecutionStatus.SKIPPED
    assert report.outcomes[0].evidence_kind is OutcomeEvidenceKind.NO_RELATED_EVIDENCE
    assert report.outcomes[0].accuracy_percentage is None
    assert report.comparison_count == 0


def test_execution_after_follow_up_assessment_is_not_counted():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    repository.save_event(make_event(
        schedule, occurred_at=NOW + timedelta(minutes=5)
    ))
    report = StudyOutcomeFeedbackService(repository).evaluate(
        schedule, make_feedback(), generated_at=NOW + timedelta(minutes=1)
    )

    assert report.outcomes == ()
    assert report.linked_task_count == 0


def test_service_rejects_cross_learner_and_invalid_report_clock():
    schedule = make_schedule()
    repository = InMemoryExecutionRepository()
    repository.save_event(make_event(schedule))
    feedback = make_feedback()
    wrong_learner = replace(feedback, learner_id="learner-2")
    with pytest.raises(ValueError, match="learner does not match"):
        StudyOutcomeFeedbackService(repository).evaluate(
            schedule, wrong_learner, generated_at=NOW + timedelta(minutes=1)
        )
    with pytest.raises(ValueError, match="cannot precede"):
        StudyOutcomeFeedbackService(repository).evaluate(
            schedule, feedback, generated_at=NOW - timedelta(minutes=1)
        )


def test_policy_validates_evidence_thresholds():
    with pytest.raises(ValueError, match="minimum_baseline_attempts"):
        StudyOutcomeFeedbackPolicy(minimum_baseline_attempts=0)
    with pytest.raises(ValueError, match="stable threshold"):
        StudyOutcomeFeedbackPolicy(stable_threshold_percentage_points=0)
