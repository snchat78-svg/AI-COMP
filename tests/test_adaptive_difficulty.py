from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ai_comp.analysis.adaptive_difficulty import AdaptiveDifficultyService
from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.analysis.question_learning import QuestionLearningHistoryService
from ai_comp.domain.adaptive_difficulty import AdaptiveAction, MasteryStatus
from ai_comp.domain.test_analysis import (
    PerformanceBand,
    QuestionOutcome,
    TestAnalysis,
    TopicPerformance,
    WeakTopic,
)


class LearningRepo:
    def __init__(self):
        self.attempts = {}
        self.topics = []

    def save_attempt(self, attempt, topics):
        self.attempts[(attempt.learner_id, attempt.session_id)] = attempt
        self.topics = [
            topic
            for topic in self.topics
            if topic.attempt_id != attempt.attempt_id
        ]
        self.topics.extend(topics)

    def get_attempt(self, learner_id, session_id):
        return self.attempts.get((learner_id, session_id))

    def list_attempts(self, learner_id):
        return tuple(
            sorted(
                (
                    item
                    for item in self.attempts.values()
                    if item.learner_id == learner_id
                ),
                key=lambda item: (item.completed_at, item.session_id),
            )
        )

    def list_topic_attempts(self, learner_id):
        return tuple(
            sorted(
                (
                    item
                    for item in self.topics
                    if item.learner_id == learner_id
                ),
                key=lambda item: (item.session_id, item.concept_id),
            )
        )


class QuestionRepo:
    def __init__(self):
        self.rows = {}

    def save_outcomes(self, outcomes):
        self.rows.update({item.outcome_id: item for item in outcomes})

    def list_outcomes(self, learner_id):
        return tuple(
            sorted(
                (
                    item
                    for item in self.rows.values()
                    if item.learner_id == learner_id
                ),
                key=lambda item: (
                    item.completed_at,
                    item.session_id,
                    item.question_id,
                ),
            )
        )


def make_analysis(session_id: str, correct: bool, question_id: str) -> TestAnalysis:
    accuracy = 1.0 if correct else 0.0
    return TestAnalysis(
        test_id=f"test-{session_id}",
        session_id=session_id,
        total_questions=1,
        attempted_questions=1,
        correct_answers=int(correct),
        incorrect_answers=int(not correct),
        unattempted_questions=0,
        raw_score=float(correct),
        percentage=accuracy * 100.0,
        accuracy=accuracy,
        outcomes=(
            QuestionOutcome(
                question_id=question_id,
                concept_ids=("science",),
                selected_option_key="B" if correct else "A",
                correct_option_key="B",
                attempted=True,
                correct=correct,
                difficulty="MEDIUM",
            ),
        ),
        topic_performance=(
            TopicPerformance(
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
            ),
        ),
        weak_topics=(
            WeakTopic(
                concept_id="science",
                priority_score=1.0 - accuracy,
                accuracy=accuracy,
                attempted_count=1,
                question_count=1,
                reason="weak",
            ),
        )
        if not correct
        else (),
    )


def build_histories(results: tuple[bool, ...]):
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    learning_repo = LearningRepo()
    learning = LearningHistoryService(learning_repo)
    question_repo = QuestionRepo()
    questions = QuestionLearningHistoryService(question_repo)

    for index, correct in enumerate(results):
        analysis = make_analysis(
            f"s{index}",
            correct,
            f"q{index}",
        )
        completed = t0 + timedelta(days=index)
        learning.record_analysis(
            "learner",
            analysis,
            completed_at=completed,
        )
        questions.record_analysis(
            "learner",
            analysis,
            completed_at=completed,
        )

    generated_at = t0 + timedelta(days=30)
    return (
        learning.history("learner", generated_at=generated_at),
        questions.history("learner", generated_at=generated_at),
    )


def test_insufficient_history_defaults_to_medium():
    history, question_history = build_histories((True,))
    profile = AdaptiveDifficultyService().analyze(
        "learner",
        history,
        question_history,
        as_of=history.generated_at,
    )
    decision = profile.decisions[0]
    assert decision.mastery is MasteryStatus.INSUFFICIENT_DATA
    assert decision.action is AdaptiveAction.STABILIZE
    assert decision.recommended_difficulty.value == "MEDIUM"
    assert profile.recommended_difficulty.value == "MEDIUM"


def test_persistent_weakness_drives_easy_remediation():
    history, question_history = build_histories((False, False))
    profile = AdaptiveDifficultyService().analyze(
        "learner",
        history,
        question_history,
        as_of=history.generated_at,
    )
    decision = profile.decisions[0]
    assert decision.mastery is MasteryStatus.LEARNING
    assert decision.action is AdaptiveAction.REMEDIATE
    assert decision.recommended_difficulty.value == "EASY"
    assert profile.recommended_difficulty.value == "EASY"


def test_repeated_strong_performance_advances_to_hard():
    history, question_history = build_histories((True, True, True))
    profile = AdaptiveDifficultyService().analyze(
        "learner",
        history,
        question_history,
        as_of=datetime(2026, 1, 9, tzinfo=timezone.utc),
    )
    decision = profile.decisions[0]
    assert decision.mastery is MasteryStatus.MASTERED
    assert decision.action is AdaptiveAction.ADVANCE
    assert decision.recommended_difficulty.value == "HARD"
    assert profile.recommended_difficulty.value == "HARD"


def test_mastered_topic_with_due_review_is_retention_due():
    history, question_history = build_histories((True, True, True))
    profile = AdaptiveDifficultyService().analyze(
        "learner",
        history,
        question_history,
        as_of=datetime(2026, 2, 9, tzinfo=timezone.utc),
    )
    decision = profile.decisions[0]
    assert decision.mastery is MasteryStatus.RETENTION_DUE
    assert decision.action is AdaptiveAction.RETAIN
    assert decision.recommended_difficulty.value == "MEDIUM"
    assert profile.recommended_difficulty.value == "MEDIUM"
    assert profile.retention_due_question_ids


def test_declining_topic_is_not_advanced():
    history, question_history = build_histories((True, True, False))
    profile = AdaptiveDifficultyService().analyze(
        "learner",
        history,
        question_history,
        as_of=history.generated_at + timedelta(days=1),
    )
    decision = profile.decisions[0]
    assert decision.recommended_difficulty.value == "EASY"
    assert decision.mastery is MasteryStatus.LEARNING
    assert decision.action is AdaptiveAction.REMEDIATE
