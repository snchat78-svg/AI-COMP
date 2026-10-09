from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from ai_comp.analysis.completed_test_feedback import CompletedTestFeedback
from ai_comp.domain.learning_history import LearningTrend
from ai_comp.domain.question_learning import LearnerQuestionAttemptRecord, QuestionOutcomeKind
from ai_comp.domain.study_schedule import StudySchedule, ScheduledStudyTask
from ai_comp.domain.study_schedule_execution import (
    StudyTaskExecution,
    StudyTaskExecutionRepository,
    StudyTaskExecutionStatus,
)
from ai_comp.domain.study_outcome_feedback import (
    OutcomeEvidenceKind,
    StudyOutcomeFeedbackReport,
    StudyTaskOutcome,
)


@dataclass(frozen=True)
class StudyOutcomeFeedbackPolicy:
    minimum_baseline_attempts: int = 2
    minimum_follow_up_attempts: int = 2
    stable_threshold_percentage_points: float = 5.0

    def __post_init__(self) -> None:
        if self.minimum_baseline_attempts < 1:
            raise ValueError("minimum_baseline_attempts must be positive")
        if self.minimum_follow_up_attempts < 1:
            raise ValueError("minimum_follow_up_attempts must be positive")
        if not 0.0 < self.stable_threshold_percentage_points <= 100.0:
            raise ValueError("stable threshold must be greater than 0 and at most 100")


