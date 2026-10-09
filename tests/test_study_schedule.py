from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from dataclasses import replace

import pytest

from ai_comp.analysis.study_schedule import StudyScheduleService
from ai_comp.domain.adaptive_difficulty import AdaptiveAction, MasteryStatus
from ai_comp.domain.learning_history import (
    LearnerLearningHistory,
    LearnerTopicPerformance,
    LearningAttemptRecord,
    LearningTrend,
    LongTermPerformanceBand,
)
from ai_comp.domain.learning_progress import LearnerProgressReport, LearnerTopicProgress
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)
from ai_comp.domain.personalized_preparation import (
    PersonalizedPreparationMode,
    PersonalizedPreparationPlan,
)
from ai_comp.domain.preparation_guidance import (
    PreparationActionKind,
    PreparationGuidance,
    PreparationGuidanceAction,
)
from ai_comp.domain.question_intelligence import (
    DifficultyLevel,
    RankedQuestionCandidate,
    QuestionIntelligenceScore,
)
from ai_comp.domain.question_learning import (
    LearnerQuestionAttemptRecord,
    LearnerQuestionHistory,
    LearnerQuestionPerformance,
    QuestionOutcomeKind,
    QuestionRevisionCandidate,
)
from ai_comp.domain.study_schedule import (
    StudySchedulePolicy,
    StudyTaskKind,
)
from ai_comp.domain.test_engine import ScoringPolicy as ScorePolicy, TestSpecification as TestSpec


NOW = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


