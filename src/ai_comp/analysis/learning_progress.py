from __future__ import annotations

from datetime import datetime, timezone
from statistics import fmean

from ai_comp.domain.adaptive_difficulty import AdaptiveDifficultyProfile
from ai_comp.domain.learning_history import (
    LearnerLearningHistory,
    LearningTrend,
)
from ai_comp.domain.learning_progress import LearnerProgressReport, LearnerTopicProgress
from ai_comp.domain.question_learning import (
    LearnerQuestionHistory,
    QuestionOutcomeKind,
)


class LearningProgressService:
    """Evaluates learner outcome movement without changing stored learning history.

    The comparison is a descriptive signal, not proof of causation: tests may differ
    in difficulty and question mix. Topic and mastery signals are re-used from the
    existing history/adaptive services rather than recalculated here.
    """

    def __init__(
        self,
        *,
        comparison_window_size: int = 3,
        stable_threshold_percentage_points: float = 5.0,
    ) -> None:
        if comparison_window_size < 1:
            raise ValueError("comparison_window_size must be positive")
        if not 0.0 < stable_threshold_percentage_points <= 100.0:
            raise ValueError("stable threshold must be greater than 0 and at most 100")
        self.comparison_window_size = comparison_window_size
        self.stable_threshold_percentage_points = stable_threshold_percentage_points

    def analyze(
        self,
        learner_id: str,
        learning_history: LearnerLearningHistory,
        question_history: LearnerQuestionHistory,
        *,
        adaptive_profile: AdaptiveDifficultyProfile | None = None,
        generated_at: datetime | None = None,
    ) -> LearnerProgressReport:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if learning_history.learner_id != learner_id:
            raise ValueError("learning history learner does not match")
        if question_history.learner_id != learner_id:
            raise ValueError("question history learner does not match")
        if adaptive_profile is not None and adaptive_profile.learner_id != learner_id:
            raise ValueError("adaptive profile learner does not match")

        attempts = tuple(sorted(
            learning_history.attempts,
            key=lambda item: (item.completed_at, item.session_id),
        ))
        session_ids = tuple(item.session_id for item in attempts)
        if len(session_ids) != len(set(session_ids)):
            raise ValueError("learning history contains duplicate sessions")
        for attempt in attempts:
            if attempt.learner_id != learner_id:
                raise ValueError("attempt learner does not match")
            if attempt.completed_at.tzinfo is None or attempt.completed_at.utcoffset() is None:
                raise ValueError("attempt timestamps must be timezone-aware")
            if not 0.0 <= attempt.percentage <= 100.0:
                raise ValueError("attempt percentage must be between 0 and 100")

        history_topics = {item.concept_id: item for item in learning_history.topic_performance}
        if len(history_topics) != len(learning_history.topic_performance):
            raise ValueError("learning history contains duplicate topic summaries")

        outcomes = tuple(question_history.outcomes)
        outcome_ids = tuple(item.outcome_id for item in outcomes)
        if len(outcome_ids) != len(set(outcome_ids)):
            raise ValueError("question history contains duplicate outcomes")
        seen_question_occurrences: set[tuple[str, str]] = set()
        for outcome in outcomes:
            if outcome.learner_id != learner_id:
                raise ValueError("question outcome learner does not match")
            occurrence = (outcome.session_id, outcome.question_id)
            if occurrence in seen_question_occurrences:
                raise ValueError("question history contains duplicate session/question outcomes")
            seen_question_occurrences.add(occurrence)

        decision_by_concept = {
            decision.concept_id: decision
            for decision in (adaptive_profile.decisions if adaptive_profile else ())
        }
        topic_progress = []
        for topic in sorted(
            learning_history.topic_performance,
            key=lambda item: (-item.priority_score, item.concept_id),
        ):
            decision = decision_by_concept.get(topic.concept_id)
            topic_progress.append(LearnerTopicProgress(
                concept_id=topic.concept_id,
                accuracy=topic.accuracy,
                recent_accuracy=topic.recent_accuracy,
                trend=topic.trend,
                performance=topic.performance,
                weak_streak=topic.weak_streak,
                priority_score=topic.priority_score,
                mastery=decision.mastery if decision else None,
                recommended_action=decision.action if decision else None,
                decision_reason=decision.reason if decision else None,
            ))

        comparison_count = min(self.comparison_window_size, len(attempts) // 2)
        if comparison_count:
            baseline = attempts[-2 * comparison_count:-comparison_count]
            recent = attempts[-comparison_count:]
            baseline_average = fmean(item.percentage for item in baseline)
            recent_average = fmean(item.percentage for item in recent)
            delta = recent_average - baseline_average
            if delta >= self.stable_threshold_percentage_points:
                trend = LearningTrend.IMPROVING
            elif delta <= -self.stable_threshold_percentage_points:
                trend = LearningTrend.DECLINING
            else:
                trend = LearningTrend.STABLE
            baseline_average = round(baseline_average, 2)
            recent_average = round(recent_average, 2)
            delta = round(delta, 2)
            baseline_count = recent_count = comparison_count
        else:
            baseline_average = recent_average = delta = None
            trend = LearningTrend.INSUFFICIENT_DATA
            baseline_count = recent_count = 0

        attempted_outcomes = tuple(
            item for item in outcomes
            if item.outcome is not QuestionOutcomeKind.UNATTEMPTED
        )
        correct_count = sum(
            item.outcome is QuestionOutcomeKind.CORRECT
            for item in outcomes
        )
        question_accuracy = (
            correct_count / len(attempted_outcomes) if attempted_outcomes else None
        )
        report_time = generated_at or datetime.now(timezone.utc)
        if report_time.tzinfo is None or report_time.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")

        return LearnerProgressReport(
            learner_id=learner_id,
            completed_test_count=len(attempts),
            total_questions=sum(item.total_questions for item in attempts),
            current_test_percentage=round(attempts[-1].percentage, 2) if attempts else None,
            baseline_average_percentage=baseline_average,
            recent_average_percentage=recent_average,
            delta_percentage_points=delta,
            trend=trend,
            baseline_test_count=baseline_count,
            recent_test_count=recent_count,
            question_outcome_count=len(outcomes),
            question_attempt_count=len(attempted_outcomes),
            question_correct_count=correct_count,
            question_accuracy=round(question_accuracy, 4) if question_accuracy is not None else None,
            topics=tuple(topic_progress),
            retention_due_question_ids=(
                adaptive_profile.retention_due_question_ids
                if adaptive_profile is not None else ()
            ),
            generated_at=report_time,
        )


__all__ = ["LearningProgressService"]
