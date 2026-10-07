from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from ai_comp.domain.material_generation import GeneratedMCQ
from ai_comp.domain.test_analysis import (
    PerformanceBand,
    QuestionOutcome,
    TestAnalysis,
    TopicPerformance,
    WeakTopic,
)
from ai_comp.domain.test_engine import TestResult, TestSession


class TestAnalysisService:
    """Builds deterministic learning analytics from an already-scored test."""

    def analyze(self, session: TestSession, result: TestResult, questions: Sequence[GeneratedMCQ]) -> TestAnalysis:
        if result.session_id != session.session_id or result.test_id != session.test_id:
            raise ValueError("result does not match test session")
        if result.status.value not in {"SUBMITTED", "EXPIRED"}:
            raise ValueError("only finished test results can be analyzed")

        by_id = {question.generated_question_id: question for question in questions}
        if set(session.question_ids) != set(by_id):
            raise ValueError("questions do not exactly match the test session")

        answers = {answer.question_id: answer for answer in session.answers}
        outcomes = []
        for question_id in session.question_ids:
            question = by_id[question_id]
            answer = answers.get(question_id)
            selected = answer.selected_option_key if answer else None
            correct = bool(
                answer
                and answer.selected_option_key.strip().upper()
                == question.correct_option_key.strip().upper()
            )
            outcomes.append(
                QuestionOutcome(
                    question_id=question_id,
                    concept_ids=tuple(question.concept_ids),
                    selected_option_key=selected,
                    correct_option_key=question.correct_option_key,
                    attempted=answer is not None,
                    correct=correct,
                    difficulty=question.difficulty,
                )
            )

        topic_performance = self._topic_performance(outcomes)
        return TestAnalysis(
            test_id=result.test_id,
            session_id=result.session_id,
            total_questions=result.total_questions,
            attempted_questions=result.attempted_questions,
            correct_answers=result.correct_answers,
            incorrect_answers=result.incorrect_answers,
            unattempted_questions=result.unattempted_questions,
            raw_score=result.raw_score,
            percentage=result.percentage,
            accuracy=result.accuracy,
            outcomes=tuple(outcomes),
            topic_performance=topic_performance,
            weak_topics=self._weak_topics(topic_performance),
        )

    @staticmethod
    def _topic_performance(outcomes: Sequence[QuestionOutcome]) -> tuple[TopicPerformance, ...]:
        grouped: dict[str, list[QuestionOutcome]] = defaultdict(list)
        for outcome in outcomes:
            for concept_id in outcome.concept_ids:
                grouped[concept_id].append(outcome)

        rows = []
        for concept_id, items in grouped.items():
            attempted = sum(item.attempted for item in items)
            correct = sum(item.correct for item in items)
            incorrect = sum(item.incorrect for item in items)
            unattempted = len(items) - attempted
            accuracy = correct / attempted if attempted else 0.0
            performance = (
                PerformanceBand.WEAK if accuracy < 0.50
                else PerformanceBand.AVERAGE if accuracy < 0.75
                else PerformanceBand.STRONG
            )
            rows.append(
                TopicPerformance(
                    concept_id=concept_id,
                    question_count=len(items),
                    attempted_count=attempted,
                    correct_count=correct,
                    incorrect_count=incorrect,
                    unattempted_count=unattempted,
                    accuracy=accuracy,
                    performance=performance,
                )
            )
        return tuple(sorted(rows, key=lambda row: row.concept_id))

    @staticmethod
    def _weak_topics(topics: Sequence[TopicPerformance]) -> tuple[WeakTopic, ...]:
        weak = []
        for topic in topics:
            if topic.performance is not PerformanceBand.WEAK:
                continue
            unattempted_rate = topic.unattempted_count / topic.question_count
            priority = min(1.0, (1.0 - topic.accuracy) * 0.70 + unattempted_rate * 0.30)
            reason = (
                "कमजोर accuracy"
                if topic.accuracy == 0.0
                else "कम accuracy और unattempted questions"
                if unattempted_rate > 0.0
                else "कम accuracy"
            )
            weak.append(
                WeakTopic(
                    concept_id=topic.concept_id,
                    priority_score=priority,
                    accuracy=topic.accuracy,
                    attempted_count=topic.attempted_count,
                    question_count=topic.question_count,
                    reason=reason,
                )
            )
        return tuple(sorted(weak, key=lambda item: (-item.priority_score, item.concept_id)))
