from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone

from ai_comp.domain.learning_history import (
    LearnerLearningHistory,
    LearnerTopicPerformance,
    LearningAttemptRecord,
    LearningHistoryRepository,
    LearningTrend,
    LongTermPerformanceBand,
    TopicAttemptRecord,
    attempt_identity,
)
from ai_comp.domain.test_analysis import TestAnalysis


class LearningHistoryService:
    """Persists and aggregates learning signals across completed tests."""

    def __init__(self, repository: LearningHistoryRepository) -> None:
        self.repository = repository

    def record_analysis(
        self,
        learner_id: str,
        analysis: TestAnalysis,
        *,
        completed_at: datetime | None = None,
    ) -> LearningAttemptRecord:
        timestamp = completed_at or datetime.now(timezone.utc)
        attempt = LearningAttemptRecord(
            attempt_id=attempt_identity(learner_id, analysis.session_id),
            learner_id=learner_id,
            test_id=analysis.test_id,
            session_id=analysis.session_id,
            total_questions=analysis.total_questions,
            attempted_questions=analysis.attempted_questions,
            correct_answers=analysis.correct_answers,
            incorrect_answers=analysis.incorrect_answers,
            unattempted_questions=analysis.unattempted_questions,
            raw_score=analysis.raw_score,
            percentage=analysis.percentage,
            accuracy=analysis.accuracy,
            completed_at=timestamp,
        )
        topics = tuple(
            TopicAttemptRecord(
                attempt_id=attempt.attempt_id,
                learner_id=learner_id,
                test_id=analysis.test_id,
                session_id=analysis.session_id,
                concept_id=topic.concept_id,
                question_count=topic.question_count,
                attempted_count=topic.attempted_count,
                correct_count=topic.correct_count,
                incorrect_count=topic.incorrect_count,
                unattempted_count=topic.unattempted_count,
                accuracy=topic.accuracy,
                performance=LongTermPerformanceBand(topic.performance.value),
            )
            for topic in analysis.topic_performance
        )
        self.repository.save_attempt(attempt, topics)
        return attempt

    def history(
        self,
        learner_id: str,
        *,
        generated_at: datetime | None = None,
    ) -> LearnerLearningHistory:
        attempts = tuple(
            sorted(
                self.repository.list_attempts(learner_id),
                key=lambda item: (item.completed_at, item.session_id),
            )
        )
        topic_attempts = tuple(
            sorted(
                self.repository.list_topic_attempts(learner_id),
                key=lambda item: (attempt_time(attempts, item.attempt_id), item.session_id),
            )
        )

        grouped: dict[str, list[TopicAttemptRecord]] = defaultdict(list)
        for item in topic_attempts:
            grouped[item.concept_id].append(item)

        topic_rows = tuple(
            self._aggregate_topic(concept_id, items)
            for concept_id, items in sorted(grouped.items())
        )
        return LearnerLearningHistory(
            learner_id=learner_id,
            attempts=attempts,
            topic_performance=topic_rows,
            generated_at=generated_at or datetime.now(timezone.utc),
        )

    @staticmethod
    def _aggregate_topic(
        concept_id: str,
        items: Sequence[TopicAttemptRecord],
    ) -> LearnerTopicPerformance:
        question_count = sum(item.question_count for item in items)
        attempted_count = sum(item.attempted_count for item in items)
        correct_count = sum(item.correct_count for item in items)
        incorrect_count = sum(item.incorrect_count for item in items)
        unattempted_count = sum(item.unattempted_count for item in items)
        accuracy = correct_count / attempted_count if attempted_count else 0.0
        recent_accuracy = items[-1].accuracy
        performance = (
            LongTermPerformanceBand.WEAK
            if accuracy < 0.50
            else LongTermPerformanceBand.AVERAGE
            if accuracy < 0.75
            else LongTermPerformanceBand.STRONG
        )

        weak_streak = 0
        for item in reversed(items):
            if item.performance is LongTermPerformanceBand.WEAK:
                weak_streak += 1
            else:
                break

        if len(items) < 2:
            trend = LearningTrend.INSUFFICIENT_DATA
        else:
            delta = items[-1].accuracy - items[-2].accuracy
            trend = (
                LearningTrend.IMPROVING if delta >= 0.10
                else LearningTrend.DECLINING if delta <= -0.10
                else LearningTrend.STABLE
            )

        priority = min(
            1.0,
            (1.0 - accuracy) * 0.55
            + (1.0 - recent_accuracy) * 0.30
            + min(weak_streak, 3) / 3.0 * 0.15,
        )
        return LearnerTopicPerformance(
            concept_id=concept_id,
            test_count=len(items),
            question_count=question_count,
            attempted_count=attempted_count,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            unattempted_count=unattempted_count,
            accuracy=accuracy,
            recent_accuracy=recent_accuracy,
            performance=performance,
            trend=trend,
            weak_streak=weak_streak,
            priority_score=priority,
        )


def attempt_time(
    attempts: Sequence[LearningAttemptRecord],
    attempt_id: str,
) -> datetime:
    for attempt in attempts:
        if attempt.attempt_id == attempt_id:
            return attempt.completed_at
    raise ValueError(f"topic references unknown attempt: {attempt_id}")
