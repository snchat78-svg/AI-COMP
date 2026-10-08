from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ai_comp.analysis.adaptive_test_composition import AdaptiveTestCompositionService
from ai_comp.domain.adaptive_difficulty import (
    AdaptiveAction,
    AdaptiveDifficultyDecision,
    AdaptiveDifficultyProfile,
    MasteryStatus,
)
from ai_comp.domain.adaptive_test_composition import AdaptiveTestCompositionPolicy
from ai_comp.domain.learning_history import LearningTrend
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
from ai_comp.domain.question_learning import (
    LearnerQuestionHistory,
    QuestionRevisionCandidate,
)


class AdaptiveStub:
    def __init__(self, profile: AdaptiveDifficultyProfile):
        self.profile = profile

    def analyze(self, *args, **kwargs):
        return self.profile


def histories():
    return (
        type("History", (), {"learner_id": "learner"})(),
        LearnerQuestionHistory(
            learner_id="learner",
            outcomes=(),
            question_performance=(),
            revision_candidates=(),
            repeated_concept_alerts=(),
            generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
    )


def question(question_id: str, concepts: tuple[str, ...], difficulty: str = "MEDIUM"):
    return GeneratedMCQ(
        generated_question_id=question_id,
        generation_id="g",
        material_id="m",
        stem=question_id,
        options=(
            GeneratedOption("A", "one"),
            GeneratedOption("B", "two"),
            GeneratedOption("C", "three"),
            GeneratedOption("D", "four"),
        ),
        correct_option_key="B",
        explanation="source",
        fact_ids=("fact",),
        concept_ids=concepts,
        difficulty=difficulty,
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("source",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def candidate(question_id: str, rank: int, difficulty=DifficultyLevel.MEDIUM):
    return RankedQuestionCandidate(
        question_id=question_id,
        rank=rank,
        score=QuestionIntelligenceScore(
            generated_question_id=question_id,
            difficulty=difficulty,
            difficulty_score={
                DifficultyLevel.EASY: 0.25,
                DifficultyLevel.MEDIUM: 0.55,
                DifficultyLevel.HARD: 0.85,
            }[difficulty],
            importance_score=0.9,
            novelty_score=1.0,
            coverage_score=0.5,
            selection_score=1.0 - rank * 0.01,
        ),
    )


def profile(
    *,
    decisions=(),
    due=(),
    difficulty=DifficultyLevel.MEDIUM,
):
    return AdaptiveDifficultyProfile(
        learner_id="learner",
        decisions=tuple(decisions),
        recommended_difficulty=difficulty,
        retention_due_question_ids=tuple(due),
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def decision(
    concept_id: str,
    action: AdaptiveAction,
    difficulty: DifficultyLevel,
    priority: float = 0.8,
):
    return AdaptiveDifficultyDecision(
        concept_id=concept_id,
        test_count=3,
        accuracy=0.9,
        recent_accuracy=0.9,
        trend=LearningTrend.STABLE,
        weak_streak=0,
        mastery=(
            MasteryStatus.LEARNING
            if action is AdaptiveAction.REMEDIATE
            else MasteryStatus.MASTERED
            if action is AdaptiveAction.ADVANCE
            else MasteryStatus.RETENTION_DUE
            if action is AdaptiveAction.RETAIN
            else MasteryStatus.DEVELOPING
        ),
        action=action,
        recommended_difficulty=difficulty,
        retention_due_count=1 if action is AdaptiveAction.RETAIN else 0,
        priority_score=priority,
        reason=action.value,
    )


def test_retention_due_is_prioritized_and_reported():
    learning, question_history = histories()
    p = profile(
        decisions=(decision("science", AdaptiveAction.RETAIN, DifficultyLevel.MEDIUM),),
        due=("q-due",),
    )
    service = AdaptiveTestCompositionService(
        adaptive_difficulty_service=AdaptiveStub(p)
    )
    questions = tuple(
        question(qid, ("science",))
        for qid in ("q-general", "q-due", "q2")
    )
    candidates = (
        candidate("q-general", 1),
        candidate("q-due", 3),
        candidate("q2", 2),
    )

    plan = service.compose(
        "learner",
        question_count=2,
        learning_history=learning,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
    )

    assert plan.question_ids[0] == "q-due"
    assert plan.retention_question_ids == ("q-due",)
    assert plan.recommended_difficulty is DifficultyLevel.MEDIUM


def test_previous_mistake_is_composed_after_retention_stage():
    learning, question_history = histories()
    revision = QuestionRevisionCandidate(
        question_id="q-mistake",
        concept_ids=("science",),
        difficulty="EASY",
        priority_score=1.0,
        mistake_count=2,
        mistake_streak=1,
        last_incorrect_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        reason="repeated mistake",
    )
    question_history = LearnerQuestionHistory(
        learner_id="learner",
        outcomes=(),
        question_performance=(),
        revision_candidates=(revision,),
        repeated_concept_alerts=(),
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    p = profile(
        decisions=(decision("science", AdaptiveAction.REMEDIATE, DifficultyLevel.EASY),),
        difficulty=DifficultyLevel.EASY,
    )

    questions = tuple(
        question(qid, ("science",), "EASY")
        for qid in ("q-mistake", "q-new", "q-new-2")
    )
    candidates = (
        candidate("q-new", 1, DifficultyLevel.MEDIUM),
        candidate("q-mistake", 3, DifficultyLevel.EASY),
        candidate("q-new-2", 2, DifficultyLevel.EASY),
    )

    plan = AdaptiveTestCompositionService(
        adaptive_difficulty_service=AdaptiveStub(p)
    ).compose(
        "learner",
        question_count=2,
        learning_history=learning,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
    )

    assert "q-mistake" in plan.revision_question_ids
    assert plan.question_ids[0] == "q-mistake"
    assert "q-mistake" in plan.remediation_question_ids


def test_coverage_balances_concepts_when_alternatives_exist():
    learning, question_history = histories()
    p = profile(
        decisions=(
            decision("science", AdaptiveAction.STABILIZE, DifficultyLevel.MEDIUM),
            decision("history", AdaptiveAction.STABILIZE, DifficultyLevel.MEDIUM),
        )
    )
    questions = tuple(
        question(
            qid,
            ("science",) if qid.startswith("s") else ("history",),
        )
        for qid in ("s1", "s2", "s3", "s4", "h1", "h2")
    )
    candidates = tuple(
        candidate(
            qid,
            rank,
            DifficultyLevel.MEDIUM,
        )
        for rank, qid in enumerate(
            ("s1", "s2", "s3", "s4", "h1", "h2"),
            start=1,
        )
    )

    plan = AdaptiveTestCompositionService(
        adaptive_difficulty_service=AdaptiveStub(p)
    ).compose(
        "learner",
        question_count=4,
        learning_history=learning,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
    )

    coverage = {item.concept_id: item.selected_count for item in plan.coverage}
    assert coverage["science"] == 2
    assert coverage["history"] == 2
    assert plan.focus_concept_ids == ("history", "science")


def test_accepted_question_gate_is_preserved():
    learning, question_history = histories()
    p = profile()

    bad = question("bad", ("science",))
    bad = GeneratedMCQ(
        generated_question_id=bad.generated_question_id,
        generation_id=bad.generation_id,
        material_id=bad.material_id,
        stem=bad.stem,
        options=bad.options,
        correct_option_key=bad.correct_option_key,
        explanation=bad.explanation,
        fact_ids=bad.fact_ids,
        concept_ids=bad.concept_ids,
        difficulty=bad.difficulty,
        importance_score=bad.importance_score,
        status=GeneratedQuestionStatus.REJECTED,
        quality_score=0.0,
    )

    with pytest.raises(ValueError, match="accepted"):
        AdaptiveTestCompositionService(
            adaptive_difficulty_service=AdaptiveStub(p)
        ).compose(
            "learner",
            question_count=1,
            learning_history=learning,
            question_history=question_history,
            candidates=(candidate("bad", 1),),
            questions=(bad,),
        )


def test_mastered_concept_advancement_is_exposed():
    learning, question_history = histories()
    p = profile(
        decisions=(decision("science", AdaptiveAction.ADVANCE, DifficultyLevel.HARD),),
        difficulty=DifficultyLevel.HARD,
    )
    questions = (
        question("hard-1", ("science",), "HARD"),
        question("other", ("other",), "MEDIUM"),
    )
    candidates = (
        candidate("other", 1, DifficultyLevel.MEDIUM),
        candidate("hard-1", 2, DifficultyLevel.HARD),
    )

    plan = AdaptiveTestCompositionService(
        adaptive_difficulty_service=AdaptiveStub(p)
    ).compose(
        "learner",
        question_count=1,
        learning_history=learning,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
    )

    assert plan.question_ids == ("hard-1",)
    assert plan.advancement_question_ids == ("hard-1",)
    assert plan.recommended_difficulty is DifficultyLevel.HARD


def test_exclusions_are_honored():
    learning, question_history = histories()
    p = profile()
    questions = (question("q1", ("science",)), question("q2", ("science",)))
    candidates = (candidate("q1", 1), candidate("q2", 2))

    plan = AdaptiveTestCompositionService(
        adaptive_difficulty_service=AdaptiveStub(p)
    ).compose(
        "learner",
        question_count=1,
        learning_history=learning,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
        exclude_question_ids=("q1",),
    )

    assert plan.question_ids == ("q2",)
