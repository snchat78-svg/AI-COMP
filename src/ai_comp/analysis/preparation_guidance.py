from __future__ import annotations

from datetime import datetime, timezone
from collections.abc import Sequence

from ai_comp.analysis.adaptive_difficulty import AdaptiveDifficultyService
from ai_comp.analysis.adaptive_study_strategy_feedback import AdaptiveStudyStrategyFeedbackService
from ai_comp.analysis.learning_progress import LearningProgressService
from ai_comp.analysis.personalized_preparation import PersonalizedPreparationService
from ai_comp.domain.learning_history import (
    LearnerLearningHistory,
    LearningTrend,
)
from ai_comp.domain.adaptive_study_strategy_feedback import AdaptiveStudyStrategyFeedbackReport
from ai_comp.domain.adaptive_study_strategy_history import AdaptiveStudyStrategyHistoryReport
from ai_comp.domain.learning_progress import LearnerProgressReport
from ai_comp.domain.material_generation import GeneratedMCQ
from ai_comp.domain.personalized_preparation import (
    PersonalizedPreparationMode,
    PersonalizedPreparationPlan,
)
from ai_comp.domain.preparation_guidance import (
    PreparationActionKind,
    PreparationGuidance,
    PreparationGuidanceAction,
)
from ai_comp.domain.question_intelligence import RankedQuestionCandidate
from ai_comp.domain.question_learning import LearnerQuestionHistory
from ai_comp.domain.test_analysis import TestAnalysis
from ai_comp.domain.test_engine import ScoringPolicy


