from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from ai_comp.analysis.adaptive_learning_loop import AdaptiveLearningLoopService
from ai_comp.analysis.adaptive_test_session import AdaptiveTestSessionService
from ai_comp.analysis.completed_test_feedback import CompletedTestFeedbackService
from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.analysis.question_learning import QuestionLearningHistoryService
from ai_comp.domain.adaptive_difficulty import AdaptiveDifficultyProfile
from ai_comp.domain.learning_history import LearnerLearningHistory
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
from ai_comp.domain.question_learning import LearnerQuestionHistory
from ai_comp.domain.test_engine import ScoringPolicy, TestSessionStatus, TestSpecification
from ai_comp.test_engine import TestEngine


class AdaptiveStub:
    def analyze(self, learner_id, learning_history, question_history, *, as_of=None):
        return AdaptiveDifficultyProfile(
            learner_id=learner_id,
            decisions=(),
            recommended_difficulty=DifficultyLevel.MEDIUM,
            retention_due_question_ids=(),
            generated_at=as_of or datetime(2026, 10, 9, tzinfo=timezone.utc),
        )


class LearningRepo:
    def __init__(self):
        self.attempts = {}
        self.topics = {}

    def save_attempt(self, attempt, topics):
        key = (attempt.learner_id, attempt.session_id)
        old = self.attempts.get(key)
        if old is not None and old != attempt:
            raise ValueError("conflicting attempt")
        self.attempts[key] = attempt
        for topic in topics:
            self.topics[(topic.attempt_id, topic.concept_id)] = topic

    def get_attempt(self, learner_id, session_id):
        return self.attempts.get((learner_id, session_id))

    def list_attempts(self, learner_id):
        return tuple(sorted(
            (x for x in self.attempts.values() if x.learner_id == learner_id),
            key=lambda x: (x.completed_at, x.session_id),
        ))

    def list_topic_attempts(self, learner_id):
        ids = {x.attempt_id for x in self.list_attempts(learner_id)}
        return tuple(x for x in self.topics.values() if x.attempt_id in ids)


class QuestionRepo:
    def __init__(self):
        self.outcomes = {}

    def save_outcomes(self, outcomes):
        for row in outcomes:
            old = self.outcomes.get(row.outcome_id)
            if old is not None and old != row:
                raise ValueError("conflicting outcome")
        for row in outcomes:
            self.outcomes[row.outcome_id] = row

    def list_outcomes(self, learner_id):
        return tuple(sorted(
            (x for x in self.outcomes.values() if x.learner_id == learner_id),
            key=lambda x: (x.completed_at, x.session_id, x.question_id),
        ))


def question(qid, concept):
    return GeneratedMCQ(
        generated_question_id=qid, generation_id="g1", material_id="m1",
        stem=f"Question {qid}", options=(
            GeneratedOption("A", "one"), GeneratedOption("B", "two"),
            GeneratedOption("C", "three"), GeneratedOption("D", "four"),
        ), correct_option_key="B", explanation="Verified explanation",
        fact_ids=("f1",), concept_ids=(concept,), difficulty="MEDIUM",
        importance_score=0.9, answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("source",), status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def candidate(qid, rank):
    return RankedQuestionCandidate(
        question_id=qid, rank=rank,
        score=QuestionIntelligenceScore(
            generated_question_id=qid, difficulty=DifficultyLevel.MEDIUM,
            difficulty_score=0.5, importance_score=0.9, novelty_score=1.0,
            coverage_score=0.5, selection_score=1.0 - rank * 0.01,
        ),
    )


def make_completed_feedback():
    past = (question("past-science", "science"), question("past-history", "history"))
    engine = TestEngine(clock=lambda: 100.0)
    spec = TestSpecification(
        test_id="past-test", title="Past", question_count=2, duration_seconds=300,
        scoring=ScoringPolicy(correct_marks=1.0, incorrect_marks=0.0),
    )
    engine.create_session(spec, (candidate("past-science", 1), candidate("past-history", 2)), past, session_id="past-session")
    engine.start("past-session")
    engine.answer("past-session", "A")
    engine.next("past-session")
    engine.answer("past-session", "B")
    engine.submit("past-session")
    learning_repo, question_repo = LearningRepo(), QuestionRepo()
    feedback_service = CompletedTestFeedbackService(
        test_engine=engine,
        learning_history_service=LearningHistoryService(learning_repo),
        question_history_service=QuestionLearningHistoryService(question_repo),
        clock=lambda: datetime(2026, 10, 9, tzinfo=timezone.utc),
    )
    feedback = feedback_service.process_completed_test("learner-1", "past-session", past)
    return feedback, engine


def make_next_inputs():
    questions = tuple(
        question(f"next-{concept}-{i}", concept)
        for concept in ("science", "history", "geography")
        for i in range(1, 3)
    )
    candidates = tuple(candidate(q.generated_question_id, i) for i, q in enumerate(questions, 1))
    return candidates, questions


def test_completed_feedback_drives_next_adaptive_session_and_keeps_timer_stopped():
    feedback, _ = make_completed_feedback()
    candidates, questions = make_next_inputs()
    engine = TestEngine(clock=lambda: 500.0)
    sessions = AdaptiveTestSessionService(
        test_engine=engine,
        composition_service=__import__(
            "ai_comp.analysis.adaptive_test_composition", fromlist=["AdaptiveTestCompositionService"]
        ).AdaptiveTestCompositionService(adaptive_difficulty_service=AdaptiveStub()),
    )
    service = AdaptiveLearningLoopService(adaptive_session_service=sessions)

    result = service.create_next_test(
        "learner-1", completed_feedback=feedback,
        test_id="next-test", title="Personalized follow-up", session_id="next-session",
        question_count=3, duration_seconds=600, candidates=candidates, questions=questions,
        as_of=datetime(2026, 10, 9, tzinfo=timezone.utc),
    )

    assert result.completed_session_id == "past-session"
    assert result.completed_test_percentage == pytest.approx(50.0)
    assert result.next_test.learner_id == "learner-1"
    assert result.next_test.session.status is TestSessionStatus.CREATED
    assert result.next_test.session.started_at is None
    assert result.next_test.session.question_ids == result.next_test.composition_plan.question_ids
    assert result.adaptive_profile.learner_id == "learner-1"


def test_follow_up_rejects_feedback_for_another_learner():
    feedback, _ = make_completed_feedback()
    candidates, questions = make_next_inputs()
    service = AdaptiveLearningLoopService()

    with pytest.raises(ValueError, match="learner does not match"):
        service.create_next_test(
            "learner-2", completed_feedback=feedback,
            test_id="next-test", title="Wrong learner", session_id="next-session",
            question_count=3, duration_seconds=600, candidates=candidates, questions=questions,
        )


def test_follow_up_rejects_unfinished_feedback_snapshot():
    feedback, _ = make_completed_feedback()
    candidates, questions = make_next_inputs()
    invalid_session = replace(feedback.session, status=TestSessionStatus.IN_PROGRESS)
    invalid_feedback = replace(feedback, session=invalid_session)
    service = AdaptiveLearningLoopService()

    with pytest.raises(ValueError, match="completed test"):
        service.create_next_test(
            "learner-1", completed_feedback=invalid_feedback,
            test_id="next-test", title="Unfinished", session_id="next-session",
            question_count=3, duration_seconds=600, candidates=candidates, questions=questions,
        )
