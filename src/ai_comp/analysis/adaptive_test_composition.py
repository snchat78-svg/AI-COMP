from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from datetime import datetime

from ai_comp.analysis.adaptive_difficulty import AdaptiveDifficultyService
from ai_comp.domain.adaptive_difficulty import AdaptiveAction, AdaptiveDifficultyProfile
from ai_comp.domain.adaptive_test_composition import (
    AdaptiveTestCompositionPlan,
    AdaptiveTestCompositionPolicy,
    ConceptCoverage,
)
from ai_comp.domain.learning_history import LearnerLearningHistory
from ai_comp.domain.material_generation import GeneratedMCQ, GeneratedQuestionStatus
from ai_comp.domain.question_intelligence import RankedQuestionCandidate
from ai_comp.domain.question_learning import LearnerQuestionHistory


class AdaptiveTestCompositionService:
    """Composes a deterministic adaptive test above existing ranking/history layers."""

    def __init__(
        self,
        policy: AdaptiveTestCompositionPolicy | None = None,
        adaptive_difficulty_service: AdaptiveDifficultyService | None = None,
    ) -> None:
        self.policy = policy or AdaptiveTestCompositionPolicy()
        self.adaptive_difficulty_service = (
            adaptive_difficulty_service or AdaptiveDifficultyService()
        )

    def compose(
        self,
        learner_id: str,
        *,
        question_count: int,
        learning_history: LearnerLearningHistory,
        question_history: LearnerQuestionHistory,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        exclude_question_ids: Sequence[str] = (),
        as_of: datetime | None = None,
    ) -> AdaptiveTestCompositionPlan:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        if learning_history.learner_id != learner_id:
            raise ValueError("learning history learner does not match")
        if question_history.learner_id != learner_id:
            raise ValueError("question history learner does not match")
        if question_count < 1:
            raise ValueError("question_count must be positive")

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
        candidate_by_id = {
            question_id: candidate
            for question_id, candidate in candidate_by_id.items()
            if question_id not in excluded
        }
        if len(candidate_by_id) < question_count:
            raise ValueError("not enough accepted ranked questions for composition")

        profile = self.adaptive_difficulty_service.analyze(
            learner_id,
            learning_history,
            question_history,
            as_of=as_of,
        )
        decisions = {
            decision.concept_id: decision
            for decision in profile.decisions
        }
        revision_ids = {
            item.question_id
            for item in question_history.revision_candidates
            if item.question_id in candidate_by_id
        }
        due_ids = set(profile.retention_due_question_ids).intersection(candidate_by_id)

        selected: list[RankedQuestionCandidate] = []
        selected_ids: set[str] = set()

        due_slots = min(
            question_count,
            self._ceil_ratio(question_count, self.policy.retention_ratio),
        )
        self._select_stage(
            selected,
            selected_ids,
            [
                candidate
                for candidate in candidate_by_id.values()
                if candidate.question_id in due_ids
            ],
            accepted,
            decisions,
            due_slots,
            question_count,
        )

        revision_slots = min(
            question_count - len(selected),
            self._ceil_ratio(question_count, self.policy.revision_ratio),
        )
        self._select_stage(
            selected,
            selected_ids,
            [
                candidate
                for candidate in candidate_by_id.values()
                if candidate.question_id in revision_ids
                and candidate.question_id not in selected_ids
            ],
            accepted,
            decisions,
            revision_slots,
            question_count,
        )

        remaining = question_count - len(selected)
        remediation_concepts = tuple(
            concept_id
            for concept_id, decision in sorted(
                decisions.items(),
                key=lambda item: (-item[1].priority_score, item[0]),
            )
            if decision.action is AdaptiveAction.REMEDIATE
        )
        remediation_slots = min(
            remaining,
            self._ceil_ratio(remaining, self.policy.remediation_ratio),
        )
        self._select_stage(
            selected,
            selected_ids,
            [
                candidate
                for candidate in candidate_by_id.values()
                if candidate.question_id not in selected_ids
                and self._matches_concepts(
                    accepted[candidate.question_id],
                    remediation_concepts,
                )
            ],
            accepted,
            decisions,
            remediation_slots,
            question_count,
        )

        remaining = question_count - len(selected)
        advancement_concepts = tuple(
            concept_id
            for concept_id, decision in sorted(
                decisions.items(),
                key=lambda item: (-item[1].priority_score, item[0]),
            )
            if decision.action is AdaptiveAction.ADVANCE
        )
        self._select_stage(
            selected,
            selected_ids,
            [
                candidate
                for candidate in candidate_by_id.values()
                if candidate.question_id not in selected_ids
                and self._matches_concepts(
                    accepted[candidate.question_id],
                    advancement_concepts,
                )
            ],
            accepted,
            decisions,
            remaining,
            question_count,
        )

        remaining = question_count - len(selected)
        self._select_stage(
            selected,
            selected_ids,
            [
                candidate
                for candidate in candidate_by_id.values()
                if candidate.question_id not in selected_ids
            ],
            accepted,
            decisions,
            remaining,
            question_count,
        )

        if len(selected) < question_count:
            raise ValueError("not enough questions after adaptive composition")

        ordered = tuple(
            candidate.__class__(
                question_id=candidate.question_id,
                score=candidate.score,
                rank=index,
            )
            for index, candidate in enumerate(selected[:question_count], start=1)
        )
        ordered_ids = {candidate.question_id for candidate in ordered}

        retention_selected = tuple(
            candidate.question_id
            for candidate in ordered
            if candidate.question_id in due_ids
        )
        revision_selected = tuple(
            candidate.question_id
            for candidate in ordered
            if candidate.question_id in revision_ids
        )
        remediation_selected = tuple(
            candidate.question_id
            for candidate in ordered
            if self._candidate_matches_action(
                accepted[candidate.question_id],
                decisions,
                AdaptiveAction.REMEDIATE,
            )
        )
        advancement_selected = tuple(
            candidate.question_id
            for candidate in ordered
            if self._candidate_matches_action(
                accepted[candidate.question_id],
                decisions,
                AdaptiveAction.ADVANCE,
            )
        )

        available_by_concept = Counter()
        selected_by_concept = Counter()
        for candidate in candidate_by_id.values():
            for concept_id in accepted[candidate.question_id].concept_ids:
                available_by_concept[concept_id] += 1
        for candidate in ordered:
            for concept_id in accepted[candidate.question_id].concept_ids:
                selected_by_concept[concept_id] += 1

        coverage = tuple(
            ConceptCoverage(
                concept_id=concept_id,
                selected_count=selected_by_concept[concept_id],
                available_count=available_by_concept[concept_id],
                action=(
                    decisions[concept_id].action.value
                    if concept_id in decisions
                    else "GENERAL"
                ),
            )
            for concept_id in sorted(available_by_concept)
            if selected_by_concept[concept_id] > 0
        )

        focus_concepts = tuple(
            concept_id
            for concept_id, count in sorted(
                selected_by_concept.items(),
                key=lambda item: (-item[1], item[0]),
            )
            if concept_id in decisions
        )

        return AdaptiveTestCompositionPlan(
            question_ids=tuple(candidate.question_id for candidate in ordered),
            ranked_candidates=ordered,
            retention_question_ids=retention_selected,
            revision_question_ids=revision_selected,
            remediation_question_ids=remediation_selected,
            advancement_question_ids=advancement_selected,
            focus_concept_ids=focus_concepts,
            coverage=coverage,
            recommended_difficulty=profile.recommended_difficulty,
            reason=self._reason(
                profile,
                retention_selected,
                revision_selected,
                remediation_selected,
                advancement_selected,
            ),
            decisions=profile.decisions,
        )

    def _select_stage(
        self,
        selected: list[RankedQuestionCandidate],
        selected_ids: set[str],
        candidates: Sequence[RankedQuestionCandidate],
        accepted: dict[str, GeneratedMCQ],
        decisions: dict,
        target_count: int,
        final_question_count: int,
    ) -> None:
        if target_count <= 0 or not candidates:
            return

        stage_target_total = len(selected) + target_count
        cap = max(
            1,
            self._ceil_ratio(
                final_question_count,
                self.policy.max_concept_ratio,
            ),
        )
        pool = [
            candidate
            for candidate in candidates
            if candidate.question_id not in selected_ids
        ]

        while len(selected) < stage_target_total and pool:
            concept_counts = Counter()
            for current in selected:
                for concept_id in accepted[current.question_id].concept_ids:
                    concept_counts[concept_id] += 1

            capped = [
                candidate
                for candidate in pool
                if not self._all_concepts_at_cap(
                    accepted[candidate.question_id],
                    concept_counts,
                    cap,
                )
            ]
            eligible = capped or pool

            chosen = min(
                eligible,
                key=lambda candidate: self._candidate_key(
                    candidate,
                    accepted[candidate.question_id],
                    decisions,
                    concept_counts,
                ),
            )
            selected.append(chosen)
            selected_ids.add(chosen.question_id)
            pool = [
                candidate
                for candidate in pool
                if candidate.question_id != chosen.question_id
            ]

    @staticmethod
    def _candidate_key(candidate, question, decisions, concept_counts):
        concepts = tuple(
            concept_id
            for concept_id in question.concept_ids
            if concept_id in decisions
        )
        target_difficulties = [
            decisions[concept_id].recommended_difficulty
            for concept_id in concepts
        ]
        difficulty_match = (
            0 if candidate.score.difficulty in target_difficulties else 1
        )
        usage = min(
            (concept_counts[concept_id] for concept_id in concepts),
            default=0,
        )
        priority = max(
            (decisions[concept_id].priority_score for concept_id in concepts),
            default=0.0,
        )
        return (
            difficulty_match,
            usage,
            -priority,
            -candidate.score.selection_score,
            -candidate.score.importance_score,
            -candidate.score.novelty_score,
            candidate.rank,
            candidate.question_id,
        )

    @staticmethod
    def _all_concepts_at_cap(question, concept_counts, cap):
        concepts = question.concept_ids
        if not concepts:
            return False
        return all(concept_counts[concept_id] >= cap for concept_id in concepts)

    @staticmethod
    def _matches_concepts(question, concepts):
        return any(concept_id in concepts for concept_id in question.concept_ids)

    @staticmethod
    def _candidate_matches_action(question, decisions, action):
        return any(
            decisions[concept_id].action is action
            for concept_id in question.concept_ids
            if concept_id in decisions
        )

    @staticmethod
    def _ceil_ratio(value: int, ratio: float) -> int:
        return int(value * ratio + 0.999999)

    @staticmethod
    def _reason(
        profile: AdaptiveDifficultyProfile,
        retention_ids,
        revision_ids,
        remediation_ids,
        advancement_ids,
    ) -> str:
        parts = [f"adaptive difficulty {profile.recommended_difficulty.value.lower()}"]
        if retention_ids:
            parts.append("retention due prioritized")
        if revision_ids:
            parts.append("previous mistakes prioritized")
        if remediation_ids:
            parts.append("weak concepts prioritized")
        if advancement_ids:
            parts.append("mastered concepts advanced")
        return "; ".join(parts) + " (adaptive composition)"


__all__ = ["AdaptiveTestCompositionService"]