class PreparationGuidanceService:
    """Connects progress signals with the existing personalized test plan.

    It adds no second selection engine or mutable learner state: test composition
    remains owned by PersonalizedPreparationService and trend calculation remains
    owned by LearningProgressService.
    """

    def __init__(
        self,
        *,
        preparation_service: PersonalizedPreparationService | None = None,
        progress_service: LearningProgressService | None = None,
        adaptive_difficulty_service: AdaptiveDifficultyService | None = None,
        strategy_feedback_service: AdaptiveStudyStrategyFeedbackService | None = None,
    ) -> None:
        self.preparation_service = (
            preparation_service or PersonalizedPreparationService()
        )
        self.progress_service = progress_service or LearningProgressService()
        self.adaptive_difficulty_service = (
            adaptive_difficulty_service
            or self.preparation_service.adaptive_difficulty_service
        )
        self.strategy_feedback_service = (
            strategy_feedback_service or AdaptiveStudyStrategyFeedbackService()
        )

    def build_guidance(
        self,
        learner_id: str,
        *,
        test_id: str,
        title: str,
        question_count: int,
        duration_seconds: int,
        history: LearnerLearningHistory,
        question_history: LearnerQuestionHistory,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        current_analysis: TestAnalysis | None = None,
        mode: PersonalizedPreparationMode = PersonalizedPreparationMode.ADAPTIVE,
        scoring: ScoringPolicy | None = None,
        shuffle_questions: bool = False,
        shuffle_seed: int | None = None,
        exclude_question_ids: Sequence[str] = (),
        as_of: datetime | None = None,
        strategy_history_report: AdaptiveStudyStrategyHistoryReport | None = None,
        generated_at: datetime | None = None,
    ) -> PreparationGuidance:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if history.learner_id != learner_id:
            raise ValueError("learning history learner does not match")
        if question_history.learner_id != learner_id:
            raise ValueError("question history learner does not match")

        report_time = generated_at or datetime.now(timezone.utc)
        # Build through the canonical phase 6.11 selection path. This preserves
        # accepted-question checks, old-mistake ordering and current-test exclusions.
        plan = self.preparation_service.build_plan(
            learner_id,
            test_id=test_id,
            title=title,
            question_count=question_count,
            duration_seconds=duration_seconds,
            history=history,
            question_history=question_history,
            candidates=candidates,
            questions=questions,
            current_analysis=current_analysis,
            mode=mode,
            scoring=scoring,
            shuffle_questions=shuffle_questions,
            shuffle_seed=shuffle_seed,
            exclude_question_ids=exclude_question_ids,
            as_of=as_of,
        )

        adaptive_profile = self.adaptive_difficulty_service.analyze(
            learner_id,
            history,
            question_history,
            as_of=as_of,
        )
        progress = self.progress_service.analyze(
            learner_id,
            history,
            question_history,
            adaptive_profile=adaptive_profile,
            generated_at=report_time,
        )
        strategy_feedback = None
        if strategy_history_report is not None:
            if strategy_history_report.learner_id != learner_id:
                raise ValueError("strategy history learner does not match")
            strategy_feedback = self.strategy_feedback_service.build_report(
                strategy_history_report,
                generated_at=report_time,
            )

        actions = self._actions(
            progress,
            plan,
            history,
            question_history,
            strategy_feedback_report=strategy_feedback,
        )

        return PreparationGuidance(
            learner_id=learner_id,
            progress_report=progress,
            preparation_plan=plan,
            actions=actions,
            generated_at=report_time,
            strategy_feedback_report=strategy_feedback,
        )

    @staticmethod
    def _actions(
        progress: LearnerProgressReport,
        plan: PersonalizedPreparationPlan,
        history: LearnerLearningHistory,
        question_history: LearnerQuestionHistory,
        *,
        strategy_feedback_report: AdaptiveStudyStrategyFeedbackReport | None = None,
    ) -> tuple[PreparationGuidanceAction, ...]:
        actions: list[PreparationGuidanceAction] = []
        revision_ids = plan.revision_question_ids
        revision_by_id = {
            item.question_id: item
            for item in question_history.revision_candidates
        }
        if revision_ids:
            revision_items = [
                revision_by_id[question_id]
                for question_id in revision_ids
                if question_id in revision_by_id
            ]
            priority = max(
                (item.priority_score for item in revision_items),
                default=0.65,
            )
            reasons = tuple(dict.fromkeys(
                item.reason for item in sorted(
                    revision_items,
                    key=lambda item: (-item.priority_score, item.question_id),
                )
            ))
            detail = "; ".join(reasons[:2])
            actions.append(PreparationGuidanceAction(
                kind=PreparationActionKind.REVIEW_PREVIOUS_MISTAKES,
                title="Review previous mistakes",
                reason=(
                    f"These {len(revision_ids)} prior-mistake question(s) were "
                    "selected for revision"
                    + (f": {detail}" if detail else ".")
                ),
                priority_score=priority,
                concept_ids=tuple(dict.fromkeys(
                    concept
                    for item in revision_items
                    for concept in item.concept_ids
                )),
                question_ids=revision_ids,
            ))

        focus_ids = plan.focus_concept_ids
        if focus_ids:
            topic_priority = {
                item.concept_id: item.priority_score
                for item in history.topic_performance
            }
            recommendation_priority = {
                item.concept_id: item.priority_score
                for item in plan.recommendations
            }
            scores = [
                topic_priority.get(
                    concept_id,
                    recommendation_priority.get(concept_id, 0.5),
                )
                for concept_id in focus_ids
            ]
            why = tuple(
                item.reason for item in plan.recommendations
                if item.concept_id in focus_ids
            )
            actions.append(PreparationGuidanceAction(
                kind=PreparationActionKind.PRACTICE_WEAK_TOPICS,
                title="Practice priority topics",
                reason=(
                    "The next test focuses on: " + ", ".join(focus_ids)
                    + (f". Evidence: {'; '.join(dict.fromkeys(why))}" if why else ".")
                ),
                priority_score=max(scores, default=0.5),
                concept_ids=focus_ids,
            ))

        retention_ids = plan.retention_due_question_ids
        if retention_ids:
            performance_priority = {
                item.question_id: item.priority_score
                for item in question_history.question_performance
            }
            actions.append(PreparationGuidanceAction(
                kind=PreparationActionKind.REVIEW_RETENTION_ITEMS,
                title="Review due retention questions",
                reason=(
                    "Spaced-revision history marks these selected questions as due; "
                    "review them to reinforce recall."
                ),
                priority_score=max(
                    (performance_priority.get(question_id, 0.5)
                     for question_id in retention_ids),
                    default=0.5,
                ),
                question_ids=retention_ids,
            ))

        if progress.trend is LearningTrend.DECLINING:
            delta = progress.delta_percentage_points
            declining_concepts = tuple(
                item.concept_id for item in progress.topics
                if item.trend is LearningTrend.DECLINING
            )
            actions.append(PreparationGuidanceAction(
                kind=PreparationActionKind.RESPOND_TO_DECLINING_TREND,
                title="Reinforce before increasing difficulty",
                reason=(
                    f"Recent test average changed by {delta:.2f} percentage points "
                    "versus the preceding window. Review incorrect answers and "
                    "compare tests of similar difficulty; do not treat this trend "
                    "alone as proof of lost mastery."
                ),
                priority_score=0.82,
                concept_ids=declining_concepts or focus_ids,
                question_ids=revision_ids,
            ))
        elif progress.trend is LearningTrend.INSUFFICIENT_DATA:
            actions.append(PreparationGuidanceAction(
                kind=PreparationActionKind.COLLECT_MORE_PROGRESS_DATA,
                title="Complete more tests to measure progress",
                reason=(
                    f"Only {progress.completed_test_count} completed test(s) are "
                    "available, so a before-versus-recent trend cannot yet be "
                    "estimated reliably."
                ),
                priority_score=0.35,
            ))
        else:
            direction = (
                "improved" if progress.trend is LearningTrend.IMPROVING
                else "remained broadly stable"
            )
            delta = progress.delta_percentage_points
            actions.append(PreparationGuidanceAction(
                kind=PreparationActionKind.MAINTAIN_STUDY_ROUTINE,
                title="Maintain the study routine",
                reason=(
                    f"Recent test average {direction} by {abs(delta):.2f} "
                    "percentage points versus the preceding window. Continue "
                    "targeted practice and compare similarly composed tests."
                ),
                priority_score=0.58 if progress.trend is LearningTrend.IMPROVING else 0.50,
            ))

        if strategy_feedback_report is not None and strategy_feedback_report.findings:
            findings = strategy_feedback_report.findings
            concept_ids = tuple(sorted({
                item for finding in findings
                if finding.scope_kind.value == "CONCEPTS"
                for item in finding.scope_ids
            }))
            question_ids = tuple(sorted({
                item for finding in findings
                if finding.scope_kind.value == "QUESTIONS"
                for item in finding.scope_ids
            }))
            reason_parts = tuple(dict.fromkeys(finding.reason for finding in findings[:2]))
            actions.append(PreparationGuidanceAction(
                kind=PreparationActionKind.REVISIT_STUDY_APPROACH,
                title="Try a different study approach for recurring declines",
                reason=(
                    "Historical strategy evidence meets the repeated-decline threshold. "
                    + " ".join(reason_parts)
                    + " Keep the next comparison as similar as practical."
                ),
                priority_score=max(finding.priority_score for finding in findings),
                concept_ids=concept_ids,
                question_ids=question_ids,
            ))

        if not actions:
            actions.append(PreparationGuidanceAction(
                kind=PreparationActionKind.COLLECT_MORE_PROGRESS_DATA,
                title="Continue practice and collect progress",
                reason="No targeted revision or weak-topic signal is available yet.",
                priority_score=0.35,
            ))

        actions.sort(key=lambda item: (-item.priority_score, item.kind.value))
        return tuple(actions)


__all__ = ["PreparationGuidanceService"]
