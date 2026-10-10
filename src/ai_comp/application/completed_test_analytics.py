from __future__ import annotations

from collections.abc import Callable
from statistics import fmean
from typing import Any

from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.analysis.question_learning import QuestionLearningHistoryService
from ai_comp.database.postgres_learning_history import PostgresLearningHistoryRepository
from ai_comp.database.postgres_question_learning import PostgresQuestionLearningHistoryRepository


ConnectionFactory = Callable[[], Any]


class CompletedTestAnalyticsProvider:
    """Build learner-scoped analytics from durable completed-test outcomes."""

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def build_report(self, learner_id: str) -> dict[str, object]:
        if not isinstance(learner_id, str) or not learner_id.strip():
            raise ValueError("learner_id is required")
        if learner_id != learner_id.strip():
            raise ValueError("learner_id must not contain surrounding whitespace")

        connection = self._connection_factory()
        try:
            learning_history = LearningHistoryService(
                PostgresLearningHistoryRepository(connection)
            ).history(learner_id)
            question_history = QuestionLearningHistoryService(
                PostgresQuestionLearningHistoryRepository(connection)
            ).history(learner_id)

            attempts = learning_history.attempts
            total_questions = sum(item.total_questions for item in attempts)
            attempted = sum(item.attempted_questions for item in attempts)
            correct = sum(item.correct_answers for item in attempts)
            incorrect = sum(item.incorrect_answers for item in attempts)
            unattempted = sum(item.unattempted_questions for item in attempts)
            percentages = [item.percentage for item in attempts]

            topic_rows = [
                {
                    "concept_id": topic.concept_id,
                    "test_count": topic.test_count,
                    "question_count": topic.question_count,
                    "attempted_count": topic.attempted_count,
                    "correct_count": topic.correct_count,
                    "incorrect_count": topic.incorrect_count,
                    "unattempted_count": topic.unattempted_count,
                    "accuracy": round(topic.accuracy, 4),
                    "accuracy_percentage": round(topic.accuracy * 100.0, 2),
                    "recent_accuracy": round(topic.recent_accuracy, 4),
                    "recent_accuracy_percentage": round(topic.recent_accuracy * 100.0, 2),
                    "performance": topic.performance.value,
                    "trend": topic.trend.value,
                    "weak_streak": topic.weak_streak,
                    "priority_score": round(topic.priority_score, 4),
                    "recommended_action": _recommended_action(
                        topic.performance.value,
                        topic.trend.value,
                        topic.unattempted_count,
                    ),
                }
                for topic in learning_history.topic_performance
            ]
            topic_rows.sort(
                key=lambda item: (-float(item["priority_score"]), str(item["concept_id"]))
            )
            weak_topics = [item for item in topic_rows if item["performance"] == "WEAK"]

            revision_candidates = [
                {
                    "question_id": item.question_id,
                    "concept_ids": list(item.concept_ids),
                    "difficulty": item.difficulty,
                    "priority_score": round(item.priority_score, 4),
                    "mistake_count": item.mistake_count,
                    "mistake_streak": item.mistake_streak,
                    "last_incorrect_at": item.last_incorrect_at.isoformat(),
                    "reason": item.reason,
                }
                for item in question_history.revision_candidates[:50]
            ]
            repeated_concept_alerts = [
                {
                    "concept_id": item.concept_id,
                    "test_count": item.test_count,
                    "weak_test_count": item.weak_test_count,
                    "question_count": item.question_count,
                    "attempted_count": item.attempted_count,
                    "correct_count": item.correct_count,
                    "incorrect_count": item.incorrect_count,
                    "unattempted_count": item.unattempted_count,
                    "accuracy": round(item.accuracy, 4),
                    "accuracy_percentage": round(item.accuracy * 100.0, 2),
                    "priority_score": round(item.priority_score, 4),
                    "reason": item.reason,
                }
                for item in question_history.repeated_concept_alerts[:50]
            ]

            return {
                "schema_version": "1.0",
                "learner_id": learner_id,
                "generated_at": learning_history.generated_at.isoformat(),
                "summary": {
                    "completed_test_count": len(attempts),
                    "total_questions": total_questions,
                    "attempted_questions": attempted,
                    "correct_answers": correct,
                    "incorrect_answers": incorrect,
                    "unattempted_questions": unattempted,
                    "average_percentage": round(fmean(percentages), 2) if percentages else None,
                    "latest_percentage": round(percentages[-1], 2) if percentages else None,
                    "overall_accuracy": round(correct / attempted, 4) if attempted else None,
                    "overall_accuracy_percentage": round(correct * 100.0 / attempted, 2) if attempted else None,
                    "concept_count": len(topic_rows),
                    "weak_topic_count": len(weak_topics),
                    "revision_candidate_count": len(question_history.revision_candidates),
                    "repeated_concept_alert_count": len(question_history.repeated_concept_alerts),
                    "question_outcome_count": len(question_history.outcomes),
                },
                "topic_performance": topic_rows,
                "weak_topics": weak_topics,
                "revision_candidates": revision_candidates,
                "repeated_concept_alerts": repeated_concept_alerts,
                "limits": {
                    "revision_candidates_returned": len(revision_candidates),
                    "repeated_concept_alerts_returned": len(repeated_concept_alerts),
                    "per_list_limit": 50,
                },
            }
        finally:
            close = getattr(connection, "close", None)
            if callable(close):
                close()


def _recommended_action(performance: str, trend: str, unattempted_count: int) -> str:
    if performance == "WEAK":
        return "REMEDIATE_AND_PRACTICE"
    if trend == "DECLINING":
        return "REVIEW_RECENT_MISTAKES"
    if unattempted_count > 0:
        return "PRACTICE_UNATTEMPTED_QUESTIONS"
    return "CONTINUE_PRACTICE"


__all__ = ["CompletedTestAnalyticsProvider"]
