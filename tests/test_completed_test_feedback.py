from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ai_comp.analysis.completed_test_feedback import CompletedTestFeedbackService
from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.analysis.question_learning import QuestionLearningHistoryService
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
from ai_comp.domain.test_engine import (
    ScoringPolicy,
    TestSessionStatus,
    TestSpecification,
)
from ai_comp.test_engine import TestEngine


class InMemoryLearningRepository:
    def __init__(self):
        self.attempts = {}
        self.topics = {}

    def save_attempt(self, attempt, topics):
        key = (attempt.learner_id, attempt.session_id)
        existing = self.attempts.get(key)
        if existing is not None:
            if existing != attempt:
                raise ValueError("conflicting attempt")
            existing_topics = {
                (row.attempt_id, row.concept_id): row
                for row in self.topics.values()
                if row.attempt_id == attempt.attempt_id
            }
            expected_topics = {
                (row.attempt_id, row.concept_id): row for row in topics
            }
            if existing_topics != expected_topics:
                raise ValueError("conflicting topic snapshot")
            return
        self.attempts[key] = attempt
        for topic in topics:
            self.topics[(topic.attempt_id, topic.concept_id)] = topic

    def get_attempt(self, learner_id, session_id):
        return self.attempts.get((learner_id, session_id))

    def list_attempts(self, learner_id):
        return tuple(
            sorted(
                (row for row in self.attempts.values() if row.learner_id == learner_id),
                key=lambda row: (row.completed_at, row.session_id),
            )
        )

    def list_topic_attempts(self, learner_id):
        attempt_ids = {row.attempt_id for row in self.list_attempts(learner_id)}
        return tuple(
            row for row in self.topics.values()
            if row.learner_id == learner_id and row.attempt_id in attempt_ids
        )


class InMemoryQuestionRepository:
    def __init__(self, *, fail_once: bool = False):
        self.outcomes = {}
        self.fail_once = fail_once

    def save_outcomes(self, outcomes):
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("temporary question-history failure")
        for row in outcomes:
            existing = self.outcomes.get(row.outcome_id)
            if existing is not None and existing != row:
                raise ValueError("conflicting question outcome")
        for row in outcomes:
            self.outcomes[row.outcome_id] = row

    def list_outcomes(self, learner_id):
        return tuple(
            sorted(
                (row for row in self.outcomes.values() if row.learner_id == learner_id),
                key=lambda row: (row.completed_at, row.session_id, row.question_id),
            )
        )


class MutableDateTimeClock:
    def __init__(self):
        self.value = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.value


