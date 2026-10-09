from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from ai_comp.analysis.adaptive_test_composition import AdaptiveTestCompositionService
from ai_comp.analysis.adaptive_test_session import AdaptiveTestSessionService
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
from ai_comp.domain.test_engine import TestSessionStatus
from ai_comp.test_engine import TestEngine


class AdaptiveStub:
    def analyze(self, learner_id, learning_history, question_history, **kwargs):
        return AdaptiveDifficultyProfile(
            learner_id=learner_id,
            decisions=(),
            recommended_difficulty=DifficultyLevel.MEDIUM,
            retention_due_question_ids=(),
            generated_at=kwargs.get("as_of") or datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def make_histories():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return (
        LearnerLearningHistory(
            learner_id="learner-1",
            attempts=(),
            topic_performance=(),
            generated_at=now,
        ),
        LearnerQuestionHistory(
            learner_id="learner-1",
            outcomes=(),
            question_performance=(),
            revision_candidates=(),
            repeated_concept_alerts=(),
            generated_at=now,
        ),
    )


def make_question(question_id: str, concept_id: str):
    return GeneratedMCQ(
        generated_question_id=question_id,
        generation_id="generation-1",
        material_id="material-1",
        stem=f"Question {question_id}?",
        options=(
            GeneratedOption("A", "One"),
            GeneratedOption("B", "Two"),
            GeneratedOption("C", "Three"),
            GeneratedOption("D", "Four"),
        ),
        correct_option_key="B",
        explanation="Supported by source evidence.",
        fact_ids=("fact-1",),
        concept_ids=(concept_id,),
        difficulty="MEDIUM",
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("source evidence",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def make_candidate(question_id: str, rank: int):
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
            selection_score=1.0 - (rank * 0.01),
        ),
    )


def make_service():
    engine = TestEngine(clock=lambda: 100.0)
    composer = AdaptiveTestCompositionService(
        adaptive_difficulty_service=AdaptiveStub()
    )
    return AdaptiveTestSessionService(
        composition_service=composer,
        test_engine=engine,
    )


def test_composition_creates_ready_to_start_test_session():
    history, question_history = make_histories()
    questions = (
        make_question("q-science-1", "science"),
        make_question("q-history-1", "history"),
        make_question("q-science-2", "science"),
        make_question("q-history-2", "history"),
    )
    candidates = tuple(
        make_candidate(question.generated_question_id, rank)
        for rank, question in enumerate(questions, start=1)
    )
    service = make_service()

    result = service.create_session(
        "learner-1",
        test_id="adaptive-test-1",
        title="Adaptive Practice",
        session_id="session-1",
        question_count=2,
        duration_seconds=600,
        learning_history=history,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
    )

    assert result.session.status is TestSessionStatus.CREATED
    assert result.session.session_id == "session-1"
    assert result.session.test_id == "adaptive-test-1"
    assert result.specification.question_count == 2
    assert result.session.question_ids == result.composition_plan.question_ids
    assert len(result.composition_plan.coverage) == 2
    assert result.session.started_at is None
    assert result.session.deadline_at is None


def test_session_timer_starts_only_when_start_is_called():
    history, question_history = make_histories()
    questions = (
        make_question("q1", "science"),
        make_question("q2", "history"),
    )
    candidates = (
        make_candidate("q1", 1),
        make_candidate("q2", 2),
    )
    service = make_service()

    created = service.create_session(
        "learner-1",
        test_id="adaptive-test-2",
        title="Timed Practice",
        session_id="session-2",
        question_count=2,
        duration_seconds=300,
        learning_history=history,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
    )
    started = service.start(created.session.session_id)

    assert started.status is TestSessionStatus.IN_PROGRESS
    assert started.started_at == 100.0
    assert started.deadline_at == 400.0


def test_excluded_and_insufficient_candidate_pool_fail_closed():
    history, question_history = make_histories()
    questions = (make_question("q1", "science"), make_question("q2", "history"))
    candidates = (make_candidate("q1", 1), make_candidate("q2", 2))
    service = make_service()

    with pytest.raises(ValueError, match="not enough accepted ranked questions"):
        service.create_session(
            "learner-1",
            test_id="adaptive-test-3",
            title="Insufficient Pool",
            session_id="session-3",
            question_count=2,
            duration_seconds=300,
            learning_history=history,
            question_history=question_history,
            candidates=candidates,
            questions=questions,
            exclude_question_ids=("q1",),
        )


def test_duplicate_session_id_is_rejected():
    history, question_history = make_histories()
    questions = (make_question("q1", "science"), make_question("q2", "history"))
    candidates = (make_candidate("q1", 1), make_candidate("q2", 2))
    service = make_service()

    kwargs = dict(
        learner_id="learner-1",
        test_id="adaptive-test-4",
        title="Duplicate Guard",
        session_id="session-4",
        question_count=2,
        duration_seconds=300,
        learning_history=history,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
    )
    service.create_session(**kwargs)
    with pytest.raises(ValueError, match="already exists"):
        service.create_session(**kwargs)


def test_unselected_rejected_question_does_not_block_session():
    history, question_history = make_histories()
    selected = (
        make_question("q1", "science"),
        make_question("q2", "history"),
    )
    rejected = replace(
        make_question("not-selected", "science"),
        status=GeneratedQuestionStatus.REJECTED,
        quality_score=0.0,
    )
    service = make_service()

    result = service.create_session(
        "learner-1",
        test_id="adaptive-test-5",
        title="Selected Questions Only",
        session_id="session-5",
        question_count=2,
        duration_seconds=300,
        learning_history=history,
        question_history=question_history,
        candidates=(
            make_candidate("q1", 1),
            make_candidate("q2", 2),
        ),
        questions=selected + (rejected,),
    )

    assert set(result.session.question_ids) == {"q1", "q2"}
