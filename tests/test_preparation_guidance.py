from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from dataclasses import replace

import pytest

from ai_comp.analysis.adaptive_study_strategy_history import AdaptiveStudyStrategyHistoryService
from ai_comp.analysis.preparation_guidance import PreparationGuidanceService
from ai_comp.application.preparation_guidance_api import PreparationGuidanceAPIService
from ai_comp.domain.adaptive_study_strategy import StudyStrategyAction
from ai_comp.domain.adaptive_study_strategy_history import (
    AdaptiveStudyStrategyHistoryReport,
    ConceptStrategyHistory,
    StrategyHistoryScopeKind,
)
from ai_comp.domain.learning_history import (
    LearnerLearningHistory,
    LearnerTopicPerformance,
    LearningAttemptRecord,
    LearningTrend,
    LongTermPerformanceBand,
)
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.preparation_guidance import PreparationActionKind
from ai_comp.domain.question_intelligence import (
    DifficultyLevel,
    RankedQuestionCandidate,
    QuestionIntelligenceScore,
)
from ai_comp.domain.study_schedule import StudyTaskKind
from ai_comp.domain.question_learning import (
    LearnerQuestionAttemptRecord,
    LearnerQuestionHistory,
    LearnerQuestionPerformance,
    QuestionOutcomeKind,
    QuestionRevisionCandidate,
)


NOW = datetime(2026, 10, 9, tzinfo=timezone.utc)


def make_attempt(index: int, percentage: float) -> LearningAttemptRecord:
    correct = int(percentage / 10)
    return LearningAttemptRecord(
        attempt_id=f"attempt-{index}",
        learner_id="learner-1",
        test_id=f"test-{index}",
        session_id=f"session-{index}",
        total_questions=10,
        attempted_questions=10,
        correct_answers=correct,
        incorrect_answers=10 - correct,
        unattempted_questions=0,
        raw_score=float(correct),
        percentage=percentage,
        accuracy=correct / 10,
        completed_at=NOW - timedelta(days=5 - index),
    )


def make_histories(
    percentages=(80.0, 80.0, 60.0, 40.0),
    *,
    include_topic=True,
    include_mistake=True,
):
    attempts = tuple(
        make_attempt(index, percentage)
        for index, percentage in enumerate(percentages, start=1)
    )
    topics = ()
    if include_topic:
        topics = (LearnerTopicPerformance(
            concept_id="science",
            test_count=max(1, len(attempts)),
            question_count=10,
            attempted_count=10,
            correct_count=4,
            incorrect_count=6,
            unattempted_count=0,
            accuracy=0.4,
            recent_accuracy=0.3,
            performance=LongTermPerformanceBand.WEAK,
            trend=LearningTrend.DECLINING,
            weak_streak=2,
            priority_score=0.9,
        ),)
    learning = LearnerLearningHistory(
        learner_id="learner-1",
        attempts=attempts,
        topic_performance=topics,
        generated_at=NOW,
    )

    old_time = NOW - timedelta(days=5)
    outcomes = ()
    performances = ()
    revisions = ()
    if include_mistake:
        outcomes = (LearnerQuestionAttemptRecord(
            outcome_id="outcome-old-q",
            attempt_id="attempt-old-q",
            learner_id="learner-1",
            test_id="test-1",
            session_id="session-1",
            question_id="old-q",
            concept_ids=("science",),
            difficulty="EASY",
            selected_option_key="A",
            correct_option_key="B",
            outcome=QuestionOutcomeKind.INCORRECT,
            completed_at=old_time,
        ),)
        performances = (LearnerQuestionPerformance(
            question_id="old-q",
            concept_ids=("science",),
            difficulty="EASY",
            test_count=1,
            attempt_count=1,
            correct_count=0,
            incorrect_count=1,
            unattempted_count=0,
            accuracy=0.0,
            last_outcome=QuestionOutcomeKind.INCORRECT,
            mistake_count=1,
            mistake_streak=1,
            priority_score=0.95,
            last_seen_at=old_time,
        ),)
        revisions = (QuestionRevisionCandidate(
            question_id="old-q",
            concept_ids=("science",),
            difficulty="EASY",
            priority_score=0.95,
            mistake_count=1,
            mistake_streak=1,
            last_incorrect_at=old_time,
            reason="previous answer was incorrect",
        ),)
    question_history = LearnerQuestionHistory(
        learner_id="learner-1",
        outcomes=outcomes,
        question_performance=performances,
        revision_candidates=revisions,
        repeated_concept_alerts=(),
        generated_at=NOW,
    )
    return learning, question_history


