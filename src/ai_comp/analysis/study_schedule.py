from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone

from ai_comp.analysis.spaced_revision import SpacedRevisionService
from ai_comp.domain.learning_history import LearnerLearningHistory
from ai_comp.domain.material_generation import GeneratedMCQ, GeneratedQuestionStatus
from ai_comp.domain.preparation_guidance import PreparationGuidance
from ai_comp.domain.question_learning import LearnerQuestionHistory
from ai_comp.domain.spaced_revision import ReviewStatus
from ai_comp.domain.study_schedule import (
    ScheduledStudyTask,
    StudyDayPlan,
    StudySchedule,
    StudySchedulePolicy,
    StudyTaskKind,
    UnscheduledStudyWork,
)


_TITLES = {
    StudyTaskKind.REVIEW_DUE_REVISION: "Review due spaced-revision questions",
    StudyTaskKind.REVIEW_PREVIOUS_MISTAKES: "Review previous mistakes",
    StudyTaskKind.STUDY_WEAK_TOPIC: "Study priority topics",
    StudyTaskKind.PRACTICE_QUESTIONS: "Practice selected questions",
}
_REASONS = {
    StudyTaskKind.REVIEW_DUE_REVISION: (
        "The existing spaced-revision engine marks these questions as due."
    ),
    StudyTaskKind.REVIEW_PREVIOUS_MISTAKES: (
        "The personalized plan selected these questions from recorded mistake history."
    ),
    StudyTaskKind.STUDY_WEAK_TOPIC: (
        "The existing personalized plan selected these concepts using learner-performance evidence."
    ),
    StudyTaskKind.PRACTICE_QUESTIONS: (
        "These accepted questions remain in the existing personalized plan after revision work is reserved."
    ),
}


@dataclass
class _WorkItem:
    work_id: str
    kind: StudyTaskKind
    remaining_minutes: int
    priority_score: float
    concept_ids: tuple[str, ...]
    question_ids: tuple[str, ...]
    deadline_date: date
    allow_split: bool


@dataclass(frozen=True)
class _ScheduledChunk:
    kind: StudyTaskKind
    scheduled_date: date
    minutes: int
    priority_score: float
    concept_ids: tuple[str, ...]
    question_ids: tuple[str, ...]
    deadline_date: date


