from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.analysis.personalization import (
    LongTermLearningRecommendationService,
    PersonalizedNextTestSelector,
)
from ai_comp.domain.learning_history import LongTermPerformanceBand
from ai_comp.domain.learning_recommendation import RecommendedDifficulty
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
from ai_comp.domain.test_analysis import (
    PerformanceBand,
    QuestionOutcome,
    TestAnalysis,
    TopicPerformance,
    WeakTopic,
)


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
        return tuple(
            sorted(
                (a for a in self.attempts.values() if a.learner_id == learner_id),
                key=lambda a: (a.completed_at, a.session_id),
            )
        )

    def list_topic_attempts(self, learner_id):
        attempt_ids = {a.attempt_id for a in self.list_attempts(learner_id)}
        return tuple(
            t
            for t in self.topics
            if t.learner_id == learner_id and t.attempt_id in attempt_ids
        )


def make_analysis(session_id, test_id, science_accuracy, history_accuracy):
    science_correct = int(science_accuracy * 4)
    history_correct = int(history_accuracy * 4)
    outcomes = tuple(
        QuestionOutcome(
            question_id=f"q-{index}",
            concept_ids=("science" if index < 4 else "history",),
            selected_option_key=(
                "B"
                if (
                    index < 4 and index < science_correct
                    or index >= 4 and index - 4 < history_correct
                )
                else "A"
            ),
            correct_option_key="B",
            attempted=True,
            correct=(
                index < 4 and index < science_correct
                or index >= 4 and index - 4 < history_correct
            ),
            difficulty="MEDIUM",
        )
        for index in range(8)
    )
    topic_specs = (
        ("science", science_accuracy),
        ("history", history_accuracy),
    )
    topic_performance = tuple(
        TopicPerformance(
            concept_id=concept,
            question_count=4,
            attempted_count=4,
            correct_count=int(accuracy * 4),
            incorrect_count=4 - int(accuracy * 4),
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
        for concept, accuracy in topic_specs
    )
    weak_topics = tuple(
        WeakTopic(
            concept_id=concept,
            priority_score=1.0 - accuracy,
            accuracy=accuracy,
            attempted_count=4,
            question_count=4,
            reason="कम accuracy",
        )
        for concept, accuracy in topic_specs
        if accuracy < 0.5
    )
    return TestAnalysis(
        test_id=test_id,
        session_id=session_id,
        total_questions=8,
        attempted_questions=8,
        correct_answers=(
            int(science_accuracy * 4) + int(history_accuracy * 4)
        ),
        incorrect_answers=(
            8 - int(science_accuracy * 4) - int(history_accuracy * 4)
        ),
        unattempted_questions=0,
        raw_score=float(
            int(science_accuracy * 4)
            + int(history_accuracy * 4)
            - 0.25 * (8 - int(science_accuracy * 4) - int(history_accuracy * 4))
        ),
        percentage=0.0,
        accuracy=(
            int(science_accuracy * 4) + int(history_accuracy * 4)
        ) / 8.0,
        outcomes=outcomes,
        topic_performance=topic_performance,
        weak_topics=weak_topics,
    )


def q(qid, concept, difficulty="EASY"):
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
        concept_ids=(concept,),
        difficulty=difficulty,
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("source",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def cand(qid, rank, difficulty=DifficultyLevel.EASY, score=0.8):
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


def test_history_aggregates_multiple_tests():
    repo = InMemoryLearningHistoryRepository()
    service = LearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.record_analysis(
        "learner-1",
        make_analysis("s1", "t1", 0.0, 1.0),
        completed_at=t0,
    )
    service.record_analysis(
        "learner-1",
        make_analysis("s2", "t2", 0.5, 0.5),
        completed_at=t0 + timedelta(days=1),
    )
    history = service.history("learner-1", generated_at=t0)
    science = next(
        item for item in history.topic_performance if item.concept_id == "science"
    )
    assert science.test_count == 2
    assert science.accuracy == pytest.approx(0.25)
    assert science.recent_accuracy == 0.5
    assert science.trend.name == "IMPROVING"
    assert science.weak_streak == 2
    assert science.performance is LongTermPerformanceBand.WEAK


def test_long_term_recommendations_prefer_persistent_weak_topic():
    repo = InMemoryLearningHistoryRepository()
    service = LearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.record_analysis(
        "learner-1",
        make_analysis("s1", "t1", 0.0, 1.0),
        completed_at=t0,
    )
    service.record_analysis(
        "learner-1",
        make_analysis("s2", "t2", 0.25, 1.0),
        completed_at=t0 + timedelta(days=1),
    )
    history = service.history("learner-1", generated_at=t0)
    recommendations = LongTermLearningRecommendationService().recommend(history)
    assert recommendations[0].concept_id == "science"
    assert recommendations[0].recommended_difficulty is RecommendedDifficulty.MEDIUM


def test_personalized_selector_uses_persistent_history():
    repo = InMemoryLearningHistoryRepository()
    service = LearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.record_analysis(
        "learner-1",
        make_analysis("s1", "t1", 0.0, 1.0),
        completed_at=t0,
    )
    service.record_analysis(
        "learner-1",
        make_analysis("s2", "t2", 0.25, 1.0),
        completed_at=t0 + timedelta(days=1),
    )
    history = service.history("learner-1", generated_at=t0)
    current = make_analysis("s3", "t3", 1.0, 0.0)
    questions = (
        q("science-1", "science"),
        q("history-1", "history"),
        q("science-2", "science"),
    )
    candidates = (
        cand("science-1", 1),
        cand("history-1", 2),
        cand("science-2", 3),
    )
    plan = PersonalizedNextTestSelector().select(
        history, current, candidates, questions, question_count=2
    )
    assert plan.focus_concept_ids == ("science",)
    assert plan.question_ids[0] == "science-1"


def test_different_learner_histories_are_isolated():
    repo = InMemoryLearningHistoryRepository()
    service = LearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.record_analysis(
        "learner-a",
        make_analysis("s1", "t1", 0.0, 1.0),
        completed_at=t0,
    )
    service.record_analysis(
        "learner-b",
        make_analysis("s2", "t2", 1.0, 0.0),
        completed_at=t0,
    )
    assert (
        service.history("learner-a").topic_performance[0].concept_id
        == "science"
    )
    assert (
        service.history("learner-b").topic_performance[0].concept_id
        == "history"
    )