def make_question(qid, concepts=("science",), difficulty="EASY"):
    return GeneratedMCQ(
        generated_question_id=qid,
        generation_id="g",
        material_id="m",
        stem=f"Question {qid}",
        options=(
            GeneratedOption("A", "one"),
            GeneratedOption("B", "two"),
            GeneratedOption("C", "three"),
            GeneratedOption("D", "four"),
        ),
        correct_option_key="B",
        explanation="verified explanation",
        fact_ids=("fact-1",),
        concept_ids=tuple(concepts),
        difficulty=difficulty,
        importance_score=0.9,
        answer_verification=AnswerVerificationStatus.VERIFIED,
        answer_verification_evidence=("source evidence",),
        status=GeneratedQuestionStatus.ACCEPTED,
        quality_score=0.95,
    )


def make_candidate(qid, rank, difficulty=DifficultyLevel.EASY):
    return RankedQuestionCandidate(
        question_id=qid,
        rank=rank,
        score=QuestionIntelligenceScore(
            generated_question_id=qid,
            difficulty=difficulty,
            difficulty_score=0.25 if difficulty is DifficultyLevel.EASY else 0.55,
            importance_score=0.9,
            novelty_score=1.0,
            coverage_score=0.7,
            selection_score=1.0 - rank * 0.05,
        ),
    )


def inputs():
    questions = (
        make_question("old-q"),
        make_question("science-new-1"),
        make_question("science-new-2"),
        make_question("general-1", ("history",)),
        make_question("general-2", ("geography",)),
    )
    candidates = tuple(
        make_candidate(question.generated_question_id, index)
        for index, question in enumerate(questions, start=1)
    )
    return candidates, questions


def build(learning, question_history, *, question_count=3, **kwargs):
    candidates, questions = inputs()
    return PreparationGuidanceService().build_guidance(
        "learner-1",
        test_id="next-test",
        title="Guided practice",
        question_count=question_count,
        duration_seconds=1800,
        history=learning,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
        as_of=NOW,
        generated_at=NOW,
        **kwargs,
    )


def test_guidance_joins_progress_with_existing_personalized_test_plan():
    learning, question_history = make_histories()
    guidance = build(learning, question_history)

    assert guidance.learner_id == "learner-1"
    assert guidance.progress_report.trend is LearningTrend.DECLINING
    assert guidance.progress_report.delta_percentage_points == -30.0
    assert guidance.preparation_plan.question_ids
    assert guidance.preparation_plan.test_specification.question_count == 3
    assert "old-q" in guidance.preparation_plan.revision_question_ids
    assert "science" in guidance.preparation_plan.focus_concept_ids
    assert guidance.preparation_plan.retention_due_question_ids == ("old-q",)
    kinds = {action.kind for action in guidance.actions}
    assert PreparationActionKind.REVIEW_PREVIOUS_MISTAKES in kinds
    assert PreparationActionKind.PRACTICE_WEAK_TOPICS in kinds
    assert PreparationActionKind.REVIEW_RETENTION_ITEMS in kinds
    assert PreparationActionKind.RESPOND_TO_DECLINING_TREND in kinds
    assert tuple(action.priority_score for action in guidance.actions) == tuple(
        sorted((action.priority_score for action in guidance.actions), reverse=True)
    )