class StudyScheduleService:
    """Builds daily/weekly plans by composing established learner-intelligence services.

    Question matching and selection remain owned by the existing preparation plan.
    This service schedules only accepted questions and evidence-backed concept IDs;
    it does not invent exam history, questions, or learner performance.
    """

    def __init__(
        self,
        *,
        policy: StudySchedulePolicy | None = None,
        spaced_revision_service: SpacedRevisionService | None = None,
    ) -> None:
        self.policy = policy or StudySchedulePolicy()
        self.spaced_revision_service = spaced_revision_service or SpacedRevisionService()

    def build_schedule(
        self,
        learner_id: str,
        *,
        guidance: PreparationGuidance,
        history: LearnerLearningHistory,
        question_history: LearnerQuestionHistory,
        questions: Sequence[GeneratedMCQ],
        daily_minutes: int,
        weekday_minutes: Mapping[int, int] | None = None,
        start_date: date | None = None,
        horizon_days: int = 7,
        exam_date: date | None = None,
        as_of: datetime | None = None,
    ) -> StudySchedule:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if guidance.learner_id != learner_id:
            raise ValueError("preparation guidance learner does not match")
        if history.learner_id != learner_id:
            raise ValueError("learning history learner does not match")
        if question_history.learner_id != learner_id:
            raise ValueError("question history learner does not match")
        if isinstance(daily_minutes, bool) or not isinstance(daily_minutes, int) or daily_minutes < 0:
            raise ValueError("daily_minutes must be a non-negative integer")
        if isinstance(horizon_days, bool) or not isinstance(horizon_days, int) or not 1 <= horizon_days <= 366:
            raise ValueError("horizon_days must be between 1 and 366")

        reference_time = as_of or datetime.now(timezone.utc)
        if reference_time.tzinfo is None or reference_time.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        planning_start = start_date or reference_time.date()
        if exam_date is not None and exam_date < planning_start:
            raise ValueError("exam_date cannot precede start_date")

        weekday_overrides = dict(weekday_minutes or {})
        for weekday, minutes in weekday_overrides.items():
            if isinstance(weekday, bool) or not isinstance(weekday, int) or not 0 <= weekday <= 6:
                raise ValueError("weekday availability keys must be integers from 0 to 6")
            if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes < 0:
                raise ValueError("weekday availability must be non-negative integer minutes")

        plan = guidance.preparation_plan
        plan_question_ids = tuple(plan.question_ids)
        if len(plan_question_ids) != len(set(plan_question_ids)):
            raise ValueError("preparation plan question IDs must be unique")
        question_by_id: dict[str, GeneratedMCQ] = {}
        for question in questions:
            question_id = question.generated_question_id
            if question_id in question_by_id:
                raise ValueError("provided questions must have unique IDs")
            if question.status is GeneratedQuestionStatus.ACCEPTED:
                question_by_id[question_id] = question
        if not set(plan_question_ids).issubset(question_by_id):
            raise ValueError(
                "preparation plan references missing or non-accepted questions"
            )
        if len(plan.focus_concept_ids) != len(set(plan.focus_concept_ids)):
            raise ValueError("preparation plan focus concepts must be unique")

        horizon_end = planning_start + timedelta(days=horizon_days - 1)
        planning_end = min(horizon_end, exam_date) if exam_date is not None else horizon_end
        last_study_date = (
            min(planning_end, exam_date - timedelta(days=1))
            if exam_date is not None
            else planning_end
        )
        default_deadline = last_study_date

        items = self._build_work_items(
            guidance=guidance,
            history=history,
            question_history=question_history,
            question_by_id=question_by_id,
            planning_start=planning_start,
            default_deadline=default_deadline,
            exam_date=exam_date,
            as_of=reference_time,
        )

        day_specs: list[tuple[date, int]] = []
        current_date = planning_start
        while current_date <= planning_end:
            available = 0 if current_date == exam_date else weekday_overrides.get(
                current_date.weekday(), daily_minutes
            )
            day_specs.append((current_date, available))
            current_date += timedelta(days=1)

        chunks_by_day: dict[date, list[_ScheduledChunk]] = {
            day: [] for day, _ in day_specs
        }
        # Stable evidence-based ordering: due reviews first, then higher-priority
        # work. Near an exam, practice work receives a configurable urgency boost.
        items.sort(key=lambda item: self._work_sort_key(item))

        for study_date, available_minutes in day_specs:
            free_minutes = available_minutes
            while free_minutes > 0:
                eligible = next(
                    (
                        item for item in items
                        if item.remaining_minutes > 0
                        and (
                            item.remaining_minutes <= free_minutes
                            or (
                                item.allow_split
                                and free_minutes >= self.policy.minimum_block_minutes
                            )
                        )
                    ),
                    None,
                )
                if eligible is None:
                    break

                if eligible.remaining_minutes <= free_minutes:
                    allocated = eligible.remaining_minutes
                else:
                    allocated = min(
                        eligible.remaining_minutes,
                        free_minutes,
                        self.policy.maximum_block_minutes,
                    )
                if allocated < 1:
                    break
                chunks_by_day[study_date].append(_ScheduledChunk(
                    kind=eligible.kind,
                    scheduled_date=study_date,
                    minutes=allocated,
                    priority_score=eligible.priority_score,
                    concept_ids=eligible.concept_ids,
                    question_ids=eligible.question_ids,
                    deadline_date=eligible.deadline_date,
                ))
                eligible.remaining_minutes -= allocated
                free_minutes -= allocated

        days: list[StudyDayPlan] = []
        for study_date, available_minutes in day_specs:
            scheduled_tasks = self._materialize_day_tasks(
                study_date,
                chunks_by_day[study_date],
            )
            days.append(StudyDayPlan(
                study_date=study_date,
                available_minutes=available_minutes,
                tasks=scheduled_tasks,
            ))

        unscheduled = tuple(
            UnscheduledStudyWork(
                work_id=item.work_id,
                kind=item.kind,
                title=_TITLES[item.kind],
                remaining_minutes=item.remaining_minutes,
                priority_score=item.priority_score,
                reason=_REASONS[item.kind],
                unscheduled_reason=(
                    "The requested availability window did not have enough usable time "
                    "to place this remaining work."
                ),
                concept_ids=item.concept_ids,
                question_ids=item.question_ids,
                deadline_date=item.deadline_date,
            )
            for item in items
            if item.remaining_minutes > 0
        )

        return StudySchedule(
            learner_id=learner_id,
            start_date=planning_start,
            end_date=planning_end,
            exam_date=exam_date,
            days=tuple(days),
            unscheduled_work=unscheduled,
            generated_at=reference_time,
        )

    def _build_work_items(
        self,
        *,
        guidance: PreparationGuidance,
        history: LearnerLearningHistory,
        question_history: LearnerQuestionHistory,
        question_by_id: Mapping[str, GeneratedMCQ],
        planning_start: date,
        default_deadline: date,
        exam_date: date | None,
        as_of: datetime,
    ) -> list[_WorkItem]:
        plan = guidance.preparation_plan
        selected_ids = set(plan.question_ids)

        selected_outcomes = tuple(
            item for item in question_history.outcomes
            if item.question_id in selected_ids
        )
        questions_with_outcomes = {
            item.question_id for item in selected_outcomes
        }
        selected_performance = tuple(
            item for item in question_history.question_performance
            if item.question_id in selected_ids
            and item.question_id in questions_with_outcomes
        )
        selected_history = replace(
            question_history,
            outcomes=selected_outcomes,
            question_performance=selected_performance,
        )
        schedules = self.spaced_revision_service.schedules(
            selected_history,
            as_of=as_of,
        )
        schedule_by_id = {item.question_id: item for item in schedules}
        planned_due_ids = set(plan.retention_due_question_ids)
        due_schedules = tuple(
            item for item in schedules
            if item.question_id in planned_due_ids
            and item.question_id in selected_ids
            and item.status is ReviewStatus.DUE
        )
        due_ids = {item.question_id for item in due_schedules}

        revision_candidates = {
            item.question_id: item
            for item in question_history.revision_candidates
        }
        question_performance = {
            item.question_id: item
            for item in question_history.question_performance
        }
        concept_by_question = {
            question_id: tuple(question_by_id[question_id].concept_ids)
            for question_id in plan.question_ids
        }
        work: list[_WorkItem] = []

        for schedule in sorted(
            due_schedules,
            key=lambda item: (
                -item.priority_score,
                -item.overdue_days,
                item.next_review_at,
                item.question_id,
            ),
        ):
            work.append(_WorkItem(
                work_id=f"{StudyTaskKind.REVIEW_DUE_REVISION.value}:{schedule.question_id}",
                kind=StudyTaskKind.REVIEW_DUE_REVISION,
                remaining_minutes=self.policy.review_minutes_per_question,
                priority_score=schedule.priority_score,
                concept_ids=concept_by_question[schedule.question_id],
                question_ids=(schedule.question_id,),
                deadline_date=max(planning_start, schedule.next_review_at.date()),
                allow_split=False,
            ))

        mistake_ids = tuple(
            question_id for question_id in plan.revision_question_ids
            if question_id not in due_ids
        )
        for question_id in sorted(
            mistake_ids,
            key=lambda value: (
                -revision_candidates[value].priority_score
                if value in revision_candidates
                else -question_performance[value].priority_score
                if value in question_performance
                else 0.0,
                value,
            ),
        ):
            revision = revision_candidates.get(question_id)
            performance = question_performance.get(question_id)
            priority = (
                revision.priority_score if revision is not None
                else performance.priority_score if performance is not None
                else 0.5
            )
            work.append(_WorkItem(
                work_id=f"{StudyTaskKind.REVIEW_PREVIOUS_MISTAKES.value}:{question_id}",
                kind=StudyTaskKind.REVIEW_PREVIOUS_MISTAKES,
                remaining_minutes=self.policy.review_minutes_per_question,
                priority_score=priority,
                concept_ids=concept_by_question[question_id],
                question_ids=(question_id,),
                deadline_date=default_deadline,
                allow_split=False,
            ))

        topic_scores: dict[str, list[float]] = {}
        for item in history.topic_performance:
            topic_scores.setdefault(item.concept_id, []).append(item.priority_score)
        for item in guidance.progress_report.topics:
            topic_scores.setdefault(item.concept_id, []).append(item.priority_score)
        for item in plan.recommendations:
            topic_scores.setdefault(item.concept_id, []).append(item.priority_score)

        for concept_id in sorted(
            plan.focus_concept_ids,
            key=lambda value: (
                -max(topic_scores.get(value, (0.5,))),
                value,
            ),
        ):
            priority = max(topic_scores.get(concept_id, (0.5,)))
            work.append(_WorkItem(
                work_id=f"{StudyTaskKind.STUDY_WEAK_TOPIC.value}:{concept_id}",
                kind=StudyTaskKind.STUDY_WEAK_TOPIC,
                remaining_minutes=self.policy.weak_topic_minutes,
                priority_score=priority,
                concept_ids=(concept_id,),
                question_ids=(),
                deadline_date=default_deadline,
                allow_split=True,
            ))

        practice_ids = tuple(
            question_id for question_id in plan.question_ids
            if question_id not in due_ids
            and question_id not in set(mistake_ids)
        )
        candidate_scores = {
            item.question_id: item.score.selection_score
            for item in plan.ranked_candidates
        }
        exam_is_close = (
            exam_date is not None
            and 0 <= (exam_date - planning_start).days
            <= self.policy.exam_urgency_window_days
        )
        for question_id in practice_ids:
            base_priority = candidate_scores.get(question_id, 0.5)
            priority = min(
                1.0,
                base_priority + (
                    self.policy.exam_urgency_bonus if exam_is_close else 0.0
                ),
            )
            work.append(_WorkItem(
                work_id=f"{StudyTaskKind.PRACTICE_QUESTIONS.value}:{question_id}",
                kind=StudyTaskKind.PRACTICE_QUESTIONS,
                remaining_minutes=self.policy.practice_minutes_per_question,
                priority_score=priority,
                concept_ids=concept_by_question[question_id],
                question_ids=(question_id,),
                deadline_date=default_deadline,
                allow_split=False,
            ))

        return work

    def _work_sort_key(self, item: _WorkItem) -> tuple[object, ...]:
        due_rank = 0 if item.kind is StudyTaskKind.REVIEW_DUE_REVISION else 1
        kind_rank = {
            StudyTaskKind.REVIEW_DUE_REVISION: 0,
            StudyTaskKind.REVIEW_PREVIOUS_MISTAKES: 1,
            StudyTaskKind.STUDY_WEAK_TOPIC: 2,
            StudyTaskKind.PRACTICE_QUESTIONS: 3,
        }[item.kind]
        return (
            due_rank,
            -item.priority_score,
            item.deadline_date,
            kind_rank,
            item.concept_ids,
            item.question_ids,
            item.work_id,
        )

    def _materialize_day_tasks(
        self,
        study_date: date,
        chunks: Sequence[_ScheduledChunk],
    ) -> tuple[ScheduledStudyTask, ...]:
        ordered = sorted(
            chunks,
            key=lambda item: (
                -item.priority_score,
                item.kind.value,
                item.deadline_date,
                item.concept_ids,
                item.question_ids,
            ),
        )
        groups: list[list[_ScheduledChunk]] = []
        for chunk in ordered:
            if (
                groups
                and groups[-1][0].kind is chunk.kind
                and sum(item.minutes for item in groups[-1]) + chunk.minutes
                <= self.policy.maximum_block_minutes
            ):
                groups[-1].append(chunk)
            else:
                groups.append([chunk])

        tasks: list[ScheduledStudyTask] = []
        for index, group in enumerate(groups, start=1):
            kind = group[0].kind
            concept_ids = tuple(dict.fromkeys(
                concept
                for chunk in group
                for concept in chunk.concept_ids
            ))
            question_ids = tuple(dict.fromkeys(
                question_id
                for chunk in group
                for question_id in chunk.question_ids
            ))
            tasks.append(ScheduledStudyTask(
                task_id=f"{study_date.isoformat()}-{index:02d}-{kind.value.lower()}",
                kind=kind,
                scheduled_date=study_date,
                title=_TITLES[kind],
                estimated_minutes=sum(chunk.minutes for chunk in group),
                priority_score=max(chunk.priority_score for chunk in group),
                reason=_REASONS[kind],
                concept_ids=concept_ids,
                question_ids=question_ids,
                deadline_date=min(chunk.deadline_date for chunk in group),
            ))
        return tuple(sorted(
            tasks,
            key=lambda item: (-item.priority_score, item.kind.value, item.task_id),
        ))


__all__ = ["StudyScheduleService"]
