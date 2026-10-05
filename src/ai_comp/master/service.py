from collections.abc import Iterable

from ai_comp.domain.master_questions import (
    MasterAssignmentPolicy,
    MasterAssignmentResult,
    MasterAssignmentStatus,
    MasterMembershipType,
    MasterQuestion,
    MasterQuestionMembership,
)
from ai_comp.domain.matching import MatchType, QuestionMatch
from ai_comp.domain.questions import QuestionCandidate
from ai_comp.master.repository import MasterQuestionRepository


class MasterQuestionService:
    """Creates and assigns canonical master-question identities safely."""

    def __init__(
        self,
        repository: MasterQuestionRepository,
        policy: MasterAssignmentPolicy | None = None,
    ) -> None:
        self.repository = repository
        self.policy = policy or MasterAssignmentPolicy()

    def assign(
        self,
        question: QuestionCandidate,
        matches: Iterable[QuestionMatch] = (),
    ) -> MasterAssignmentResult:
        existing = self.repository.get_membership_for_question(
            question.question_id
        )
        if existing is not None:
            return MasterAssignmentResult(
                question_id=question.question_id,
                status=MasterAssignmentStatus.ALREADY_ASSIGNED,
                master_question_id=existing.master_question_id,
                relationship=existing.relationship,
                reason="question already has a master assignment",
            )

        candidates = self._master_candidates(question.question_id, matches)
        eligible = [
            item
            for item in candidates
            if self._eligible(item[0])
        ]

        selected = self._select(eligible)
        if selected is None:
            if self._has_competing_candidates(eligible):
                competing = tuple(
                    sorted({master_id for master_id, _, _ in eligible})
                )
                return MasterAssignmentResult(
                    question_id=question.question_id,
                    status=MasterAssignmentStatus.AMBIGUOUS,
                    competing_master_ids=competing,
                    reason="multiple competing masters have no safe winner",
                )
            return self._create_master(question)

        master_id, relationship, confidence = selected
        membership = MasterQuestionMembership(
            master_question_id=master_id,
            question_id=question.question_id,
            relationship=relationship,
            confidence=confidence,
        )
        self.repository.save_membership(membership)

        return MasterAssignmentResult(
            question_id=question.question_id,
            status=MasterAssignmentStatus.ASSIGNED,
            master_question_id=master_id,
            relationship=relationship,
            reason="assigned using an eligible historical-equivalent match",
        )

    def _master_candidates(
        self,
        question_id: str,
        matches: Iterable[QuestionMatch],
    ) -> list[tuple[str, MasterMembershipType, float]]:
        result: list[tuple[str, MasterMembershipType, float]] = []
        for match in matches:
            if match.left_question_id == question_id:
                other_id = match.right_question_id
            elif match.right_question_id == question_id:
                other_id = match.left_question_id
            else:
                continue

            if match.match_type not in {
                MatchType.EXACT,
                MatchType.REPHRASED,
            }:
                continue

            master = self.repository.get_master_for_question(other_id)
            if master is None:
                continue

            if match.match_type is MatchType.EXACT:
                relationship = MasterMembershipType.EXACT
            else:
                relationship = MasterMembershipType.REPHRASED

            result.append((master.master_question_id, relationship, match.confidence))
        return result

    def _eligible(
        self,
        relationship: MasterMembershipType,
    ) -> bool:
        return relationship is MasterMembershipType.EXACT or (
            relationship is MasterMembershipType.REPHRASED
            and self.policy.min_rephrased_confidence <= 1.0
        )

    def _select(
        self,
        candidates: list[tuple[str, MasterMembershipType, float]],
    ) -> tuple[str, MasterMembershipType, float] | None:
        if not candidates:
            return None

        grouped: dict[str, tuple[MasterMembershipType, float]] = {}
        rank = {
            MasterMembershipType.EXACT: 2,
            MasterMembershipType.REPHRASED: 1,
        }
        for master_id, relationship, confidence in candidates:
            current = grouped.get(master_id)
            if current is None or (
                rank[relationship],
                confidence,
            ) > (
                rank[current[0]],
                current[1],
            ):
                grouped[master_id] = (relationship, confidence)

        ranked = sorted(
            (
                (master_id, relationship, confidence)
                for master_id, (relationship, confidence) in grouped.items()
            ),
            key=lambda item: (rank[item[1]], item[2], item[0]),
            reverse=True,
        )

        if len(ranked) == 1:
            return ranked[0]

        first = ranked[0]
        second = ranked[1]

        if first[1] is MasterMembershipType.EXACT:
            if second[1] is MasterMembershipType.EXACT:
                return None
            return first

        if first[2] < self.policy.min_rephrased_confidence:
            return None
        if first[2] - second[2] < self.policy.min_confidence_margin:
            return None
        return first

    @staticmethod
    def _has_competing_candidates(
        candidates: list[tuple[str, MasterMembershipType, float]],
    ) -> bool:
        return len({master_id for master_id, _, _ in candidates}) > 1

    def _create_master(
        self,
        question: QuestionCandidate,
    ) -> MasterAssignmentResult:
        master = MasterQuestion(
            master_question_id=f"master:{question.question_id}",
            canonical_question_id=question.question_id,
            stem=question.stem,
            options=question.options,
            kind=question.kind,
        )
        self.repository.save_master(master)
        self.repository.save_membership(
            MasterQuestionMembership(
                master_question_id=master.master_question_id,
                question_id=question.question_id,
                relationship=MasterMembershipType.CANONICAL,
                confidence=1.0,
            )
        )
        return MasterAssignmentResult(
            question_id=question.question_id,
            status=MasterAssignmentStatus.CREATED,
            master_question_id=master.master_question_id,
            relationship=MasterMembershipType.CANONICAL,
            reason="no eligible historical-equivalent master existed",
        )