def test_guidance_for_insufficient_history_asks_for_more_evidence():
    learning, question_history = make_histories(
        (70.0,), include_topic=False, include_mistake=False,
    )
    guidance = build(
        learning,
        question_history,
        question_count=2,
        mode=PersonalizedPreparationMode.ADAPTIVE,
    )

    assert guidance.progress_report.trend is LearningTrend.INSUFFICIENT_DATA
    assert len(guidance.actions) == 1
    assert guidance.actions[0].kind is PreparationActionKind.COLLECT_MORE_PROGRESS_DATA


def test_guidance_enforces_learner_scope_and_preserves_question_exclusions():
    learning, question_history = make_histories()
    wrong_history = replace(learning, learner_id="learner-2")
    candidates, questions = inputs()
    service = PreparationGuidanceService()

    with pytest.raises(ValueError, match="learning history learner does not match"):
        service.build_guidance(
            "learner-1",
            test_id="wrong",
            title="Wrong learner",
            question_count=2,
            duration_seconds=600,
            history=wrong_history,
            question_history=question_history,
            candidates=candidates,
            questions=questions,
            generated_at=NOW,
            as_of=NOW,
        )

    guidance = service.build_guidance(
        "learner-1",
        test_id="exclude",
        title="Exclude old question",
        question_count=2,
        duration_seconds=600,
        history=learning,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
        exclude_question_ids=("science-new-1",),
        generated_at=NOW,
        as_of=NOW,
    )
    assert "science-new-1" not in guidance.preparation_plan.question_ids
    assert len(guidance.preparation_plan.question_ids) == 2



def make_repeated_decline_strategy_history(*, learner_id="learner-1", assessment_count=3):
    scope = ConceptStrategyHistory(
        scope_kind=StrategyHistoryScopeKind.CONCEPTS,
        scope_ids=("science",),
        task_kind=StudyTaskKind.STUDY_WEAK_TOPIC,
        decision_count=3,
        assessment_count=assessment_count,
        improving_count=0,
        declining_count=2,
        stable_count=1,
        insufficient_data_count=0,
        mean_baseline_accuracy_percentage=70.0,
        mean_follow_up_accuracy_percentage=60.0,
        mean_delta_percentage_points=-10.0,
        mean_recommended_priority_delta=0.15,
        mean_applied_priority_delta=0.15,
        latest_action=StudyStrategyAction.REINFORCE_WEAK_AREA,
        latest_recorded_at=NOW,
    )
    return AdaptiveStudyStrategyHistoryReport(
        learner_id=learner_id,
        entries=(),
        scopes=(scope,),
        generated_at=NOW,
    )


def test_guidance_uses_prior_strategy_history_only_after_evidence_threshold():
    learning, question_history = make_histories()
    before = build(learning, question_history)
    guidance = build(
        learning,
        question_history,
        strategy_history_report=make_repeated_decline_strategy_history(),
    )

    assert guidance.preparation_plan.question_ids == before.preparation_plan.question_ids
    action = next(
        item for item in guidance.actions
        if item.kind is PreparationActionKind.REVISIT_STUDY_APPROACH
    )
    assert action.concept_ids == ("science",)
    assert action.priority_score == pytest.approx(0.88)
    assert "does not prove" in action.reason


def test_guidance_ignores_strategy_history_that_does_not_meet_assessment_threshold():
    learning, question_history = make_histories()
    guidance = build(
        learning,
        question_history,
        strategy_history_report=make_repeated_decline_strategy_history(
            assessment_count=2
        ),
    )

    assert PreparationActionKind.REVISIT_STUDY_APPROACH not in {
        action.kind for action in guidance.actions
    }


def test_guidance_rejects_strategy_history_from_another_learner():
    learning, question_history = make_histories()
    wrong_report = make_repeated_decline_strategy_history(learner_id="learner-2")

    with pytest.raises(ValueError, match="strategy history learner does not match"):
        build(learning, question_history, strategy_history_report=wrong_report)