class StudyOutcomeFeedbackService:
    """Correlates pre-test study execution with a real completed assessment.

    Correlation is descriptive rather than causal. Question-level outcomes remain
    sourced from CompletedTestFeedback and execution observations remain sourced
    from StudyTaskExecutionRepository; nothing is written back as synthetic mastery.
    """

    def __init__(
        self,
        repository: StudyTaskExecutionRepository,
        *,
        policy: StudyOutcomeFeedbackPolicy | None = None,
    ) -> None:
        self.repository = repository
        self.policy = policy or StudyOutcomeFeedbackPolicy()

    def evaluate(
        self,
        schedule: StudySchedule,
        completed_feedback: CompletedTestFeedback,
        *,
        generated_at: datetime | None = None,
    ) -> StudyOutcomeFeedbackReport:
        if completed_feedback.learner_id != schedule.learner_id:
            raise ValueError("completed test learner does not match schedule")
        assessed_at = completed_feedback.attempt.completed_at
        if assessed_at.tzinfo is None or assessed_at.utcoffset() is None:
            raise ValueError("completed test timestamp must be timezone-aware")
        if completed_feedback.session.session_id != completed_feedback.attempt.session_id:
            raise ValueError("completed test session does not match persisted attempt")
        if completed_feedback.analysis.session_id != completed_feedback.session.session_id:
            raise ValueError("analysis does not match completed test session")
        if completed_feedback.result.session_id != completed_feedback.session.session_id:
            raise ValueError("result does not match completed test session")

        report_time = generated_at or datetime.now(timezone.utc)
        if report_time.tzinfo is None or report_time.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        if report_time < assessed_at:
            raise ValueError("generated_at cannot precede the completed assessment")

        task_by_id: dict[str, ScheduledStudyTask] = {
            task.task_id: task for day in schedule.days for task in day.tasks
        }
        events = self.repository.list_for_schedule(schedule.schedule_id, schedule.learner_id)
        if any(
            event.schedule_id != schedule.schedule_id
            or event.learner_id != schedule.learner_id
            or event.task_id not in task_by_id
            for event in events
        ):
            raise ValueError("execution repository returned an event outside this schedule")

        # An execution after the test cannot be credited to that test. For each
        # task, the latest observation at or before the assessment is authoritative.
        before_assessment = tuple(
            event for event in events if event.occurred_at < assessed_at
        )
        events_by_task: dict[str, list[StudyTaskExecution]] = {}
        for event in before_assessment:
            events_by_task.setdefault(event.task_id, []).append(event)

        outcomes = tuple(
            self._evaluate_task(
                task=task,
                events=tuple(sorted(
                    events_by_task.get(task.task_id, ()),
                    key=lambda row: (row.occurred_at, row.event_id),
                )),
                feedback=completed_feedback,
            )
            for task in sorted(task_by_id.values(), key=lambda item: item.task_id)
            if events_by_task.get(task.task_id)
        )
        return StudyOutcomeFeedbackReport(
            learner_id=schedule.learner_id,
            schedule_id=schedule.schedule_id,
            assessment_session_id=completed_feedback.session.session_id,
            assessed_at=assessed_at,
            outcomes=outcomes,
            generated_at=report_time,
        )

    def _evaluate_task(
        self,
        *,
        task: ScheduledStudyTask,
        events: tuple[StudyTaskExecution, ...],
        feedback: CompletedTestFeedback,
    ) -> StudyTaskOutcome:
        latest = events[-1]
        active_events = tuple(
            event for event in events
            if event.status in {
                StudyTaskExecutionStatus.PARTIAL,
                StudyTaskExecutionStatus.COMPLETED,
            }
        )
        if latest.status not in {
            StudyTaskExecutionStatus.PARTIAL,
            StudyTaskExecutionStatus.COMPLETED,
        }:
            return self._empty_outcome(task, events, latest, feedback)

        task_start = active_events[0].occurred_at if active_events else latest.occurred_at
        studied_question_ids = set()
        for event in active_events:
            if event.status is StudyTaskExecutionStatus.COMPLETED:
                studied_question_ids.update(task.question_ids)
            else:
                studied_question_ids.update(event.completed_question_ids)
        task_concepts = set(task.concept_ids)
        if not task_concepts and studied_question_ids:
            task_concepts.update(
                concept_id
                for record in feedback.question_history.outcomes
                if record.question_id in studied_question_ids
                for concept_id in record.concept_ids
            )

        assessment_outcomes = tuple(feedback.analysis.outcomes)
        direct = tuple(
            outcome for outcome in assessment_outcomes
            if outcome.question_id in studied_question_ids
        )
        concept_matched = tuple(
            outcome for outcome in assessment_outcomes
            if task_concepts and task_concepts.intersection(outcome.concept_ids)
        )
        if direct:
            matched = direct
            evidence_kind = OutcomeEvidenceKind.DIRECT_QUESTION_MATCH
        elif concept_matched:
            matched = concept_matched
            evidence_kind = OutcomeEvidenceKind.CONCEPT_OVERLAP
        else:
            matched = ()
            evidence_kind = OutcomeEvidenceKind.NO_RELATED_EVIDENCE

        linked_concepts = tuple(sorted({
            concept_id for outcome in matched for concept_id in outcome.concept_ids
            if not task_concepts or concept_id in task_concepts
        }))
        if not linked_concepts:
            linked_concepts = tuple(sorted(task_concepts))

        baseline_source = tuple(
            record for record in feedback.question_history.outcomes
            if record.session_id != feedback.session.session_id
            and record.completed_at < task_start
        )
        baseline, follow_up, comparison_trend, delta = self._compare(
            task_concepts=set(linked_concepts) or task_concepts,
            studied_question_ids=studied_question_ids,
            baseline_source=baseline_source,
            current_outcomes=matched,
        )
        question_count = len(matched)
        attempted = sum(outcome.attempted for outcome in matched)
        correct = sum(outcome.attempted and outcome.correct for outcome in matched)
        incorrect = attempted - correct
        unattempted = question_count - attempted
        accuracy = (100.0 * correct / attempted) if attempted else None

        if evidence_kind is OutcomeEvidenceKind.NO_RELATED_EVIDENCE:
            interpretation = (
                "This completed task has no question or concept overlap with the "
                "assessment, so no learning outcome is attributed to it."
            )
        elif comparison_trend is LearningTrend.INSUFFICIENT_DATA:
            interpretation = (
                "Related assessment evidence exists, but the pre-study baseline or "
                "follow-up sample is too small for a reliable trend comparison."
            )
        else:
            interpretation = (
                f"Observed follow-up accuracy changed by {delta:.2f} percentage "
                "points against the pre-study baseline. This is an association, "
                "not proof that the task caused the change; test difficulty and "
                "question composition may differ."
            )

        return StudyTaskOutcome(
            task_id=task.task_id,
            task_kind=task.kind,
            execution_event_ids=tuple(event.event_id for event in events),
            execution_status=latest.status,
            evidence_kind=evidence_kind,
            assessment_session_id=feedback.session.session_id,
            assessed_at=feedback.attempt.completed_at,
            related_question_ids=tuple(outcome.question_id for outcome in matched),
            related_concept_ids=linked_concepts,
            question_count=question_count,
            attempted_count=attempted,
            correct_count=correct,
            incorrect_count=incorrect,
            unattempted_count=unattempted,
            accuracy_percentage=accuracy,
            baseline_attempted_count=baseline[0],
            baseline_accuracy_percentage=baseline[1],
            follow_up_attempted_count=follow_up[0],
            follow_up_accuracy_percentage=follow_up[1],
            delta_percentage_points=delta,
            trend=comparison_trend,
            interpretation=interpretation,
        )

    def _compare(
        self,
        *,
        task_concepts: set[str],
        studied_question_ids: set[str],
        baseline_source: tuple[LearnerQuestionAttemptRecord, ...],
        current_outcomes: tuple[object, ...],
    ) -> tuple[tuple[int, float | None], tuple[int, float | None], LearningTrend, float | None]:
        baseline_records = tuple(
            record for record in baseline_source
            if (
                bool(task_concepts.intersection(record.concept_ids))
                or (not task_concepts and record.question_id in studied_question_ids)
            )
        )
        baseline_attempted = tuple(
            record for record in baseline_records
            if record.outcome is not QuestionOutcomeKind.UNATTEMPTED
        )
        baseline_correct = sum(
            record.outcome is QuestionOutcomeKind.CORRECT
            for record in baseline_attempted
        )
        baseline_accuracy = (
            100.0 * baseline_correct / len(baseline_attempted)
            if baseline_attempted else None
        )

        follow_up_attempted = tuple(
            outcome for outcome in current_outcomes if getattr(outcome, "attempted")
        )
        follow_up_correct = sum(
            bool(getattr(outcome, "correct")) for outcome in follow_up_attempted
        )
        follow_up_accuracy = (
            100.0 * follow_up_correct / len(follow_up_attempted)
            if follow_up_attempted else None
        )
        baseline_summary = (len(baseline_attempted), baseline_accuracy)
        follow_up_summary = (len(follow_up_attempted), follow_up_accuracy)

        if (
            baseline_accuracy is None
            or follow_up_accuracy is None
            or len(baseline_attempted) < self.policy.minimum_baseline_attempts
            or len(follow_up_attempted) < self.policy.minimum_follow_up_attempts
        ):
            return baseline_summary, follow_up_summary, LearningTrend.INSUFFICIENT_DATA, None

        delta = follow_up_accuracy - baseline_accuracy
        if delta > self.policy.stable_threshold_percentage_points:
            trend = LearningTrend.IMPROVING
        elif delta < -self.policy.stable_threshold_percentage_points:
            trend = LearningTrend.DECLINING
        else:
            trend = LearningTrend.STABLE
        return baseline_summary, follow_up_summary, trend, delta

    @staticmethod
    def _empty_outcome(
        task: ScheduledStudyTask,
        events: tuple[StudyTaskExecution, ...],
        latest: StudyTaskExecution,
        feedback: CompletedTestFeedback,
    ) -> StudyTaskOutcome:
        label = (
            "The latest task event is skipped or postponed; it is not treated as "
            "completed study and receives no learning-outcome attribution."
        )
        return StudyTaskOutcome(
            task_id=task.task_id,
            task_kind=task.kind,
            execution_event_ids=tuple(event.event_id for event in events),
            execution_status=latest.status,
            evidence_kind=OutcomeEvidenceKind.NO_RELATED_EVIDENCE,
            assessment_session_id=feedback.session.session_id,
            assessed_at=feedback.attempt.completed_at,
            related_question_ids=(),
            related_concept_ids=task.concept_ids,
            question_count=0,
            attempted_count=0,
            correct_count=0,
            incorrect_count=0,
            unattempted_count=0,
            accuracy_percentage=None,
            baseline_attempted_count=0,
            baseline_accuracy_percentage=None,
            follow_up_attempted_count=0,
            follow_up_accuracy_percentage=None,
            delta_percentage_points=None,
            trend=LearningTrend.INSUFFICIENT_DATA,
            interpretation=label,
        )


__all__ = ["StudyOutcomeFeedbackPolicy", "StudyOutcomeFeedbackService"]
