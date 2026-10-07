from __future__ import annotations

import pytest

from ai_comp.domain.material_generation import (
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


class FakeClock:
    def __init__(self, value: float = 1000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


def question(question_id: str, correct: str = "B", status=GeneratedQuestionStatus.ACCEPTED):
    return GeneratedMCQ(
        generated_question_id=question_id,
        generation_id="generation:test",
        material_id="material:test",
        stem=f"प्रश्न {question_id}?",
        options=(
            GeneratedOption("A", "एक"),
            GeneratedOption("B", "दो"),
            GeneratedOption("C", "तीन"),
            GeneratedOption("D", "चार"),
        ),
        correct_option_key=correct,
        explanation="स्रोत तथ्य द्वारा समर्थित।",
        fact_ids=("fact-1",),
        concept_ids=("concept-1",),
        difficulty="MEDIUM",
        importance_score=0.90,
        status=status,
        quality_score=0.95,
    )


def candidate(question_id: str, rank: int) -> RankedQuestionCandidate:
    score = QuestionIntelligenceScore(
        generated_question_id=question_id,
        difficulty=DifficultyLevel.MEDIUM,
        difficulty_score=0.55,
        importance_score=0.90,
        novelty_score=1.0,
        coverage_score=0.5,
        selection_score=0.90,
    )
    return RankedQuestionCandidate(question_id=question_id, score=score, rank=rank)


def make_engine():
    return TestEngine(clock=FakeClock())


def make_test(shuffle=False):
    return TestSpecification(
        test_id="test:1",
        title="प्रैक्टिस टेस्ट",
        question_count=3,
        duration_seconds=60,
        scoring=ScoringPolicy(correct_marks=1.0, incorrect_marks=-0.25),
        shuffle_questions=shuffle,
        shuffle_seed=42 if shuffle else None,
    )


def setup_session(engine, specification=None):
    specification = specification or make_test()
    questions = tuple(question(f"q-{i}") for i in range(1, 5))
    candidates = tuple(candidate(f"q-{i}", i) for i in range(1, 5))
    return engine.create_session(
        specification,
        candidates,
        questions,
        session_id="session:1",
    )


def test_session_selects_top_ranked_candidates():
    engine = make_engine()
    session = setup_session(engine)
    assert session.question_ids == ("q-1", "q-2", "q-3")


def test_shuffle_is_deterministic_for_same_seed():
    first = setup_session(make_engine(), make_test(shuffle=True))
    second = setup_session(make_engine(), make_test(shuffle=True))
    assert first.question_ids == second.question_ids
    assert first.question_ids != ("q-1", "q-2", "q-3")


def test_only_accepted_generated_questions_can_enter_test():
    engine = make_engine()
    specification = TestSpecification(
        test_id="test:accepted",
        title="टेस्ट",
        question_count=1,
        duration_seconds=60,
    )
    with pytest.raises(ValueError, match="accepted"):
        engine.create_session(
            specification,
            (candidate("q-1", 1),),
            (question("q-1", status=GeneratedQuestionStatus.REJECTED),),
            session_id="session:accepted",
        )


def test_start_sets_deadline_and_answer_navigation():
    clock = FakeClock()
    engine = TestEngine(clock=clock)
    session = setup_session(engine)
    started = engine.start(session.session_id)
    assert started.status is TestSessionStatus.IN_PROGRESS
    assert started.deadline_at == 1060.0

    engine.answer(session.session_id, "b")
    moved = engine.next(session.session_id)
    assert moved.current_index == 1
    back = engine.previous(session.session_id)
    assert back.current_index == 0


def test_invalid_option_is_rejected():
    engine = make_engine()
    session = setup_session(engine)
    engine.start(session.session_id)
    with pytest.raises(ValueError, match="not valid"):
        engine.answer(session.session_id, "Z")


def test_goto_and_review_toggle():
    engine = make_engine()
    session = setup_session(engine)
    engine.start(session.session_id)
    moved = engine.goto(session.session_id, 3)
    assert moved.current_index == 2
    reviewed = engine.toggle_review(session.session_id)
    assert reviewed.review_question_ids == ("q-3",)
    unreviewed = engine.toggle_review(session.session_id)
    assert unreviewed.review_question_ids == ()


def test_submit_scores_correct_incorrect_and_unattempted():
    clock = FakeClock()
    engine = TestEngine(clock=clock)
    session = setup_session(engine)
    engine.start(session.session_id)

    engine.answer(session.session_id, "B")
    engine.next(session.session_id)
    engine.answer(session.session_id, "A")

    result = engine.submit(session.session_id)
    assert result.status is TestSessionStatus.SUBMITTED
    assert result.total_questions == 3
    assert result.attempted_questions == 2
    assert result.correct_answers == 1
    assert result.incorrect_answers == 1
    assert result.unattempted_questions == 1
    assert result.raw_score == 0.75
    assert result.percentage == 25.0
    assert result.accuracy == 0.5


def test_negative_marking_can_produce_negative_percentage():
    engine = TestEngine(clock=FakeClock())
    specification = TestSpecification(
        test_id="test:negative",
        title="नकारात्मक अंकन",
        question_count=1,
        duration_seconds=60,
        scoring=ScoringPolicy(correct_marks=1.0, incorrect_marks=-0.25),
    )
    session = engine.create_session(
        specification,
        (candidate("q-1", 1),),
        (question("q-1"),),
        session_id="session:negative",
    )
    engine.start(session.session_id)
    engine.answer(session.session_id, "A")
    result = engine.submit(session.session_id)
    assert result.raw_score == -0.25
    assert result.percentage == -25.0


def test_submit_is_idempotent():
    engine = make_engine()
    session = setup_session(engine)
    engine.start(session.session_id)
    first = engine.submit(session.session_id)
    second = engine.submit(session.session_id)
    assert first == second


def test_expiry_auto_submits_as_expired():
    clock = FakeClock()
    engine = TestEngine(clock=clock)
    session = setup_session(engine)
    engine.start(session.session_id)
    engine.answer(session.session_id, "B")

    clock.value = 1060.0
    expired = engine.get_session(session.session_id)
    assert expired.status is TestSessionStatus.EXPIRED
    assert expired.result is not None
    assert expired.result.timed_out is True
    assert expired.result.correct_answers == 1


def test_answer_after_expiry_is_rejected():
    clock = FakeClock()
    engine = TestEngine(clock=clock)
    session = setup_session(engine)
    engine.start(session.session_id)
    clock.value = 1060.0
    engine.get_session(session.session_id)
    with pytest.raises(ValueError, match="not in progress"):
        engine.answer(session.session_id, "B")


def test_not_enough_questions_is_rejected():
    engine = make_engine()
    specification = TestSpecification(
        test_id="test:small",
        title="टेस्ट",
        question_count=5,
        duration_seconds=60,
    )
    questions = tuple(question(f"q-{i}") for i in range(1, 4))
    candidates = tuple(candidate(f"q-{i}", i) for i in range(1, 4))
    with pytest.raises(ValueError, match="not enough"):
        engine.create_session(
            specification, candidates, questions, session_id="session:small"
        )


def test_invalid_scoring_policy_is_rejected():
    with pytest.raises(ValueError, match="zero or negative"):
        ScoringPolicy(incorrect_marks=0.5)


def test_rejected_question_definition_is_not_usable():
    engine = make_engine()
    specification = make_test()
    questions = (
        question("q-1"),
        question("q-2", status=GeneratedQuestionStatus.REJECTED),
        question("q-3"),
        question("q-4"),
    )
    candidates = tuple(candidate(f"q-{i}", i) for i in range(1, 5))
    with pytest.raises(ValueError, match="accepted"):
        engine.create_session(
            specification, candidates, questions, session_id="session:reject"
        )