class EmptyStrategyAuditRepository:
    def list_for_learner(self, learner_id, *, limit=50):
        return ()


class FixedStrategyHistoryService:
    def __init__(self, report):
        self.report = report
        self.calls = []

    def build_report(self, learner_id, *, limit=50, generated_at=None):
        self.calls.append((learner_id, limit, generated_at))
        if self.report.learner_id != learner_id:
            raise ValueError("audit history learner mismatch")
        return replace(self.report, generated_at=generated_at)


def test_api_application_service_returns_versioned_json_payload_and_reuses_canonical_plan():
    learning, question_history = make_histories()
    candidates, questions = inputs()
    app = PreparationGuidanceAPIService(
        strategy_history_service=AdaptiveStudyStrategyHistoryService(
            EmptyStrategyAuditRepository()
        ),
        guidance_service=PreparationGuidanceService(),
    )
    response = app.build_response(
        "learner-1",
        test_id="api-test",
        title="API guided practice",
        question_count=3,
        duration_seconds=1800,
        history=learning,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
        exclude_question_ids=("science-new-1",),
        history_limit=25,
        as_of=NOW,
        generated_at=NOW,
    )

    payload = response.to_payload()
    encoded = json.dumps(payload, ensure_ascii=False)
    assert payload["schema_version"] == "1.0"
    assert payload["learner_id"] == "learner-1"
    assert payload["generated_at"] == NOW.isoformat()
    assert payload["strategy_history"]["summary"]["audit_count"] == 0
    assert payload["strategy_feedback"]["findings"] == []
    assert "science-new-1" not in payload["guidance"]["preparation_plan"]["question_ids"]
    assert isinstance(encoded, str)
    assert payload["guidance"]["actions"][0]["kind"] in {
        action.kind.value for action in response.guidance.actions
    }
    assert type(payload["guidance"]["actions"][0]["kind"]) is str


def test_api_application_service_delivers_qualified_strategy_feedback_in_same_response():
    learning, question_history = make_histories()
    candidates, questions = inputs()
    history_report = make_repeated_decline_strategy_history()
    history_service = FixedStrategyHistoryService(history_report)
    app = PreparationGuidanceAPIService(
        strategy_history_service=history_service,
        guidance_service=PreparationGuidanceService(),
    )

    response = app.build_response(
        "learner-1",
        test_id="api-feedback-test",
        title="API feedback",
        question_count=3,
        duration_seconds=1800,
        history=learning,
        question_history=question_history,
        candidates=candidates,
        questions=questions,
        as_of=NOW,
        generated_at=NOW,
    )

    assert history_service.calls == [("learner-1", 50, NOW)]
    assert len(response.strategy_feedback.findings) == 1
    assert response.guidance.strategy_feedback_report == response.strategy_feedback
    action = next(
        action for action in response.guidance.actions
        if action.kind is PreparationActionKind.REVISIT_STUDY_APPROACH
    )
    assert action.concept_ids == ("science",)
    assert response.to_payload()["strategy_feedback"]["findings"][0]["kind"] == "CHANGE_APPROACH"


def test_api_application_service_validates_learner_and_shared_clock():
    learning, question_history = make_histories()
    candidates, questions = inputs()
    app = PreparationGuidanceAPIService(
        strategy_history_service=AdaptiveStudyStrategyHistoryService(
            EmptyStrategyAuditRepository()
        )
    )

    with pytest.raises(ValueError, match="learner_id"):
        app.build_response(
            " ", test_id="x", title="x", question_count=1, duration_seconds=60,
            history=learning, question_history=question_history,
            candidates=candidates, questions=questions, generated_at=NOW,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        app.build_response(
            "learner-1", test_id="x", title="x", question_count=1, duration_seconds=60,
            history=learning, question_history=question_history,
            candidates=candidates, questions=questions,
            generated_at=datetime(2026, 10, 9),
        )
