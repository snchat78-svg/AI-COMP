from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from ai_comp.domain.material_generation import GeneratedMCQ, GeneratedQuestionStatus
from ai_comp.domain.question_intelligence import RankedQuestionCandidate
from ai_comp.domain.question_learning import LearnerQuestionHistory, QuestionOutcomeKind
from ai_comp.domain.spaced_revision import (
    LearnerQuestionReviewSchedule,
    ReviewStatus,
    SpacedRevisionPolicy,
    TimeAwareQuestionPlan,
    next_interval_days,
)


class SpacedRevisionService:
    """Derives a deterministic review schedule from durable question outcomes."""

    def __init__(self, policy: SpacedRevisionPolicy | None = None) -> None:
        self.policy = policy or SpacedRevisionPolicy()

    def schedules(
        self,
        history: LearnerQuestionHistory,
        *,
        as_of: datetime | None = None,
    ) -> tuple[LearnerQuestionReviewSchedule, ...]:
        now = as_of or datetime.now(timezone.utc)
        rows = []

        for performance in history.question_performance:
            outcomes = [
                outcome
                for outcome in history.outcomes
                if outcome.question_id == performance.question_id
            ]
            outcomes.sort(
                key=lambda item: (
                    item.completed_at,
                    item.session_id,
                    item.question_id,
                )
            )
            latest = outcomes[-1]
            correct_streak = 0
            for outcome in reversed(outcomes):
                if outcome.outcome is QuestionOutcomeKind.CORRECT:
                    correct_streak += 1
                else:
                    break

            interval = next_interval_days(
                correct_streak,
                policy=self.policy,
            )
            if latest.outcome is not QuestionOutcomeKind.CORRECT:
                interval = self.policy.first_interval_days

            next_review_at = latest.completed_at + timedelta(days=interval)
            overdue_seconds = max(
                0.0, (now - next_review_at).total_seconds()
            )
            overdue_days = overdue_seconds / 86400.0
            status = (
                ReviewStatus.DUE
                if now >= next_review_at
                else ReviewStatus.UPCOMING
            )
            mistake_signal = min(1.0, performance.mistake_count / 3.0)
            overdue_signal = (
                min(1.0, overdue_days / max(float(interval), 1.0))
                if status is ReviewStatus.DUE
                else 0.0
            )
            repetition_signal = min(1.0, performance.test_count / 3.0)
            priority = min(
                1.0,
                self.policy.mistake_weight * mistake_signal
                + self.policy.overdue_weight * max(0.5, overdue_signal)
                + self.policy.repetition_weight * repetition_signal,
            )
            rows.append(
                LearnerQuestionReviewSchedule(
                    learner_id=history.learner_id,
                    question_id=performance.question_id,
                    last_review_at=latest.completed_at,
                    next_review_at=next_review_at,
                    interval_days=interval,
                    correct_streak=correct_streak,
                    mistake_count=performance.mistake_count,
                    mistake_streak=performance.mistake_streak,
                    status=status,
                    overdue_days=overdue_days,
                    priority_score=priority,
                )
            )

        return tuple(
            sorted(
                rows,
                key=lambda item: (
                    0 if item.status is ReviewStatus.DUE else 1,
                    -item.priority_score,
                    item.next_review_at,
                    item.question_id,
                ),
            )
        )


class TimeAwareQuestionSelector:
    """Selects due/spaced-review questions without replacing Phase 6.6 ranking."""

    def __init__(self, policy: SpacedRevisionPolicy | None = None) -> None:
        self.service = SpacedRevisionService(policy)

    def select(
        self,
        history: LearnerQuestionHistory,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        *,
        question_count: int,
        as_of: datetime | None = None,
        exclude_question_ids: Sequence[str] = (),
        due_ratio: float = 0.60,
    ) -> TimeAwareQuestionPlan:
        if question_count < 1:
            raise ValueError("question_count must be positive")
        if not 0.0 <= due_ratio <= 1.0:
            raise ValueError("due_ratio must be between 0 and 1")

        reference_time = as_of or datetime.now(timezone.utc)
        accepted = {
            item.generated_question_id: item
            for item in questions
            if item.status is GeneratedQuestionStatus.ACCEPTED
        }
        candidate_by_id: dict[str, RankedQuestionCandidate] = {}
        for candidate in candidates:
            if candidate.question_id in candidate_by_id:
                raise ValueError("ranked candidates must have unique question IDs")
            if candidate.question_id not in accepted:
                raise ValueError("candidate must reference an accepted question")
            candidate_by_id[candidate.question_id] = candidate

        excluded = set(exclude_question_ids)
        schedule_by_id = {
            schedule.question_id: schedule
            for schedule in self.service.schedules(
                history,
                as_of=reference_time,
            )
            if schedule.question_id not in excluded
        }

        due_slots = min(
            question_count,
            max(0, int(question_count * due_ratio + 0.999999)),
        )
        due_candidates = [
            candidate
            for question_id, candidate in candidate_by_id.items()
            if question_id in schedule_by_id
            and schedule_by_id[question_id].status is ReviewStatus.DUE
        ]
        due_candidates.sort(
            key=lambda candidate: (
                -schedule_by_id[candidate.question_id].priority_score,
                -schedule_by_id[candidate.question_id].overdue_days,
                -candidate.score.selection_score,
                candidate.rank,
                candidate.question_id,
            )
        )

        selected: list[RankedQuestionCandidate] = []
        due_selected: list[str] = []
        selected_ids: set[str] = set()

        for candidate in due_candidates[:due_slots]:
            selected.append(candidate)
            selected_ids.add(candidate.question_id)
            due_selected.append(candidate.question_id)

        remaining = [
            candidate
            for candidate in candidate_by_id.values()
            if candidate.question_id not in selected_ids
            and candidate.question_id not in excluded
        ]
        remaining.sort(
            key=lambda candidate: (
                0
                if candidate.question_id in schedule_by_id
                and schedule_by_id[candidate.question_id].status is ReviewStatus.UPCOMING
                else 1,
                schedule_by_id[candidate.question_id].next_review_at
                if candidate.question_id in schedule_by_id
                else reference_time,
                -(
                    schedule_by_id[candidate.question_id].priority_score
                    if candidate.question_id in schedule_by_id
                    else 0.0
                ),
                -candidate.score.selection_score,
                -candidate.score.importance_score,
                candidate.rank,
                candidate.question_id,
            )
        )
        selected.extend(
            remaining[: max(0, question_count - len(selected))]
        )

        if len(selected) < question_count:
            raise ValueError(
                "not enough accepted ranked questions for time-aware review"
            )

        ordered = tuple(
            candidate.__class__(
                question_id=candidate.question_id,
                score=candidate.score,
                rank=index,
            )
            for index, candidate in enumerate(
                selected[:question_count],
                start=1,
            )
        )
        selected_ids = {candidate.question_id for candidate in ordered}
        focus_ids = tuple(
            question_id
            for question_id in due_selected
            if question_id in selected_ids
        )
        selected_schedules = tuple(
            schedule_by_id[question_id]
            for question_id in (
                candidate.question_id for candidate in ordered
            )
            if question_id in schedule_by_id
        )
        return TimeAwareQuestionPlan(
            question_ids=tuple(candidate.question_id for candidate in ordered),
            ranked_candidates=ordered,
            due_question_ids=focus_ids,
            focus_question_ids=focus_ids,
            schedules=selected_schedules,
        )
