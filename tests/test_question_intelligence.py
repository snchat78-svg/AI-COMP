from __future__ import annotations

import pytest

from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)
from ai_comp.domain.question_intelligence import (
    DifficultyLevel,
    QuestionIntelligenceInput,
    QuestionIntelligencePolicy,
)
from ai_comp.material.intelligence import QuestionIntelligenceService


def question(question_id: str, difficulty: str = "MEDIUM") -> GeneratedMCQ:
    return GeneratedMCQ(
        generated_question_id=question_id,
        generation_id="generation:intelligence",
        material_id="material:intelligence",
        stem=f"प्रश्न {question_id}?",
        options=(
            GeneratedOption("A", "एक"),
            GeneratedOption("B", "दो"),
            GeneratedOption("C", "तीन"),
            GeneratedOption("D", "चार"),
        ),
        correct_option_key="B",
        explanation="स्रोत तथ्य द्वारा समर्थित।",
        fact_ids=("fact-1",),
        concept_ids=("concept-1",),
        difficulty=difficulty,
        importance_score=0.90,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("सत्यापित स्रोत तथ्य",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def evidence(question_id: str, appearances: int, *, signal=None, novelty=1.0, coverage=0.5):
    return QuestionIntelligenceInput(
        generated_question_id=question_id,
        requested_difficulty=DifficultyLevel.MEDIUM,
        fact_importance_scores=(0.90,),
        fact_confidences=(0.95,),
        concept_confidences=(0.90,),
        verified_appearance_count=appearances,
        difficulty_signal=signal,
        novelty_score=novelty,
        coverage_score=coverage,
    )


def test_importance_uses_verified_frequency_as_bounded_evidence():
    service = QuestionIntelligenceService()
    low = service.score(question("q-low"), evidence("q-low", 0))
    high = service.score(question("q-high"), evidence("q-high", 10))
    assert high.importance_score > low.importance_score
    assert high.importance_score <= 1.0


def test_frequency_does_not_make_unverified_history_appear():
    service = QuestionIntelligenceService()
    result = service.score(question("q"), evidence("q", 0))
    assert result.importance_score < 1.0


def test_explicit_difficulty_signal_maps_to_difficulty_band():
    service = QuestionIntelligenceService()
    result = service.score(question("q"), evidence("q", 1, signal=0.82))
    assert result.difficulty is DifficultyLevel.HARD
    assert result.difficulty_score == 0.82


def test_easy_signal_maps_to_easy():
    result = QuestionIntelligenceService().score(
        question("q"), evidence("q", 1, signal=0.20)
    )
    assert result.difficulty is DifficultyLevel.EASY


def test_ranking_prefers_importance_then_novelty_and_coverage():
    service = QuestionIntelligenceService()
    questions = (question("q-a"), question("q-b"))
    evidence_map = {
        "q-a": evidence("q-a", 10, novelty=0.2, coverage=0.1),
        "q-b": evidence("q-b", 2, novelty=1.0, coverage=1.0),
    }
    ranked = service.rank(questions, evidence_map)
    assert ranked[0].question_id == "q-b"
    assert ranked[0].rank == 1
    assert ranked[1].rank == 2


def test_rank_limit_is_applied_after_deterministic_sort():
    service = QuestionIntelligenceService()
    questions = (question("q-b"), question("q-a"))
    evidence_map = {
        "q-a": evidence("q-a", 5),
        "q-b": evidence("q-b", 5),
    }
    ranked = service.rank(questions, evidence_map, limit=1)
    assert len(ranked) == 1
    assert ranked[0].question_id == "q-a"


def test_rejects_non_accepted_question():
    rejected = question("q")
    rejected = GeneratedMCQ(
        **{**rejected.__dict__, "status": GeneratedQuestionStatus.REJECTED}
    )
    with pytest.raises(ValueError, match="only accepted"):
        QuestionIntelligenceService().score(rejected, evidence("q", 1))


def test_evidence_identity_must_match_question():
    with pytest.raises(ValueError, match="does not match"):
        QuestionIntelligenceService().score(
            question("q-1"), evidence("q-2", 1)
        )


def test_policy_weights_must_sum_to_one():
    with pytest.raises(ValueError, match="sum to 1"):
        QuestionIntelligencePolicy(fact_importance_weight=0.5)
