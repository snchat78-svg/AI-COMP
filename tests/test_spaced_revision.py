from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai_comp.analysis.question_learning import QuestionLearningHistoryService
from ai_comp.analysis.spaced_revision import (
    SpacedRevisionService,
    TimeAwareQuestionSelector,
)
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)
from ai_comp.domain.question_intelligence import (
    DifficultyLevel,
    RankedQuestionCandidate,
    QuestionIntelligenceScore,
)
from ai_comp.domain.question_learning import (
    QuestionOutcomeKind,
)
from ai_comp.domain.test_analysis import (
    PerformanceBand,
    QuestionOutcome,
    TestAnalysis,
    TopicPerformance,
    WeakTopic,
)


class Repo:
    def __init__(self):
        self.rows = {}

    def save_outcomes(self, outcomes):
        for row in outcomes:
            self.rows[row.outcome_id] = row

    def list_outcomes(self, learner_id):
        return tuple(
            sorted(
                (
                    row for row in self.rows.values()
                    if row.learner_id == learner_id
                ),
                key=lambda row: (
                    row.completed_at,
                    row.session_id,
                    row.question_id,
                ),
            )
        )


def analysis(session_id, question_id, correct):
    accuracy = 1.0 if correct else 0.0
    topic = TopicPerformance(
        concept_id="science",
        question_count=1,
        attempted_count=1,
        correct_count=int(correct),
        incorrect_count=int(not correct),
        unattempted_count=0,
        accuracy=accuracy,
        performance=(
            PerformanceBand.STRONG
            if correct
            else PerformanceBand.WEAK
        ),
    )
    return TestAnalysis(
        test_id=f"t-{session_id}",
        session_id=session_id,
        total_questions=1,
        attempted_questions=1,
        correct_answers=int(correct),
        incorrect_answers=int(not correct),
        unattempted_questions=0,
        raw_score=1.0 if correct else -0.25,
        percentage=100.0 if correct else -25.0,
        accuracy=accuracy,
        outcomes=(
            QuestionOutcome(
                question_id=question_id,
                concept_ids=("science",),
                selected_option_key="B" if correct else "A",
                correct_option_key="B",
                attempted=True,
                correct=correct,
                difficulty="EASY",
            ),
        ),
        topic_performance=(topic,),
        weak_topics=(
            WeakTopic(
                concept_id="science",
                priority_score=1.0 - accuracy,
                accuracy=accuracy,
                attempted_count=1,
                question_count=1,
                reason="weak",
            ),
        ) if not correct else (),
    )


def question(qid):
    return GeneratedMCQ(
        generated_question_id=qid,
        generation_id="g",
        material_id="m",
        stem=qid,
        options=(
            GeneratedOption("A", "one"),
            GeneratedOption("B", "two"),
            GeneratedOption("C", "three"),
            GeneratedOption("D", "four"),
        ),
        correct_option_key="B",
        explanation="source",
        fact_ids=("f",),
        concept_ids=("science",),
        difficulty="EASY",
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("source",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def candidate(qid, rank):
    return RankedQuestionCandidate(
        question_id=qid,
        rank=rank,
        score=QuestionIntelligenceScore(
            generated_question_id=qid,
            difficulty=DifficultyLevel.EASY,
            difficulty_score=0.25,
            importance_score=0.9,
            novelty_score=1.0,
            coverage_score=0.5,
            selection_score=0.8,
        ),
    )


def test_incorrect_question_is_due_after_one_day():
    repo = Repo()
    service = QuestionLearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.record_analysis(
        "learner",
        analysis("s1", "q1", False),
        completed_at=t0,
    )
    history = service.history("learner", generated_at=t0)
    schedule = SpacedRevisionService().schedules(
        history,
        as_of=t0 + timedelta(days=1),
    )[0]
    assert schedule.question_id == "q1"
    assert schedule.status.value == "DUE"
    assert schedule.interval_days == 1


def test_correct_streak_expands_interval():
    repo = Repo()
    service = QuestionLearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for index in range(3):
        service.record_analysis(
            "learner",
            analysis(f"s{index}", "q1", True),
            completed_at=t0 + timedelta(days=index * 3),
        )
    history = service.history("learner", generated_at=t0)
    schedule = SpacedRevisionService().schedules(
        history,
        as_of=t0 + timedelta(days=2),
    )[0]
    assert schedule.correct_streak == 3
    assert schedule.interval_days == 7
    assert schedule.status.value == "UPCOMING"


def test_time_aware_selector_prioritizes_due_question():
    repo = Repo()
    service = QuestionLearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.record_analysis(
        "learner",
        analysis("s1", "q1", False),
        completed_at=t0,
    )
    history = service.history("learner", generated_at=t0)

    questions = (question("q1"), question("q2"))
    candidates = (candidate("q2", 1), candidate("q1", 2))

    plan = TimeAwareQuestionSelector().select(
        history,
        candidates,
        questions,
        question_count=2,
        as_of=t0 + timedelta(days=2),
    )
    assert plan.question_ids[0] == "q1"
    assert plan.due_question_ids == ("q1",)


def test_selector_honors_exclusions_and_accepted_questions():
    repo = Repo()
    service = QuestionLearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.record_analysis(
        "learner",
        analysis("s1", "q1", False),
        completed_at=t0,
    )
    history = service.history("learner", generated_at=t0)

    questions = (question("q1"), question("q2"))
    rejected = GeneratedMCQ(
        generated_question_id="bad",
        generation_id="g",
        material_id="m",
        stem="bad",
        options=(
            GeneratedOption("A", "one"),
            GeneratedOption("B", "two"),
            GeneratedOption("C", "three"),
            GeneratedOption("D", "four"),
        ),
        correct_option_key="B",
        explanation="source",
        fact_ids=("f",),
        concept_ids=("science",),
        difficulty="EASY",
        importance_score=0.9,
        status=GeneratedQuestionStatus.REJECTED,
        quality_score=0.0,
    )
    questions = questions + (rejected,)
    candidates = (
        candidate("q1", 1),
        candidate("q2", 2),
    )
    plan = TimeAwareQuestionSelector().select(
        history,
        candidates,
        questions,
        question_count=1,
        as_of=t0 + timedelta(days=2),
        exclude_question_ids=("q1",),
    )
    assert plan.question_ids == ("q2",)
    assert plan.due_question_ids == ()


def test_wrong_outcome_has_no_fake_correct_streak():
    repo = Repo()
    service = QuestionLearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.record_analysis(
        "learner",
        analysis("s1", "q1", True),
        completed_at=t0,
    )
    service.record_analysis(
        "learner",
        analysis("s2", "q1", False),
        completed_at=t0 + timedelta(days=2),
    )
    history = service.history("learner", generated_at=t0)
    schedule = SpacedRevisionService().schedules(history, as_of=t0 + timedelta(days=3))[0]
    assert schedule.correct_streak == 0
    assert schedule.interval_days == 1
    assert schedule.status.value == "DUE"
