from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.analysis.personalized_preparation import PersonalizedPreparationService
from ai_comp.analysis.question_learning import QuestionLearningHistoryService
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.question_intelligence import (
    DifficultyLevel,
    RankedQuestionCandidate,
    QuestionIntelligenceScore,
)
from ai_comp.domain.test_analysis import (
    PerformanceBand,
    QuestionOutcome,
    TestAnalysis,
    TopicPerformance,
    WeakTopic,
)
from ai_comp.test_engine import TestEngine


class InMemoryLearningHistoryRepository:
    def __init__(self):
        self.attempts = {}
        self.topics = []

    def save_attempt(self, attempt, topics):
        existing = self.attempts.get((attempt.learner_id, attempt.session_id))
        if existing is not None and existing != attempt:
            raise ValueError("conflict")
        self.attempts[(attempt.learner_id, attempt.session_id)] = attempt
        self.topics = [t for t in self.topics if t.attempt_id != attempt.attempt_id]
        self.topics.extend(topics)

    def get_attempt(self, learner_id, session_id):
        return self.attempts.get((learner_id, session_id))

    def list_attempts(self, learner_id):
        return tuple(sorted(
            (a for a in self.attempts.values() if a.learner_id == learner_id),
            key=lambda a: (a.completed_at, a.session_id),
        ))

    def list_topic_attempts(self, learner_id):
        ids = {a.attempt_id for a in self.list_attempts(learner_id)}
        return tuple(
            t for t in self.topics
            if t.learner_id == learner_id and t.attempt_id in ids
        )


class InMemoryQuestionHistoryRepository:
    def __init__(self):
        self.rows = {}

    def save_outcomes(self, outcomes):
        for row in outcomes:
            existing = self.rows.get(row.outcome_id)
            if existing is not None and existing != row:
                raise ValueError("conflict")
            self.rows[row.outcome_id] = row

    def list_outcomes(self, learner_id):
        return tuple(sorted(
            (row for row in self.rows.values() if row.learner_id == learner_id),
            key=lambda row: (row.completed_at, row.session_id, row.question_id),
        ))


def make_analysis(session_id, test_id, question_ids, correct_count=0):
    total = len(question_ids)
    accuracy = correct_count / total
    outcomes = tuple(
        QuestionOutcome(
            question_id=question_id,
            concept_ids=("science",),
            selected_option_key="B" if index < correct_count else "A",
            correct_option_key="B",
            attempted=True,
            correct=index < correct_count,
            difficulty="EASY",
        )
        for index, question_id in enumerate(question_ids)
    )
    topic = TopicPerformance(
        concept_id="science",
        question_count=total,
        attempted_count=total,
        correct_count=correct_count,
        incorrect_count=total - correct_count,
        unattempted_count=0,
        accuracy=accuracy,
        performance=(
            PerformanceBand.WEAK
            if accuracy < 0.5
            else PerformanceBand.AVERAGE
            if accuracy < 0.75
            else PerformanceBand.STRONG
        ),
    )
    return TestAnalysis(
        test_id=test_id,
        session_id=session_id,
        total_questions=total,
        attempted_questions=total,
        correct_answers=correct_count,
        incorrect_answers=total - correct_count,
        unattempted_questions=0,
        raw_score=float(correct_count),
        percentage=accuracy * 100.0,
        accuracy=accuracy,
        outcomes=outcomes,
        topic_performance=(topic,),
        weak_topics=(
            WeakTopic(
                concept_id="science",
                priority_score=1.0 - accuracy,
                accuracy=accuracy,
                attempted_count=total,
                question_count=total,
                reason="weak",
            ),
        ) if accuracy < 0.5 else (),
    )