def make_question(question_id: str, concept_id: str) -> GeneratedMCQ:
    return GeneratedMCQ(
        generated_question_id=question_id,
        generation_id="generation-1",
        material_id="material-1",
        stem=f"Question for {concept_id}",
        options=(
            GeneratedOption("A", "one"),
            GeneratedOption("B", "two"),
            GeneratedOption("C", "three"),
            GeneratedOption("D", "four"),
        ),
        correct_option_key="B",
        explanation="Verified explanation",
        fact_ids=("fact-1",),
        concept_ids=(concept_id,),
        difficulty="MEDIUM",
        importance_score=0.8,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("source evidence",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.9,
    )


def make_candidate(question: GeneratedMCQ, rank: int, priority: float) -> RankedQuestionCandidate:
    return RankedQuestionCandidate(
        question_id=question.generated_question_id,
        rank=rank,
        score=QuestionIntelligenceScore(
            generated_question_id=question.generated_question_id,
            difficulty=DifficultyLevel.MEDIUM,
            difficulty_score=0.5,
            importance_score=0.8,
            novelty_score=0.6,
            coverage_score=0.7,
            selection_score=priority,
        ),
    )


def make_learning_history() -> LearnerLearningHistory:
    attempt = LearningAttemptRecord(
        attempt_id="attempt-1",
        learner_id="learner-1",
        test_id="old-test",
        session_id="old-session",
        total_questions=2,
        attempted_questions=2,
        correct_answers=1,
        incorrect_answers=1,
        unattempted_questions=0,
        raw_score=1.0,
        percentage=50.0,
        accuracy=0.5,
        completed_at=NOW - timedelta(days=1),
    )
    topics = (
        LearnerTopicPerformance(
            concept_id="science",
            test_count=1,
            question_count=1,
            attempted_count=1,
            correct_count=0,
            incorrect_count=1,
            unattempted_count=0,
            accuracy=0.0,
            recent_accuracy=0.0,
            performance=LongTermPerformanceBand.WEAK,
            trend=LearningTrend.DECLINING,
            weak_streak=1,
            priority_score=0.9,
        ),
        LearnerTopicPerformance(
            concept_id="history",
            test_count=1,
            question_count=1,
            attempted_count=1,
            correct_count=1,
            incorrect_count=0,
            unattempted_count=0,
            accuracy=1.0,
            recent_accuracy=1.0,
            performance=LongTermPerformanceBand.STRONG,
            trend=LearningTrend.STABLE,
            weak_streak=0,
            priority_score=0.4,
        ),
    )
    return LearnerLearningHistory(
        learner_id="learner-1",
        attempts=(attempt,),
        topic_performance=topics,
        generated_at=NOW,
    )


def make_question_history() -> LearnerQuestionHistory:
    recent_mistake = NOW - timedelta(hours=1)
    old_correct = NOW - timedelta(days=10)
    outcomes = (
        LearnerQuestionAttemptRecord(
            outcome_id="outcome-mistake",
            attempt_id="attempt-1",
            learner_id="learner-1",
            test_id="old-test",
            session_id="old-session",
            question_id="q-mistake",
            concept_ids=("science",),
            difficulty="MEDIUM",
            selected_option_key="A",
            correct_option_key="B",
            outcome=QuestionOutcomeKind.INCORRECT,
            completed_at=recent_mistake,
        ),
        LearnerQuestionAttemptRecord(
            outcome_id="outcome-due",
            attempt_id="attempt-1",
            learner_id="learner-1",
            test_id="old-test",
            session_id="old-session",
            question_id="q-due",
            concept_ids=("history",),
            difficulty="MEDIUM",
            selected_option_key="B",
            correct_option_key="B",
            outcome=QuestionOutcomeKind.CORRECT,
            completed_at=old_correct,
        ),
    )
    performance = (
        LearnerQuestionPerformance(
            question_id="q-mistake",
            concept_ids=("science",),
            difficulty="MEDIUM",
            test_count=1,
            attempt_count=1,
            correct_count=0,
            incorrect_count=1,
            unattempted_count=0,
            accuracy=0.0,
            last_outcome=QuestionOutcomeKind.INCORRECT,
            mistake_count=1,
            mistake_streak=1,
            priority_score=0.95,
            last_seen_at=recent_mistake,
        ),
        LearnerQuestionPerformance(
            question_id="q-due",
            concept_ids=("history",),
            difficulty="MEDIUM",
            test_count=1,
            attempt_count=1,
            correct_count=1,
            incorrect_count=0,
            unattempted_count=0,
            accuracy=1.0,
            last_outcome=QuestionOutcomeKind.CORRECT,
            mistake_count=0,
            mistake_streak=0,
            priority_score=0.5,
            last_seen_at=old_correct,
        ),
    )
    revision = (
        QuestionRevisionCandidate(
            question_id="q-mistake",
            concept_ids=("science",),
            difficulty="MEDIUM",
            priority_score=0.95,
            mistake_count=1,
            mistake_streak=1,
            last_incorrect_at=recent_mistake,
            reason="last answer was incorrect",
        ),
    )
    return LearnerQuestionHistory(
        learner_id="learner-1",
        outcomes=outcomes,
        question_performance=performance,
        revision_candidates=revision,
        repeated_concept_alerts=(),
        generated_at=NOW,
    )


def make_guidance() -> tuple[PreparationGuidance, tuple[GeneratedMCQ, ...]]:
    questions = (
        make_question("q-mistake", "science"),
        make_question("q-due", "history"),
        make_question("q-practice", "geography"),
    )
    candidates = tuple(
        make_candidate(question, index, score)
        for index, (question, score) in enumerate(
            zip(questions, (0.8, 0.7, 0.9)),
            start=1,
        )
    )
    specification = TestSpec(
        test_id="next-test",
        title="Next adaptive test",
        question_count=3,
        duration_seconds=600,
        scoring=ScorePolicy(correct_marks=1.0, incorrect_marks=0.0),
    )
    plan = PersonalizedPreparationPlan(
        learner_id="learner-1",
        test_specification=specification,
        mode=PersonalizedPreparationMode.ADAPTIVE,
        recommended_difficulty=DifficultyLevel.MEDIUM,
        question_ids=tuple(question.generated_question_id for question in questions),
        ranked_candidates=candidates,
        focus_concept_ids=("science", "history"),
        revision_question_ids=("q-mistake",),
        recommendations=(),
        reason="Selected by the existing personalized preparation planner.",
        retention_due_question_ids=("q-due",),
    )
    progress = LearnerProgressReport(
        learner_id="learner-1",
        completed_test_count=1,
        total_questions=2,
        current_test_percentage=50.0,
        baseline_average_percentage=None,
        recent_average_percentage=None,
        delta_percentage_points=None,
        trend=LearningTrend.INSUFFICIENT_DATA,
        baseline_test_count=0,
        recent_test_count=0,
        question_outcome_count=2,
        question_attempt_count=2,
        question_correct_count=1,
        question_accuracy=0.5,
        topics=(
            LearnerTopicProgress(
                concept_id="science",
                accuracy=0.0,
                recent_accuracy=0.0,
                trend=LearningTrend.DECLINING,
                performance=LongTermPerformanceBand.WEAK,
                weak_streak=1,
                priority_score=0.9,
                mastery=MasteryStatus.LEARNING,
                recommended_action=AdaptiveAction.REMEDIATE,
                decision_reason="Recorded performance remains weak.",
            ),
            LearnerTopicProgress(
                concept_id="history",
                accuracy=1.0,
                recent_accuracy=1.0,
                trend=LearningTrend.STABLE,
                performance=LongTermPerformanceBand.STRONG,
                weak_streak=0,
                priority_score=0.4,
                mastery=MasteryStatus.MASTERED,
                recommended_action=AdaptiveAction.RETAIN,
                decision_reason="Revision due.",
            ),
        ),
        retention_due_question_ids=("q-due",),
        generated_at=NOW,
    )
    guidance = PreparationGuidance(
        learner_id="learner-1",
        progress_report=progress,
        preparation_plan=plan,
        actions=(
            PreparationGuidanceAction(
                kind=PreparationActionKind.PRACTICE_WEAK_TOPICS,
                title="Practice priority topics",
                reason="Focus on evidence-backed weak concepts.",
                priority_score=0.9,
                concept_ids=("science",),
            ),
        ),
        generated_at=NOW,
    )
    return guidance, questions


def build_schedule(**overrides):
    guidance, questions = make_guidance()
    args = dict(
        learner_id="learner-1",
        guidance=guidance,
        history=make_learning_history(),
        question_history=make_question_history(),
        questions=questions,
        daily_minutes=60,
        weekday_minutes=None,
        start_date=TODAY,
        horizon_days=7,
        exam_date=None,
        as_of=NOW,
    )
    args.update(overrides)
    return StudyScheduleService().build_schedule(**args)


def test_schedule_uses_due_revision_mistakes_weak_topics_and_practice():
    schedule = build_schedule(exam_date=TODAY + timedelta(days=3), horizon_days=7)

    all_tasks = tuple(task for day in schedule.days for task in day.tasks)
    kinds = {task.kind for task in all_tasks}

    assert schedule.learner_id == "learner-1"
    assert schedule.end_date == TODAY + timedelta(days=3)
    assert kinds == {
        StudyTaskKind.REVIEW_DUE_REVISION,
        StudyTaskKind.REVIEW_PREVIOUS_MISTAKES,
        StudyTaskKind.STUDY_WEAK_TOPIC,
        StudyTaskKind.PRACTICE_QUESTIONS,
    }
    assert any("science" in task.concept_ids for task in all_tasks)
    assert any("q-due" in task.question_ids for task in all_tasks)
    assert any("q-mistake" in task.question_ids for task in all_tasks)
    assert any("q-practice" in task.question_ids for task in all_tasks)
    assert all(day.scheduled_minutes <= day.available_minutes for day in schedule.days)
    assert schedule.scheduled_minutes <= schedule.total_available_minutes
    assert all(day.available_minutes == 0 for day in schedule.days if day.study_date == schedule.exam_date)
    assert not any(task.scheduled_date == schedule.exam_date for task in all_tasks)
    assert schedule.remaining_work_minutes >= 0


def test_weekday_overrides_are_respected_and_exam_day_is_not_used_for_study():
    schedule = build_schedule(
        daily_minutes=60,
        weekday_minutes={4: 15, 5: 0, 6: 10, 0: 30},
        horizon_days=10,
        exam_date=date(2026, 10, 12),
    )
    available = {day.study_date: day.available_minutes for day in schedule.days}

    assert available[TODAY] == 15
    assert available[TODAY + timedelta(days=1)] == 0
    assert available[TODAY + timedelta(days=2)] == 10
    assert available[date(2026, 10, 12)] == 0
    assert all(day.scheduled_minutes <= day.available_minutes for day in schedule.days)
    assert all(day.study_date < date(2026, 10, 12) or not day.tasks for day in schedule.days)


def test_zero_availability_returns_explicit_unallocated_work():
    schedule = build_schedule(
        daily_minutes=0,
        weekday_minutes={weekday: 0 for weekday in range(7)},
        horizon_days=3,
    )

    assert schedule.scheduled_minutes == 0
    assert schedule.remaining_work_minutes > 0
    assert schedule.unscheduled_work
    assert all(not day.tasks for day in schedule.days)


def test_schedule_rejects_cross_learner_history_and_unaccepted_questions():
    guidance, questions = make_guidance()
    service = StudyScheduleService()

    with pytest.raises(ValueError, match="learning history learner does not match"):
        service.build_schedule(
            "learner-1",
            guidance=guidance,
            history=replace(make_learning_history(), learner_id="learner-2"),
            question_history=make_question_history(),
            questions=questions,
            daily_minutes=60,
            start_date=TODAY,
            as_of=NOW,
        )

    with pytest.raises(ValueError, match="missing or non-accepted"):
        service.build_schedule(
            "learner-1",
            guidance=guidance,
            history=make_learning_history(),
            question_history=make_question_history(),
            questions=questions[:-1],
            daily_minutes=60,
            start_date=TODAY,
            as_of=NOW,
        )


def test_schedule_rejects_invalid_availability_and_exam_date():
    with pytest.raises(ValueError, match="weekday availability keys"):
        build_schedule(weekday_minutes={7: 30})

    with pytest.raises(ValueError, match="exam_date cannot precede start_date"):
        build_schedule(exam_date=TODAY - timedelta(days=1))


def test_policy_rejects_question_estimate_larger_than_a_study_block():
    with pytest.raises(ValueError, match="cannot exceed maximum block"):
        StudySchedulePolicy(
            review_minutes_per_question=60,
            maximum_block_minutes=45,
        )
