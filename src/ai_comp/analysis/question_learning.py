from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone

from ai_comp.domain.material_generation import GeneratedMCQ, GeneratedQuestionStatus
from ai_comp.domain.question_intelligence import RankedQuestionCandidate
from ai_comp.domain.test_analysis import TestAnalysis
from ai_comp.domain.learning_history import attempt_identity
from ai_comp.domain.question_learning import (
    LearnerQuestionAttemptRecord,
    LearnerQuestionHistory,
    LearnerQuestionPerformance,
    LearnerQuestionHistoryRepository,
    QuestionLearningHistoryConflictError,
    QuestionOutcomeKind,
    QuestionRecommendationPlan,
    QuestionRevisionCandidate,
    RepeatedConceptAlert,
    question_attempt_identity,
)


class QuestionLearningHistoryService:
    """Persists question-level learner outcomes for mistakes and revision."""

    def __init__(self, repository: LearnerQuestionHistoryRepository) -> None:
        self.repository = repository

    def record_analysis(
        self,
        learner_id: str,
        analysis: TestAnalysis,
        *,
        completed_at: datetime | None = None,
    ) -> tuple[LearnerQuestionAttemptRecord, ...]:
        timestamp = completed_at or datetime.now(timezone.utc)
        attempt_id = attempt_identity(learner_id, analysis.session_id)
        records = []
        for outcome in analysis.outcomes:
            kind = (
                QuestionOutcomeKind.CORRECT
                if outcome.correct
                else QuestionOutcomeKind.INCORRECT
                if outcome.attempted
                else QuestionOutcomeKind.UNATTEMPTED
            )
            records.append(
                LearnerQuestionAttemptRecord(
                    outcome_id=question_attempt_identity(
                        learner_id,
                        analysis.session_id,
                        outcome.question_id,
                    ),
                    attempt_id=attempt_id,
                    learner_id=learner_id,
                    test_id=analysis.test_id,
                    session_id=analysis.session_id,
                    question_id=outcome.question_id,
                    concept_ids=outcome.concept_ids,
                    difficulty=outcome.difficulty,
                    selected_option_key=outcome.selected_option_key,
                    correct_option_key=outcome.correct_option_key,
                    outcome=kind,
                    completed_at=timestamp,
                )
            )
        materialized = tuple(records)
        self.repository.save_outcomes(materialized)
        return materialized

    def history(
        self,
        learner_id: str,
        *,
        generated_at: datetime | None = None,
    ) -> LearnerQuestionHistory:
        outcomes = tuple(
            sorted(
                self.repository.list_outcomes(learner_id),
                key=lambda item: (
                    item.completed_at,
                    item.session_id,
                    item.question_id,
                ),
            )
        )
        by_question: dict[str, list[LearnerQuestionAttemptRecord]] = defaultdict(list)
        for item in outcomes:
            by_question[item.question_id].append(item)

        performances = tuple(
            self._aggregate_question(question_id, items)
            for question_id, items in sorted(by_question.items())
        )
        revisions = tuple(
            sorted(
                (
                    self._revision_candidate(performance, by_question[performance.question_id])
                    for performance in performances
                    if performance.mistake_count > 0
                ),
                key=lambda item: (
                    -item.last_incorrect_at.timestamp(),
                    -item.priority_score,
                    item.question_id,
                ),
            )
        )
        alerts = self._repeated_concept_alerts(outcomes)

        return LearnerQuestionHistory(
            learner_id=learner_id,
            outcomes=outcomes,
            question_performance=performances,
            revision_candidates=revisions,
            repeated_concept_alerts=alerts,
            generated_at=generated_at or datetime.now(timezone.utc),
        )

    @staticmethod
    def _aggregate_question(
        question_id: str,
        items: Sequence[LearnerQuestionAttemptRecord],
    ) -> LearnerQuestionPerformance:
        latest = items[-1]
        correct = sum(item.outcome is QuestionOutcomeKind.CORRECT for item in items)
        incorrect = sum(item.outcome is QuestionOutcomeKind.INCORRECT for item in items)
        unattempted = sum(item.outcome is QuestionOutcomeKind.UNATTEMPTED for item in items)
        attempted = correct + incorrect
        accuracy = correct / attempted if attempted else 0.0

        streak = 0
        for item in reversed(items):
            if item.outcome is QuestionOutcomeKind.INCORRECT:
                streak += 1
            else:
                break

        mistake_rate = incorrect / len(items)
        repeat_signal = min(1.0, incorrect / 3.0)
        streak_signal = min(1.0, streak / 3.0)
        priority = min(
            1.0,
            0.50 * mistake_rate
            + 0.30 * streak_signal
            + 0.20 * repeat_signal,
        )
        return LearnerQuestionPerformance(
            question_id=question_id,
            concept_ids=latest.concept_ids,
            difficulty=latest.difficulty,
            test_count=len({item.session_id for item in items}),
            attempt_count=attempted,
            correct_count=correct,
            incorrect_count=incorrect,
            unattempted_count=unattempted,
            accuracy=accuracy,
            last_outcome=latest.outcome,
            mistake_count=incorrect,
            mistake_streak=streak,
            priority_score=priority,
            last_seen_at=latest.completed_at,
        )

    @staticmethod
    def _revision_candidate(
        performance: LearnerQuestionPerformance,
        items: Sequence[LearnerQuestionAttemptRecord],
    ) -> QuestionRevisionCandidate:
        last_incorrect = max(
            item.completed_at
            for item in items
            if item.outcome is QuestionOutcomeKind.INCORRECT
        )
        reason = (
            "repeated mistake across tests"
            if performance.mistake_count >= 2
            else "previously answered incorrectly"
        )
        return QuestionRevisionCandidate(
            question_id=performance.question_id,
            concept_ids=performance.concept_ids,
            difficulty=performance.difficulty,
            priority_score=performance.priority_score,
            mistake_count=performance.mistake_count,
            mistake_streak=performance.mistake_streak,
            last_incorrect_at=last_incorrect,
            reason=reason,
        )

    @staticmethod
    def _repeated_concept_alerts(
        outcomes: Sequence[LearnerQuestionAttemptRecord],
    ) -> tuple[RepeatedConceptAlert, ...]:
        concept_rows: dict[str, list[LearnerQuestionAttemptRecord]] = defaultdict(list)
        for outcome in outcomes:
            for concept_id in outcome.concept_ids:
                concept_rows[concept_id].append(outcome)

        alerts: list[RepeatedConceptAlert] = []
        for concept_id, rows in sorted(concept_rows.items()):
            session_ids = {row.session_id for row in rows}
            if len(session_ids) < 2:
                continue
            weak_sessions = {
                row.session_id
                for row in rows
                if row.outcome is not QuestionOutcomeKind.CORRECT
            }
            correct = sum(row.outcome is QuestionOutcomeKind.CORRECT for row in rows)
            incorrect = sum(row.outcome is QuestionOutcomeKind.INCORRECT for row in rows)
            unattempted = sum(row.outcome is QuestionOutcomeKind.UNATTEMPTED for row in rows)
            attempted = correct + incorrect
            accuracy = correct / attempted if attempted else 0.0
            if len(weak_sessions) < 2 or accuracy >= 0.75:
                continue

            weak_ratio = len(weak_sessions) / len(session_ids)
            priority = min(
                1.0,
                (1.0 - accuracy) * 0.65 + weak_ratio * 0.35,
            )
            reason = (
                "concept repeated with weak performance across multiple tests"
            )
            alerts.append(
                RepeatedConceptAlert(
                    concept_id=concept_id,
                    test_count=len(session_ids),
                    weak_test_count=len(weak_sessions),
                    question_count=len(rows),
                    attempted_count=attempted,
                    correct_count=correct,
                    incorrect_count=incorrect,
                    unattempted_count=unattempted,
                    accuracy=accuracy,
                    priority_score=priority,
                    reason=reason,
                )
            )

        alerts.sort(
            key=lambda item: (
                -item.priority_score,
                -item.test_count,
                item.concept_id,
            )
        )
        return tuple(alerts)


