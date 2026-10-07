from __future__ import annotations

from dataclasses import replace

import pytest

from ai_comp.analysis.test_analysis import TestAnalysisService
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
from ai_comp.domain.test_engine import ScoringPolicy, TestSessionStatus, TestSpecification
from ai_comp.test_engine import TestEngine


class Clock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value


def question(qid, concepts):
    return GeneratedMCQ(
        generated_question_id=qid,
        generation_id="g",
        material_id="m",
        stem=f"प्रश्न {qid}",
        options=(
            GeneratedOption("A", "एक"),
            GeneratedOption("B", "दो"),
            GeneratedOption("C", "तीन"),
            GeneratedOption("D", "चार"),
        ),
        correct_option_key="B",
        explanation="स्रोत",
        fact_ids=("f",),
        concept_ids=tuple(concepts),
        difficulty="MEDIUM",
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("स्रोत",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def candidate(qid, rank):
    return RankedQuestionCandidate(
        question_id=qid,
        rank=rank,
        score=QuestionIntelligenceScore(
            generated_question_id=qid,
            difficulty=DifficultyLevel.MEDIUM,
            difficulty_score=0.55,
            importance_score=0.9,
            novelty_score=1.0,
            coverage_score=0.5,
            selection_score=0.9,
        ),
    )


def make_session():
    clock = Clock()
    engine = TestEngine(clock=clock)
    spec = TestSpecification(
        test_id="test:a",
        title="विश्लेषण",
        question_count=4,
        duration_seconds=60,
        scoring=ScoringPolicy(correct_marks=1.0, incorrect_marks=-0.25),
    )
    qs = (
        question("q1", ("history",)),
        question("q2", ("history",)),
        question("q3", ("science",)),
        question("q4", ("science",)),
    )
    engine.create_session(
        spec,
        tuple(candidate(q.generated_question_id, i + 1) for i, q in enumerate(qs)),
        qs,
        session_id="s1",
    )
    engine.start("s1")
    engine.answer("s1", "B")
    engine.next("s1")
    engine.answer("s1", "A")
    engine.next("s1")
    engine.answer("s1", "A")
    engine.next("s1")
    result = engine.submit("s1")
    return engine.get_session("s1"), result, qs


def test_analysis_builds_question_outcomes_and_topic_stats():
    session, result, qs = make_session()
    analysis = TestAnalysisService().analyze(session, result, qs)
    assert analysis.correct_answers == 1
    assert analysis.incorrect_answers == 2
    assert analysis.unattempted_questions == 1
    history = next(x for x in analysis.topic_performance if x.concept_id == "history")
    science = next(x for x in analysis.topic_performance if x.concept_id == "science")
    assert history.question_count == 2
    assert history.correct_count == 1
    assert history.accuracy == 0.5
    assert science.accuracy == 0.0


def test_weak_topics_are_ranked_by_priority():
    session, result, qs = make_session()
    analysis = TestAnalysisService().analyze(session, result, qs)
    assert analysis.weak_topics[0].concept_id == "science"
    assert analysis.weak_topics[0].priority_score > 0.9


def test_finished_status_is_required():
    session, result, qs = make_session()
    created = replace(session, status=TestSessionStatus.CREATED, result=None, submitted_at=None)
    with pytest.raises(ValueError, match="finished"):
        TestAnalysisService().analyze(created, result, qs)


def test_session_result_identity_is_required():
    session, result, qs = make_session()
    wrong = replace(result, session_id="other")
    with pytest.raises(ValueError, match="does not match"):
        TestAnalysisService().analyze(session, wrong, qs)


def test_questions_must_exactly_match_session():
    session, result, qs = make_session()
    with pytest.raises(ValueError, match="exactly match"):
        TestAnalysisService().analyze(session, result, qs[:-1])
