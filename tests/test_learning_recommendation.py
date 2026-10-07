from __future__ import annotations

from ai_comp.analysis.learning import LearningRecommendationService, WeakTopicNextTestSelector
from ai_comp.domain.learning_recommendation import (
    LearningRecommendationPolicy,
    RecommendedDifficulty,
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
from ai_comp.domain.test_analysis import (
    PerformanceBand,
    TestAnalysis,
    TopicPerformance,
    WeakTopic,
)


def question(qid, concepts, difficulty="MEDIUM"):
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
        difficulty=difficulty,
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("स्रोत",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def candidate(qid, rank, difficulty=DifficultyLevel.MEDIUM, score=0.9, novelty=1.0):
    return RankedQuestionCandidate(
        question_id=qid,
        rank=rank,
        score=QuestionIntelligenceScore(
            generated_question_id=qid,
            difficulty=difficulty,
            difficulty_score={"EASY": 0.25, "MEDIUM": 0.55, "HARD": 0.80}[difficulty.value],
            importance_score=0.9,
            novelty_score=novelty,
            coverage_score=0.5,
            selection_score=score,
        ),
    )


def analysis():
    return TestAnalysis(
        test_id="t",
        session_id="s",
        total_questions=4,
        attempted_questions=3,
        correct_answers=1,
        incorrect_answers=2,
        unattempted_questions=1,
        raw_score=0.5,
        percentage=12.5,
        accuracy=1 / 3,
        outcomes=(
            __import__("ai_comp.domain.test_analysis", fromlist=["QuestionOutcome"]).QuestionOutcome(
                question_id="old-science",
                concept_ids=("science",),
                selected_option_key="A",
                correct_option_key="B",
                attempted=True,
                correct=False,
                difficulty="MEDIUM",
            ),
            __import__("ai_comp.domain.test_analysis", fromlist=["QuestionOutcome"]).QuestionOutcome(
                question_id="old-history",
                concept_ids=("history",),
                selected_option_key="A",
                correct_option_key="B",
                attempted=True,
                correct=False,
                difficulty="MEDIUM",
            ),
            __import__("ai_comp.domain.test_analysis", fromlist=["QuestionOutcome"]).QuestionOutcome(
                question_id="old-history-2",
                concept_ids=("history",),
                selected_option_key="B",
                correct_option_key="B",
                attempted=True,
                correct=True,
                difficulty="MEDIUM",
            ),
            __import__("ai_comp.domain.test_analysis", fromlist=["QuestionOutcome"]).QuestionOutcome(
                question_id="old-science-2",
                concept_ids=("science",),
                selected_option_key=None,
                correct_option_key="B",
                attempted=False,
                correct=False,
                difficulty="MEDIUM",
            ),
        ),
        topic_performance=(
            TopicPerformance(
                concept_id="history",
                question_count=2,
                attempted_count=2,
                correct_count=1,
                incorrect_count=1,
                unattempted_count=0,
                accuracy=0.5,
                performance=PerformanceBand.AVERAGE,
            ),
            TopicPerformance(
                concept_id="science",
                question_count=2,
                attempted_count=1,
                correct_count=0,
                incorrect_count=1,
                unattempted_count=1,
                accuracy=0.0,
                performance=PerformanceBand.WEAK,
            ),
        ),
        weak_topics=(
            WeakTopic(
                concept_id="science",
                priority_score=1.0,
                accuracy=0.0,
                attempted_count=1,
                question_count=2,
                reason="कमजोर accuracy",
            ),
        ),
    )


def test_recommendations_convert_weak_topics_into_difficulty_guidance():
    recommendations = LearningRecommendationService().recommend(analysis())
    assert len(recommendations) == 1
    assert recommendations[0].concept_id == "science"
    assert recommendations[0].recommended_difficulty is RecommendedDifficulty.EASY


def test_selector_focuses_next_test_on_weak_topic():
    qs = (
        question("old-science", ("science",), "MEDIUM"),
        question("new-history", ("history",), "MEDIUM"),
        question("new-science", ("science",), "EASY"),
        question("new-math", ("math",), "HARD"),
    )
    candidates = (
        candidate("old-science", 1),
        candidate("new-history", 2),
        candidate("new-science", 3, DifficultyLevel.EASY, score=0.80),
        candidate("new-math", 4),
    )
    plan = WeakTopicNextTestSelector().select(
        analysis(), candidates, qs, question_count=3
    )
    assert plan.focus_concept_ids == ("science",)
    assert plan.question_ids[0] == "new-science"
    assert "old-science" in plan.question_ids
    assert plan.question_ids[-1] == "new-history"


def test_selector_requires_accepted_questions_and_enough_candidates():
    qs = (question("q1", ("science",)),)
    candidates = (candidate("q1", 1),)
    import pytest
    with pytest.raises(ValueError, match="not enough"):
        WeakTopicNextTestSelector().select(
            analysis(), candidates, qs, question_count=2
        )


def test_policy_validates_focus_ratio():
    import pytest
    with pytest.raises(ValueError, match="focus_ratio"):
        LearningRecommendationPolicy(focus_ratio=0.0)