class PersonalizedQuestionRecommendationService:
    """Uses prior mistakes and repeated concepts without replacing Phase 6.6 ranking."""

    def recommend(
        self,
        history: LearnerQuestionHistory,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        *,
        question_count: int,
        revision_only: bool = False,
        exclude_question_ids: Sequence[str] = (),
    ) -> QuestionRecommendationPlan:
        if question_count < 1:
            raise ValueError("question_count must be positive")

        accepted = {
            question.generated_question_id: question
            for question in questions
            if question.status is GeneratedQuestionStatus.ACCEPTED
        }
        candidate_by_id: dict[str, RankedQuestionCandidate] = {}
        for candidate in candidates:
            if candidate.question_id in candidate_by_id:
                raise ValueError("ranked candidates must have unique question IDs")
            if candidate.question_id not in accepted:
                raise ValueError("candidate must reference an accepted question")
            candidate_by_id[candidate.question_id] = candidate

        excluded = set(exclude_question_ids)
        revision_by_id = {
            item.question_id: item
            for item in history.revision_candidates
            if item.question_id not in excluded
            and item.question_id in candidate_by_id
        }
        alert_priority = {
            item.concept_id: item.priority_score
            for item in history.repeated_concept_alerts
        }

        revision_slots = (
            question_count
            if revision_only
            else min(
                question_count,
                max(1, int(question_count * 0.40 + 0.999999)),
            )
        )

        selected: list[RankedQuestionCandidate] = []
        selected_ids: set[str] = set()
        revision_selected: list[str] = []

        revision_pool = sorted(
            (
                candidate
                for question_id, candidate in candidate_by_id.items()
                if question_id in revision_by_id
            ),
            key=lambda candidate: (
                -revision_by_id[candidate.question_id].priority_score,
                -revision_by_id[candidate.question_id].mistake_count,
                candidate.rank,
                candidate.question_id,
            ),
        )
        for candidate in revision_pool:
            if len(selected) >= revision_slots:
                break
            selected.append(candidate)
            selected_ids.add(candidate.question_id)
            revision_selected.append(candidate.question_id)

        remaining = [
            candidate
            for candidate in candidate_by_id.values()
            if candidate.question_id not in selected_ids
            and candidate.question_id not in excluded
        ]
        remaining.sort(
            key=lambda candidate: (
                0
                if any(
                    concept_id in alert_priority
                    for concept_id in accepted[candidate.question_id].concept_ids
                )
                else 1,
                -max(
                    (
                        alert_priority[concept_id]
                        for concept_id in accepted[candidate.question_id].concept_ids
                        if concept_id in alert_priority
                    ),
                    default=0.0,
                ),
                -candidate.score.selection_score,
                -candidate.score.importance_score,
                -candidate.score.novelty_score,
                candidate.rank,
                candidate.question_id,
            )
        )
        for candidate in remaining:
            if len(selected) >= question_count:
                break
            selected.append(candidate)

        if len(selected) < question_count:
            raise ValueError("not enough accepted ranked questions for recommendation")

        ordered = tuple(
            candidate.__class__(
                question_id=candidate.question_id,
                score=candidate.score,
                rank=index,
            )
            for index, candidate in enumerate(selected[:question_count], start=1)
        )
        selected_ids_tuple = tuple(candidate.question_id for candidate in ordered)
        focus_alerts = tuple(
            concept_id
            for concept_id, _ in sorted(
                alert_priority.items(),
                key=lambda item: (-item[1], item[0]),
            )
            if any(
                concept_id in accepted[question_id].concept_ids
                for question_id in selected_ids_tuple
            )
        )
        return QuestionRecommendationPlan(
            question_ids=selected_ids_tuple,
            ranked_candidates=ordered,
            revision_question_ids=tuple(revision_selected),
            alert_concept_ids=focus_alerts,
        )