def question(qid, difficulty="EASY"):
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
        difficulty=difficulty,
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("source",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def candidate(qid, rank, score=0.8, difficulty=DifficultyLevel.EASY):
    return RankedQuestionCandidate(
        question_id=qid,
        rank=rank,
        score=QuestionIntelligenceScore(
            generated_question_id=qid,
            difficulty=difficulty,
            difficulty_score=0.25 if difficulty is DifficultyLevel.EASY else 0.55,
            importance_score=0.9,
            novelty_score=1.0,
            coverage_score=0.5,
            selection_score=score,
        ),
    )


def make_histories(previous, current=None):
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    lr = InMemoryLearningHistoryRepository()
    ls = LearningHistoryService(lr)
    ls.record_analysis("learner", previous, completed_at=t0)
    if current is not None:
        ls.record_analysis(
            "learner",
            current,
            completed_at=t0 + timedelta(days=1),
        )

    qr = InMemoryQuestionHistoryRepository()
    qs = QuestionLearningHistoryService(qr)
    qs.record_analysis("learner", previous, completed_at=t0)
    if current is not None:
        qs.record_analysis(
            "learner",
            current,
            completed_at=t0 + timedelta(days=1),
        )
    return ls.history("learner"), qs.history("learner")


def test_adaptive_combines_prior_mistakes_and_weak_topics():
    previous = make_analysis("s0", "t0", ("old-0", "old-1"))
    current = make_analysis("s1", "t1", ("current-0", "current-1"))
    history, question_history = make_histories(previous, current)

    questions = tuple(
        question(qid)
        for qid in ("old-0", "old-1", "new-1", "new-2", "new-3", "new-4")
    )
    candidates = tuple(
        candidate(qid, rank, score=1.0 - rank * 0.05)
        for rank, qid in enumerate(
            ("old-0", "old-1", "new-1", "new-2", "new-3", "new-4"),
            start=1,
        )
    )

    plan = PersonalizedPreparationService().build_plan(
        "learner",
        test_id="next-1",
        title="Personalized Revision",
        question_count=4,
        duration_seconds=3600,
        history=history,
        question_history=question_history,
        current_analysis=current,
        candidates=candidates,
        questions=questions,
    )

    assert plan.mode is PersonalizedPreparationMode.MIXED
    assert len(plan.question_ids) == 4
    assert plan.revision_question_ids == ("old-1", "old-0")
    assert "current-0" not in plan.question_ids
    assert "current-1" not in plan.question_ids
    assert plan.focus_concept_ids == ("science",)
    assert plan.recommended_difficulty is DifficultyLevel.EASY


def test_revision_mode_uses_previous_mistakes():
    previous = make_analysis("s0", "t0", ("old-0", "old-1"))
    history, question_history = make_histories(previous)

    questions = (question("old-0"), question("old-1"), question("new-1"))
    candidates = (
        candidate("old-0", 3, score=0.8),
        candidate("old-1", 2, score=0.7),
        candidate("new-1", 1, score=1.0),
    )

    plan = PersonalizedPreparationService().build_plan(
        "learner",
        test_id="revision-1",
        title="Revision",
        question_count=2,
        duration_seconds=1800,
        history=history,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
        mode=PersonalizedPreparationMode.REVISION,
    )

    assert plan.revision_question_ids == ("old-0", "old-1")
    assert plan.question_ids == ("old-1", "old-0")


def test_weak_topic_mode_falls_back_when_focus_pool_is_small():
    previous = make_analysis("s0", "t0", ("old-0", "old-1"))
    history, question_history = make_histories(previous)

    questions = (question("new-1"), question("new-2", difficulty="MEDIUM"))
    candidates = (
        candidate("new-1", 1, score=0.7),
        candidate("new-2", 2, score=1.0, difficulty=DifficultyLevel.MEDIUM),
    )

    plan = PersonalizedPreparationService().build_plan(
        "learner",
        test_id="weak-1",
        title="Weak Topics",
        question_count=2,
        duration_seconds=600,
        history=history,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
        mode=PersonalizedPreparationMode.WEAK_TOPICS,
    )

    assert plan.question_ids == ("new-1", "new-2")
    assert plan.focus_concept_ids == ("science",)


def test_plan_feeds_phase_67_test_engine_directly():
    previous = make_analysis("s0", "t0", ("old-0",))
    history, question_history = make_histories(previous)

    questions = (question("new-1"), question("new-2"))
    candidates = (
        candidate("new-1", 1, score=1.0),
        candidate("new-2", 2, score=0.9),
    )

    plan = PersonalizedPreparationService().build_plan(
        "learner",
        test_id="adaptive-1",
        title="Adaptive Test",
        question_count=2,
        duration_seconds=1200,
        history=history,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
    )

    engine = TestEngine(clock=lambda: 100.0)
    session = engine.create_session(
        plan.test_specification,
        plan.ranked_candidates,
        questions,
        session_id="personalized-session",
    )
    assert session.question_ids == plan.question_ids


def test_learner_scope_is_enforced():
    previous = make_analysis("s0", "t0", ("old-0",))
    history, question_history = make_histories(previous)

    with pytest.raises(ValueError, match="learner"):
        PersonalizedPreparationService().build_plan(
            "another-learner",
            test_id="x",
            title="x",
            question_count=1,
            duration_seconds=60,
            history=history,
            question_history=question_history,
            candidates=(candidate("q", 1),),
            questions=(question("q"),),
        )


def test_explicit_exclusions_are_honored():
    previous = make_analysis("s0", "t0", ("old-0",))
    history, question_history = make_histories(previous)
    questions = (question("new-1"), question("new-2"))
    candidates = (candidate("new-1", 1), candidate("new-2", 2))

    plan = PersonalizedPreparationService().build_plan(
        "learner",
        test_id="exclude-1",
        title="Excluded",
        question_count=1,
        duration_seconds=300,
        history=history,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
        exclude_question_ids=("new-1",),
    )
    assert plan.question_ids == ("new-2",)
