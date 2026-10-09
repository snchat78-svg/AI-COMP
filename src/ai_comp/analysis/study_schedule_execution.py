from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from ai_comp.domain.adaptive_study_strategy import (
    AdaptiveStudyStrategyReport,
    StudyStrategyAction,
    StudyTaskStrategyAdjustment,
)
from ai_comp.domain.study_schedule import (
    ScheduledStudyTask, StudyDayPlan, StudySchedule, StudySchedulePolicy,
    StudyTaskKind, UnscheduledStudyWork,
)
from ai_comp.domain.study_schedule_execution import (
    StudyTaskExecution, StudyTaskExecutionConflictError,
    StudyTaskExecutionRepository, StudyTaskExecutionStatus,
)

_TITLES = {
    StudyTaskKind.REVIEW_DUE_REVISION: "Review due spaced-revision questions",
    StudyTaskKind.REVIEW_PREVIOUS_MISTAKES: "Review previous mistakes",
    StudyTaskKind.STUDY_WEAK_TOPIC: "Study priority topics",
    StudyTaskKind.PRACTICE_QUESTIONS: "Practice selected questions",
}
_REASONS = {
    StudyTaskKind.REVIEW_DUE_REVISION: "Carried forward from the learner's spaced-revision plan.",
    StudyTaskKind.REVIEW_PREVIOUS_MISTAKES: "Carried forward from recorded previous-mistake history.",
    StudyTaskKind.STUDY_WEAK_TOPIC: "Carried forward from evidence-backed personalized topic priorities.",
    StudyTaskKind.PRACTICE_QUESTIONS: "Carried forward from the accepted-question preparation plan.",
}


@dataclass
class _Work:
    work_id: str
    kind: StudyTaskKind
    title: str
    reason: str
    remaining_minutes: int
    priority_score: float
    concept_ids: tuple[str, ...]
    question_ids: tuple[str, ...]
    deadline_date: date | None
    available_from_date: date
    allow_split: bool


