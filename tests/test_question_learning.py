from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai_comp.analysis.question_learning import (
    PersonalizedQuestionRecommendationService,
    QuestionLearningHistoryService,
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
from ai_comp.domain.question_learning import QuestionOutcomeKind
from ai_comp.domain.test_analysis import (
    PerformanceBand,
    QuestionOutcome,
    TestAnalysis,
    TopicPerformance,
    WeakTopic,
)


class InMemoryQuestionHistoryRepository:
    def __init__(self):
        self.rows = {}

    def save_outcomes(self, outcomes):
        for outcome in outcomes:
            existing = self.rows.get(outcome.outcome_id)
            if existing is not None and existing != outcome:
                raise ValueError("conflict")
            self.rows[outcome.outcome_id] = outcome

    def list_outcomes(self, learner_id):
        return tuple(
            sorted(
                (row for row in self.rows.values() if row.learner_id == learner_id),
                key=lambda row: (row.completed_at, row.session_id, row.question_id),
            )
        )


def make_analysis(session_id: str, science_results: tuple[bool, bool], t: datetime):
    outcomes = []
    for index, correct in enumerate(science_results, start=1):
        outcomes.append(
            QuestionOutcome(
                question_id=f"q{index}",
                concept_ids=("science",),
                selected_option_key="B" if correct else "A",
                correct_option_key="B",
                attempted=True,
                correct=correct,
                difficulty="EASY",
            )
        )
    correct_count = sum(science_results)
    topic = TopicPerformance(
        concept_id="science",
        question_count=2,
        attempted_count=2,
        correct_count=correct_count,
        incorrect_count=2 - correct_count,
        unattempted_count=0,
        accuracy=correct_count / 2.0,
        performance=(
            PerformanceBand.WEAK
            if correct_count / 2.0 < 0.5
            else PerformanceBand.AVERAGE
            if correct_count / 2.0 < 0.75
            else PerformanceBand.STRONG
        ),
    )
    weak = (
        WeakTopic(
            concept_id="science",
            priority_score=1.0 - topic.accuracy,
            accuracy=topic.accuracy,
            attempted_count=2,
            question_count=2,
            reason="weak",
        ),
    ) if topic.accuracy < 0.5 else ()
    return TestAnalysis(
        test_id=f"t-{session_id}",
        session_id=session_id,
        total_questions=2,
        attempted_questions=2,
        correct_answers=correct_count,
        incorrect_answers=2 - correct_count,
        unattempted_questions=0,
        raw_score=float(correct_count),
        percentage=correct_count * 50.0,
        accuracy=correct_count / 2.0,
        outcomes=tuple(outcomes),
        topic_performance=(topic,),
        weak_topics=weak,
    )


def question(qid: str):
    return GeneratedMCQ(
        generated_question_id=qid,
        generation_id="g",
        material_id="m",
        stem=qid,
        options=(
            GeneratedOption("A", "एक"),
            GeneratedOption("B", "दो"),
            GeneratedOption("C", "तीन"),
            GeneratedOption("D", "चार"),
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


def candidate(qid: str, rank: int, selection_score: float = 0.8):
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
            selection_score=selection_score,
        ),
    )


def test_question_history_persists_previous_mistake_and_is_idempotent():
    repo = InMemoryQuestionHistoryRepository()
    service = QuestionLearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    analysis = make_analysis("s1", (False, True), t0)
    service.record_analysis("learner", analysis, completed_at=t0)
    service.record_analysis("learner", analysis, completed_at=t0)

    history = service.history("learner", generated_at=t0)
    assert len(history.outcomes) == 2
    assert history.revision_candidates[0].question_id == "q1"
    assert history.revision_candidates[0].mistake_count == 1
    q1 = next(item for item in history.question_performance if item.question_id == "q1")
    assert q1.last_outcome is QuestionOutcomeKind.INCORRECT
    assert q1.accuracy == 0.0


def test_repeated_weak_concept_creates_alert():
    repo = InMemoryQuestionHistoryRepository()
    service = QuestionLearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.record_analysis("learner", make_analysis("s1", (False, False), t0), completed_at=t0)
    service.record_analysis(
        "learner",
        make_analysis("s2", (False, True), t0 + timedelta(days=1)),
        completed_at=t0 + timedelta(days=1),
    )
    history = service.history("learner", generated_at=t0)
    assert history.repeated_concept_alerts[0].concept_id == "science"
    assert history.repeated_concept_alerts[0].test_count == 2
    assert history.repeated_concept_alerts[0].weak_test_count == 2


def test_personalized_recommendation_prefers_previous_mistake():
    repo = InMemoryQuestionHistoryRepository()
    history_service = QuestionLearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    history_service.record_analysis("learner", make_analysis("s1", (False, True), t0), completed_at=t0)
    history = history_service.history("learner", generated_at=t0)

    questions = (question("q1"), question("q2"))
    candidates = (candidate("q2", 1, 1.0), candidate("q1", 2, 0.5))
    plan = PersonalizedQuestionRecommendationService().recommend(
        history,
        candidates,
        questions,
        question_count=2,
    )
    assert plan.revision_question_ids == ("q1",)
    assert plan.question_ids == ("q1", "q2")


def test_revision_only_prioritizes_mistakes_and_excludes_current_questions():
    repo = InMemoryQuestionHistoryRepository()
    history_service = QuestionLearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    history_service.record_analysis("learner", make_analysis("s1", (False, False), t0), completed_at=t0)
    history = history_service.history("learner", generated_at=t0)

    questions = (question("q1"), question("q2"))
    candidates = (candidate("q2", 2), candidate("q1", 1))
    plan = PersonalizedQuestionRecommendationService().recommend(
        history,
        candidates,
        questions,
        question_count=1,
        revision_only=True,
        exclude_question_ids=("q1",),
    )
    assert plan.question_ids == ("q2",)


def test_question_history_is_learner_scoped():
    repo = InMemoryQuestionHistoryRepository()
    service = QuestionLearningHistoryService(repo)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    service.record_analysis("learner-a", make_analysis("s1", (False, True), t0), completed_at=t0)
    service.record_analysis("learner-b", make_analysis("s2", (True, True), t0), completed_at=t0)
    history_a = service.history("learner-a", generated_at=t0)
    history_b = service.history("learner-b", generated_at=t0)
    assert len(history_a.revision_candidates) == 1
    assert not history_b.revision_candidates