def make_question(question_id, concept_id):
    return GeneratedMCQ(
        generated_question_id=question_id,
        generation_id="generation-1",
        material_id="material-1",
        stem=f"Question about {concept_id}",
        options=(
            GeneratedOption("A", "Option one"),
            GeneratedOption("B", "Option two"),
            GeneratedOption("C", "Option three"),
            GeneratedOption("D", "Option four"),
        ),
        correct_option_key="B",
        explanation="Supported by the supplied evidence.",
        fact_ids=("fact-1",),
        concept_ids=(concept_id,),
        difficulty="MEDIUM",
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("verified source",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def make_candidate(question_id, rank):
    return RankedQuestionCandidate(
        question_id=question_id,
        rank=rank,
        score=QuestionIntelligenceScore(
            generated_question_id=question_id,
            difficulty=DifficultyLevel.MEDIUM,
            difficulty_score=0.55,
            importance_score=0.9,
            novelty_score=1.0,
            coverage_score=0.5,
            selection_score=1.0 - rank * 0.01,
        ),
    )


def make_pipeline(*, fail_question_history_once=False):
    questions = (
        make_question("q-history", "history"),
        make_question("q-science-wrong", "science"),
        make_question("q-science-unattempted", "science"),
    )
    engine = TestEngine(clock=lambda: 100.0)
    specification = TestSpecification(
        test_id="test-phase-6-16",
        title="End-to-end feedback",
        question_count=len(questions),
        duration_seconds=600,
        scoring=ScoringPolicy(correct_marks=1.0, incorrect_marks=-0.25),
    )
    engine.create_session(
        specification,
        tuple(
            make_candidate(question.generated_question_id, rank)
            for rank, question in enumerate(questions, start=1)
        ),
        questions,
        session_id="session-phase-6-16",
    )
    engine.start("session-phase-6-16")
    engine.answer("session-phase-6-16", "B")
    engine.next("session-phase-6-16")
    engine.answer("session-phase-6-16", "A")
    engine.next("session-phase-6-16")
    result = engine.submit("session-phase-6-16")
    assert result.status is TestSessionStatus.SUBMITTED

    learning_repo = InMemoryLearningRepository()
    question_repo = InMemoryQuestionRepository(fail_once=fail_question_history_once)
    clock = MutableDateTimeClock()
    service = CompletedTestFeedbackService(
        test_engine=engine,
        learning_history_service=LearningHistoryService(learning_repo),
        question_history_service=QuestionLearningHistoryService(question_repo),
        clock=clock,
    )
    return service, engine, questions, learning_repo, question_repo, clock


def test_completed_result_flows_into_weak_topics_and_both_histories():
    service, _, questions, learning_repo, question_repo, _ = make_pipeline()

    feedback = service.process_completed_test(
        "learner-1", "session-phase-6-16", questions
    )

    assert feedback.result.correct_answers == 1
    assert feedback.result.incorrect_answers == 1
    assert feedback.result.unattempted_questions == 1
    assert feedback.result.raw_score == pytest.approx(0.75)
    assert feedback.result.percentage == pytest.approx(25.0)
    assert feedback.analysis.weak_topics[0].concept_id == "science"
    assert feedback.analysis.weak_topics[0].accuracy == 0.0
    assert feedback.attempt.session_id == feedback.session.session_id
    assert len(feedback.learning_history.attempts) == 1
    science = next(
        row for row in feedback.learning_history.topic_performance
        if row.concept_id == "science"
    )
    assert science.performance.value == "WEAK"
    assert science.question_count == 2
    assert science.incorrect_count == 1
    assert science.unattempted_count == 1
    assert len(feedback.question_history.outcomes) == 3
    assert len(feedback.question_history.revision_candidates) == 1
    assert feedback.question_history.revision_candidates[0].question_id == "q-science-wrong"
    assert len(learning_repo.attempts) == 1
    assert len(question_repo.outcomes) == 3


def test_processing_same_completed_session_is_idempotent():
    service, _, questions, learning_repo, question_repo, _ = make_pipeline()

    first = service.process_completed_test(
        "learner-1", "session-phase-6-16", questions
    )
    second = service.process_completed_test(
        "learner-1", "session-phase-6-16", questions
    )

    assert first.attempt == second.attempt
    assert first.attempt.completed_at == second.attempt.completed_at
    assert len(learning_repo.attempts) == 1
    assert len(learning_repo.topics) == 2
    assert len(question_repo.outcomes) == len(questions)
    assert len(second.learning_history.attempts) == 1
    assert len(second.question_history.outcomes) == len(questions)


def test_processing_is_rejected_before_a_session_is_finished():
    service, engine, questions, learning_repo, question_repo, _ = make_pipeline()
    engine.create_session(
        TestSpecification(
            test_id="not-finished",
            title="Not finished",
            question_count=1,
            duration_seconds=60,
        ),
        (make_candidate("q-not-finished", 1),),
        (make_question("q-not-finished", "science"),),
        session_id="session-not-finished",
    )

    with pytest.raises(ValueError, match="finished"):
        service.process_completed_test(
            "learner-1",
            "session-not-finished",
            (make_question("q-not-finished", "science"),),
        )
    assert not learning_repo.attempts
    assert not question_repo.outcomes


def test_question_set_is_validated_before_any_history_is_written():
    service, _, questions, learning_repo, question_repo, _ = make_pipeline()

    with pytest.raises(ValueError, match="exactly match"):
        service.process_completed_test(
            "learner-1", "session-phase-6-16", questions[:-1]
        )
    assert not learning_repo.attempts
    assert not question_repo.outcomes


def test_retry_after_question_history_failure_reuses_persisted_timestamp():
    service, _, questions, learning_repo, question_repo, clock = make_pipeline(
        fail_question_history_once=True
    )

    with pytest.raises(RuntimeError, match="temporary"):
        service.process_completed_test(
            "learner-1", "session-phase-6-16", questions
        )
    first_timestamp = next(iter(learning_repo.attempts.values())).completed_at
    assert len(learning_repo.attempts) == 1
    assert not question_repo.outcomes

    clock.value = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
    feedback = service.process_completed_test(
        "learner-1", "session-phase-6-16", questions
    )

    assert feedback.attempt.completed_at == first_timestamp
    assert len(learning_repo.attempts) == 1
    assert len(question_repo.outcomes) == len(questions)
    assert all(
        row.completed_at == first_timestamp
        for row in question_repo.outcomes.values()
    )


def test_stored_result_identity_must_match_its_session():
    service, engine, questions, learning_repo, question_repo, _ = make_pipeline()
    session = engine.get_session("session-phase-6-16")
    invalid_result = session.result
    assert invalid_result is not None
    from dataclasses import replace

    corrupted = replace(
        session,
        result=replace(invalid_result, session_id="other-session"),
    )
    engine.repository.save(corrupted)

    with pytest.raises(ValueError, match="does not match"):
        service.process_completed_test(
            "learner-1", "session-phase-6-16", questions
        )
    assert not learning_repo.attempts
    assert not question_repo.outcomes


def test_unaccepted_question_cannot_be_written_to_learning_history():
    service, _, questions, learning_repo, question_repo, _ = make_pipeline()
    from dataclasses import replace

    rejected = replace(
        questions[-1],
        status=GeneratedQuestionStatus.REJECTED,
        quality_score=0.0,
    )
    bad_questions = questions[:-1] + (rejected,)

    with pytest.raises(ValueError, match="accepted"):
        service.process_completed_test(
            "learner-1", "session-phase-6-16", bad_questions
        )
    assert not learning_repo.attempts
    assert not question_repo.outcomes