class StudyScheduleExecutionService:
    """Append-only task execution tracking and capacity-aware schedule replanning.

    Marking a study task complete does not manufacture question outcomes. Answer
    correctness and mastery continue to be owned by the completed-test feedback
    and learner-history services.
    """

    def __init__(
        self,
        repository: StudyTaskExecutionRepository,
        *,
        policy: StudySchedulePolicy | None = None,
    ) -> None:
        self.repository = repository
        self.policy = policy or StudySchedulePolicy()

    def record_execution(
        self, schedule: StudySchedule, event: StudyTaskExecution
    ) -> StudyTaskExecution:
        if event.learner_id != schedule.learner_id:
            raise ValueError("execution learner does not match schedule")
        if event.schedule_id != schedule.schedule_id:
            raise ValueError("execution schedule fingerprint does not match")
        task_map = {
            task.task_id: task for day in schedule.days for task in day.tasks
        }
        task = task_map.get(event.task_id)
        if task is None:
            raise ValueError("execution task does not belong to this schedule")
        if (
            event.postponed_until is not None
            and event.postponed_until < event.occurred_at.date()
        ):
            raise ValueError("postponed_until cannot precede the execution date")
        if not set(event.completed_question_ids).issubset(task.question_ids):
            raise ValueError("completed question IDs must belong to the scheduled task")
        if event.status is StudyTaskExecutionStatus.PARTIAL:
            assert event.remaining_minutes is not None
            if event.remaining_minutes > task.estimated_minutes:
                raise ValueError("remaining_minutes cannot exceed task estimate")
            remaining_questions = set(task.question_ids) - set(event.completed_question_ids)
            if task.question_ids and not remaining_questions:
                raise ValueError("fully completed question tasks must use COMPLETED status")
            if remaining_questions and event.remaining_minutes < len(remaining_questions):
                raise ValueError("remaining minutes must cover every unfinished question")

        existing = self.repository.get_event(event.event_id)
        if existing is not None:
            if existing != event:
                raise StudyTaskExecutionConflictError(
                    "event_id already exists with different execution data"
                )
            return existing

        history = self.repository.list_for_schedule(schedule.schedule_id, schedule.learner_id)
        self._validate_transition(event, history)
        self.repository.save_event(event)
        saved = self.repository.get_event(event.event_id)
        return event if saved is None else saved

    @staticmethod
    def _validate_transition(
        event: StudyTaskExecution,
        history: tuple[StudyTaskExecution, ...],
    ) -> None:
        prior = [item for item in history if item.task_id == event.task_id]
        if not prior:
            return
        latest = max(prior, key=lambda item: (item.occurred_at, item.event_id))
        if latest.status in {
            StudyTaskExecutionStatus.COMPLETED,
            StudyTaskExecutionStatus.SKIPPED,
            StudyTaskExecutionStatus.POSTPONED,
        }:
            raise ValueError("task already has a terminal execution status")
        if latest.status is StudyTaskExecutionStatus.PARTIAL:
            if event.status is StudyTaskExecutionStatus.PARTIAL:
                if not set(latest.completed_question_ids).issubset(event.completed_question_ids):
                    raise ValueError("partial execution cannot forget completed questions")
                if (
                    latest.remaining_minutes is not None
                    and event.remaining_minutes is not None
                    and event.remaining_minutes > latest.remaining_minutes
                ):
                    raise ValueError("remaining minutes cannot increase for a partial task")
            elif event.status is StudyTaskExecutionStatus.POSTPONED:
                raise ValueError("replan partial progress before postponing the remaining task")

    def replan(
        self,
        schedule: StudySchedule,
        *,
        daily_minutes: int,
        weekday_minutes: Mapping[int, int] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        first_day_minutes: int | None = None,
        as_of: datetime | None = None,
        exam_date: date | None = None,
        strategy_report: AdaptiveStudyStrategyReport | None = None,
    ) -> StudySchedule:
        self._validate_minutes("daily_minutes", daily_minutes)
        if first_day_minutes is not None:
            self._validate_minutes("first_day_minutes", first_day_minutes)
        now = as_of or datetime.now(timezone.utc)
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        start = start_date or now.date()
        exam = schedule.exam_date if exam_date is None else exam_date
        if exam is not None and exam < start:
            raise ValueError("exam_date cannot precede replanning start date")
        if strategy_report is not None:
            if strategy_report.learner_id != schedule.learner_id:
                raise ValueError("strategy report learner does not match schedule")
            if strategy_report.schedule_id != schedule.schedule_id:
                raise ValueError("strategy report schedule fingerprint does not match")
            if strategy_report.generated_at > now:
                raise ValueError("as_of cannot precede strategy report generation")

        events = self.repository.list_for_schedule(schedule.schedule_id, schedule.learner_id)
        tasks = {task.task_id: task for day in schedule.days for task in day.tasks}
        if any(
            row.schedule_id != schedule.schedule_id
            or row.learner_id != schedule.learner_id
            or row.task_id not in tasks
            for row in events
        ):
            raise ValueError("execution repository returned an event outside this schedule")
        latest: dict[str, StudyTaskExecution] = {}
        for row in events:
            old = latest.get(row.task_id)
            if old is None or (row.occurred_at, row.event_id) > (old.occurred_at, old.event_id):
                latest[row.task_id] = row

        work = self._unfinished_work(schedule, latest, start)
        if strategy_report is not None:
            self._apply_strategy_recommendations(work, schedule, strategy_report)
        postponed_dates = [item.available_from_date for item in work]
        requested_end = end_date if end_date is not None else max(
            [start, schedule.end_date, *postponed_dates]
        )
        if requested_end < start:
            raise ValueError("end_date cannot precede replanning start date")
        if (requested_end - start).days >= 366:
            raise ValueError("replanning window cannot exceed 366 calendar days")
        end = min(requested_end, exam) if exam is not None else requested_end

        overrides = dict(weekday_minutes or {})
        for weekday, minutes in overrides.items():
            if isinstance(weekday, bool) or not isinstance(weekday, int) or not 0 <= weekday <= 6:
                raise ValueError("weekday availability keys must be integers from 0 to 6")
            self._validate_minutes("weekday availability", minutes)

        exam_close = (
            exam is not None
            and 0 <= (exam - start).days <= self.policy.exam_urgency_window_days
        )
        if exam_close:
            for item in work:
                if item.kind is StudyTaskKind.PRACTICE_QUESTIONS:
                    item.priority_score = min(
                        1.0, item.priority_score + self.policy.exam_urgency_bonus
                    )
        work.sort(key=self._sort_key)

        day_specs: list[tuple[date, int]] = []
        current = start
        while current <= end:
            if current == exam:
                capacity = 0
            elif current == start and first_day_minutes is not None:
                capacity = first_day_minutes
            else:
                capacity = overrides.get(current.weekday(), daily_minutes)
            day_specs.append((current, capacity))
            current += timedelta(days=1)

        chunks: dict[date, list[tuple[_Work, int]]] = {day: [] for day, _ in day_specs}
        for day, capacity in day_specs:
            free = capacity
            while free > 0:
                eligible = next((
                    item for item in work
                    if item.remaining_minutes > 0
                    and item.available_from_date <= day
                    and (
                        item.remaining_minutes <= free
                        or (item.allow_split and free >= self.policy.minimum_block_minutes)
                    )
                ), None)
                if eligible is None:
                    break
                allocated = (
                    eligible.remaining_minutes if eligible.remaining_minutes <= free
                    else min(eligible.remaining_minutes, free, self.policy.maximum_block_minutes)
                )
                if allocated < 1:
                    break
                chunks[day].append((eligible, allocated))
                eligible.remaining_minutes -= allocated
                free -= allocated

        days = tuple(
            StudyDayPlan(
                study_date=day,
                available_minutes=capacity,
                tasks=self._materialize(day, chunks[day]),
            )
            for day, capacity in day_specs
        )
        unallocated = tuple(
            UnscheduledStudyWork(
                work_id=item.work_id,
                kind=item.kind,
                title=item.title,
                remaining_minutes=item.remaining_minutes,
                priority_score=item.priority_score,
                reason=item.reason,
                unscheduled_reason=(
                    f"Target date {item.available_from_date.isoformat()} is outside "
                    "the replanning window or remaining daily capacity is insufficient."
                ),
                concept_ids=item.concept_ids,
                question_ids=item.question_ids,
                deadline_date=item.deadline_date,
                available_from_date=item.available_from_date,
            )
            for item in work if item.remaining_minutes > 0
        )
        return StudySchedule(
            learner_id=schedule.learner_id,
            start_date=start,
            end_date=end,
            exam_date=exam,
            days=days,
            unscheduled_work=unallocated,
            generated_at=now,
        )

    @staticmethod
    def _apply_strategy_recommendations(
        work: list[_Work],
        schedule: StudySchedule,
        strategy_report: AdaptiveStudyStrategyReport,
    ) -> None:
        """Apply approved strategy advice to matching unfinished work only.

        Source schedules and append-only execution events remain unchanged. Multiple
        recommendations overlapping one work item use the highest proposed priority
        and earliest review date, a conservative deterministic merge.
        """
        tasks = {
            task.task_id: task
            for day in schedule.days
            for task in day.tasks
        }
        recommendations: list[
            tuple[set[str], set[str], StudyTaskStrategyAdjustment]
        ] = []
        for adjustment in strategy_report.adjustments:
            source_task = tasks.get(adjustment.task_id)
            if source_task is None:
                raise ValueError("strategy report references a task outside the schedule")
            if source_task.kind is not adjustment.task_kind:
                raise ValueError("strategy report task kind does not match schedule")
            if adjustment.action is StudyStrategyAction.COLLECT_MORE_EVIDENCE:
                continue
            recommendations.append((
                set(source_task.concept_ids),
                set(source_task.question_ids),
                adjustment,
            ))

        for item in work:
            matched = []
            item_concepts = set(item.concept_ids)
            item_questions = set(item.question_ids)
            for concepts, questions, adjustment in recommendations:
                if concepts.intersection(item_concepts) or questions.intersection(item_questions):
                    matched.append(adjustment)
            if not matched:
                continue

            # On conflicts, keep the strongest focus priority and earliest review date.
            item.priority_score = max(
                adjustment.recommended_priority_score for adjustment in matched
            )
            review_dates = [
                strategy_report.assessed_at.date()
                + timedelta(days=adjustment.suggested_revision_interval_days)
                for adjustment in matched
                if adjustment.suggested_revision_interval_days is not None
            ]
            if review_dates:
                target_date = min(review_dates)
                if item.deadline_date is not None:
                    target_date = min(target_date, item.deadline_date)
                item.available_from_date = max(item.available_from_date, target_date)
            action_names = ", ".join(sorted({adjustment.action.value for adjustment in matched}))
            item.reason = (
                f"{item.reason} Adaptive strategy applied ({action_names}); "
                "priority and next-review timing were derived from linked assessment evidence."
            )

    @staticmethod
    def _validate_minutes(name: str, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")

    def _unfinished_work(
        self,
        schedule: StudySchedule,
        latest: Mapping[str, StudyTaskExecution],
        start: date,
    ) -> list[_Work]:
        result: list[_Work] = []
        for day in schedule.days:
            for task in day.tasks:
                event = latest.get(task.task_id)
                if event and event.status in {
                    StudyTaskExecutionStatus.COMPLETED,
                    StudyTaskExecutionStatus.SKIPPED,
                }:
                    continue
                available = max(start, task.scheduled_date)
                minutes = task.estimated_minutes
                question_ids = task.question_ids
                if event:
                    if event.status is StudyTaskExecutionStatus.POSTPONED:
                        assert event.postponed_until is not None
                        available = max(start, event.postponed_until)
                    elif event.status is StudyTaskExecutionStatus.PARTIAL:
                        assert event.remaining_minutes is not None
                        minutes = event.remaining_minutes
                        completed = set(event.completed_question_ids)
                        question_ids = tuple(q for q in task.question_ids if q not in completed)
                if question_ids:
                    self._append_question_units(
                        result, base_id=task.task_id, kind=task.kind,
                        title=task.title, reason=task.reason, total_minutes=minutes,
                        priority=task.priority_score, concept_ids=task.concept_ids,
                        original_question_count=len(task.question_ids),
                        question_ids=question_ids, deadline=task.deadline_date,
                        available=available,
                    )
                elif task.concept_ids:
                    result.append(_Work(
                        work_id=task.task_id, kind=task.kind, title=task.title,
                        reason=task.reason, remaining_minutes=minutes,
                        priority_score=task.priority_score, concept_ids=task.concept_ids,
                        question_ids=(), deadline_date=task.deadline_date,
                        available_from_date=available,
                        allow_split=task.kind is StudyTaskKind.STUDY_WEAK_TOPIC,
                    ))

        for item in schedule.unscheduled_work:
            available = max(start, item.available_from_date or start)
            if item.question_ids:
                self._append_question_units(
                    result, base_id=item.work_id, kind=item.kind,
                    title=item.title, reason=item.reason,
                    total_minutes=item.remaining_minutes, priority=item.priority_score,
                    concept_ids=item.concept_ids, original_question_count=len(item.question_ids),
                    question_ids=item.question_ids, deadline=item.deadline_date,
                    available=available,
                )
            elif item.concept_ids:
                result.append(_Work(
                    work_id=item.work_id, kind=item.kind, title=item.title,
                    reason=item.reason, remaining_minutes=item.remaining_minutes,
                    priority_score=item.priority_score, concept_ids=item.concept_ids,
                    question_ids=(), deadline_date=item.deadline_date,
                    available_from_date=available,
                    allow_split=item.kind is StudyTaskKind.STUDY_WEAK_TOPIC,
                ))
        return result

    @staticmethod
    def _append_question_units(
        target: list[_Work], *, base_id: str, kind: StudyTaskKind,
        title: str, reason: str, total_minutes: int, priority: float,
        concept_ids: tuple[str, ...], original_question_count: int,
        question_ids: tuple[str, ...], deadline: date | None, available: date,
    ) -> None:
        if not question_ids:
            return
        if total_minutes < len(question_ids):
            raise ValueError("remaining minutes must cover every unfinished question")
        base, remainder = divmod(total_minutes, len(question_ids))
        for index, question_id in enumerate(question_ids):
            # An aggregated task doesn't retain a precise concept-to-question map.
            concepts = concept_ids if original_question_count == 1 else ()
            target.append(_Work(
                work_id=f"{base_id}:question:{question_id}",
                kind=kind, title=title, reason=reason,
                remaining_minutes=base + (1 if index < remainder else 0),
                priority_score=priority, concept_ids=concepts,
                question_ids=(question_id,), deadline_date=deadline,
                available_from_date=available, allow_split=False,
            ))

    @staticmethod
    def _sort_key(item: _Work) -> tuple[object, ...]:
        kind_order = {
            StudyTaskKind.REVIEW_DUE_REVISION: 0,
            StudyTaskKind.REVIEW_PREVIOUS_MISTAKES: 1,
            StudyTaskKind.STUDY_WEAK_TOPIC: 2,
            StudyTaskKind.PRACTICE_QUESTIONS: 3,
        }
        return (
            kind_order[item.kind], -item.priority_score,
            item.deadline_date or date.max, item.available_from_date, item.work_id,
        )

    def _materialize(
        self, day: date, chunks: list[tuple[_Work, int]]
    ) -> tuple[ScheduledStudyTask, ...]:
        chunks.sort(key=lambda item: (-item[0].priority_score, item[0].kind.value, item[0].work_id))
        groups: list[list[tuple[_Work, int]]] = []
        for chunk in chunks:
            if (
                groups and groups[-1][0][0].kind is chunk[0].kind
                and sum(minutes for _, minutes in groups[-1]) + chunk[1] <= self.policy.maximum_block_minutes
            ):
                groups[-1].append(chunk)
            else:
                groups.append([chunk])
        tasks: list[ScheduledStudyTask] = []
        for index, group in enumerate(groups, start=1):
            first = group[0][0]
            concepts = tuple(dict.fromkeys(
                concept for item, _ in group for concept in item.concept_ids
            ))
            questions = tuple(dict.fromkeys(
                question for item, _ in group for question in item.question_ids
            ))
            deadlines = [item.deadline_date for item, _ in group if item.deadline_date is not None]
            tasks.append(ScheduledStudyTask(
                task_id=f"{day.isoformat()}-{index:02d}-{first.kind.value.lower()}",
                kind=first.kind, scheduled_date=day, title=first.title,
                estimated_minutes=sum(minutes for _, minutes in group),
                priority_score=max(item.priority_score for item, _ in group),
                reason=first.reason, concept_ids=concepts, question_ids=questions,
                deadline_date=min(deadlines) if deadlines else None,
            ))
        return tuple(tasks)


__all__ = ["StudyScheduleExecutionService"]
