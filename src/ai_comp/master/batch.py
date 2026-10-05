from collections.abc import Iterable

from ai_comp.domain.master_questions import (
    MasterAssignmentResult,
    MasterAssignmentStatus,
    MasterMembershipType,
    MasterQuestion,
)
from ai_comp.domain.matching import MatchType, QuestionMatch
from ai_comp.domain.questions import QuestionCandidate
from ai_comp.master.repository import MasterQuestionRepository
from ai_comp.master.service import MasterQuestionService


class MasterQuestionBatchService:
    """Assigns a full extracted question set deterministically."""

    def __init__(
        self,
        repository: MasterQuestionRepository,
        service: MasterQuestionService | None = None,
    ) -> None:
        self.repository = repository
        self.service = service or MasterQuestionService(repository)

    def assign_many(
        self,
        questions: Iterable[QuestionCandidate],
        matches: Iterable[QuestionMatch] = (),
    ) -> tuple[MasterAssignmentResult, ...]:
        questions_by_id = self._validate_questions(questions)
        match_items = tuple(matches)

        results: dict[str, MasterAssignmentResult] = {}
        components = self._exact_components(
            tuple(questions_by_id),
            match_items,
        )

        for component in components:
            self._assign_component(
                component,
                questions_by_id,
                match_items,
                results,
            )

        return tuple(results[question_id] for question_id in questions_by_id)

    @staticmethod
    def _validate_questions(
        questions: Iterable[QuestionCandidate],
    ) -> dict[str, QuestionCandidate]:
        result: dict[str, QuestionCandidate] = {}
        for question in sorted(
            tuple(questions),
            key=lambda item: (
                item.document_id,
                item.question_number,
                item.question_id,
            ),
        ):
            if question.question_id in result:
                raise ValueError(
                    f"duplicate question_id in batch: {question.question_id}"
                )
            result[question.question_id] = question
        return result

    @staticmethod
    def _exact_components(
        question_ids: tuple[str, ...],
        matches: tuple[QuestionMatch, ...],
    ) -> tuple[tuple[str, ...], ...]:
        parent = {question_id: question_id for question_id in question_ids}
        batch_ids = set(question_ids)

        def find(question_id: str) -> str:
            current = question_id
            while parent[current] != current:
                parent[current] = parent[parent[current]]
                current = parent[current]
            return current

        def union(left: str, right: str) -> None:
            left_root = find(left)
            right_root = find(right)
            if left_root != right_root:
                parent[right_root] = left_root

        for match in matches:
            if match.match_type is not MatchType.EXACT:
                continue
            if (
                match.left_question_id in batch_ids
                and match.right_question_id in batch_ids
            ):
                union(match.left_question_id, match.right_question_id)

        components: dict[str, list[str]] = {}
        for question_id in question_ids:
            components.setdefault(find(question_id), []).append(question_id)

        return tuple(
            tuple(
                sorted(
                    members,
                    key=lambda question_id: (
                        question_ids.index(question_id)
                    ),
                )
            )
            for members in sorted(components.values(), key=lambda items: items[0])
        )

    def _assign_component(
        self,
        component: tuple[str, ...],
        questions_by_id: dict[str, QuestionCandidate],
        matches: tuple[QuestionMatch, ...],
        results: dict[str, MasterAssignmentResult],
    ) -> None:
        active_members = [
            question_id
            for question_id in component
            if question_id not in results
        ]
        if not active_members:
            return

        existing_masters = {
            master.master_question_id
            for question_id in component
            if (
                (master := self.repository.get_master_for_question(question_id))
                is not None
                and self._is_active(master)
            )
        }

        if len(existing_masters) > 1:
            self._mark_ambiguous(
                active_members,
                results,
                tuple(sorted(existing_masters)),
                "exact component is already split across multiple masters",
            )
            for question_id in component:
                if question_id not in results:
                    results[question_id] = self._already_assigned(
                        question_id,
                        existing_masters,
                    )
            return

        if len(existing_masters) == 1:
            master_id = next(iter(existing_masters))
            for question_id in active_members:
                membership = self._make_membership(
                    master_id,
                    question_id,
                    MasterMembershipType.EXACT,
                    1.0,
                )
                self.repository.save_membership(membership)
                results[question_id] = MasterAssignmentResult(
                    question_id=question_id,
                    status=MasterAssignmentStatus.ASSIGNED,
                    master_question_id=master_id,
                    relationship=MasterMembershipType.EXACT,
                    reason="assigned through an exact-equivalence component",
                )
            return

        external = self._external_candidates(
            component,
            matches,
        )
        exact_masters = {
            master_id
            for master_id, relationship, _ in external
            if relationship is MasterMembershipType.EXACT
        }
        if len(exact_masters) > 1:
            self._mark_ambiguous(
                active_members,
                results,
                tuple(sorted(exact_masters)),
                "exact matches point to multiple existing masters",
            )
            return
        if len(exact_masters) == 1:
            master_id = next(iter(exact_masters))
            self._assign_to_master(
                active_members,
                master_id,
                matches,
                results,
                exact=True,
            )
            return

        rephrased_candidates = [
            candidate
            for candidate in external
            if candidate[1] is MasterMembershipType.REPHRASED
        ]
        eligible = [
            candidate
            for candidate in rephrased_candidates
            if candidate[2] >= self.service.policy.min_rephrased_confidence
        ]
        selected = self.service._select(eligible)
        if selected is not None:
            self._assign_to_master(
                active_members,
                selected[0],
                matches,
                results,
                exact=False,
            )
            return
        if len({item[0] for item in eligible}) > 1:
            self._mark_ambiguous(
                active_members,
                results,
                tuple(sorted({item[0] for item in eligible})),
                "rephrased candidates do not have a safe winner",
            )
            return

        canonical_id = min(
            active_members,
            key=lambda question_id: (
                questions_by_id[question_id].document_id,
                questions_by_id[question_id].question_number,
                question_id,
            ),
        )
        question = questions_by_id[canonical_id]
        master = MasterQuestion(
            master_question_id=f"master:{canonical_id}",
            canonical_question_id=canonical_id,
            stem=question.stem,
            options=question.options,
            kind=question.kind,
        )
        self.repository.save_master(master)

        for question_id in active_members:
            relationship = (
                MasterMembershipType.CANONICAL
                if question_id == canonical_id
                else MasterMembershipType.EXACT
            )
            confidence = 1.0
            self.repository.save_membership(
                self._make_membership(
                    master.master_question_id,
                    question_id,
                    relationship,
                    confidence,
                )
            )
            results[question_id] = MasterAssignmentResult(
                question_id=question_id,
                status=(
                    MasterAssignmentStatus.CREATED
                    if question_id == canonical_id
                    else MasterAssignmentStatus.ASSIGNED
                ),
                master_question_id=master.master_question_id,
                relationship=relationship,
                reason=(
                    "created deterministic master for exact batch component"
                    if question_id == canonical_id
                    else "assigned through exact batch component"
                ),
            )

    def _assign_to_master(
        self,
        question_ids: list[str],
        master_id: str,
        matches: tuple[QuestionMatch, ...],
        results: dict[str, MasterAssignmentResult],
        *,
        exact: bool,
    ) -> None:
        for question_id in question_ids:
            relationship = MasterMembershipType.EXACT
            confidence = 1.0

            if not exact:
                direct_rephrased = []
                for match in matches:
                    if (
                        match.match_type is not MatchType.REPHRASED
                        or question_id
                        not in (match.left_question_id, match.right_question_id)
                    ):
                        continue
                    other_id = self._other_question(question_id, match)
                    if other_id is None:
                        continue
                    other_master = self.repository.get_master_for_question(other_id)
                    if (
                        other_master is not None
                        and other_master.master_question_id == master_id
                        and self._is_active(other_master)
                    ):
                        direct_rephrased.append(match.confidence)
                if direct_rephrased:
                    relationship = MasterMembershipType.REPHRASED
                    confidence = max(direct_rephrased)

            self.repository.save_membership(
                self._make_membership(
                    master_id,
                    question_id,
                    relationship,
                    confidence,
                )
            )
            results[question_id] = MasterAssignmentResult(
                question_id=question_id,
                status=MasterAssignmentStatus.ASSIGNED,
                master_question_id=master_id,
                relationship=relationship,
                reason="assigned to safe existing master from batch evidence",
            )

    def _external_candidates(
        self,
        component: tuple[str, ...],
        matches: tuple[QuestionMatch, ...],
    ) -> list[tuple[str, MasterMembershipType, float]]:
        component_ids = set(component)
        result = []
        for match in matches:
            if match.match_type not in {
                MatchType.EXACT,
                MatchType.REPHRASED,
            }:
                continue

            if match.left_question_id in component_ids:
                other_id = match.right_question_id
                current_id = match.left_question_id
            elif match.right_question_id in component_ids:
                other_id = match.left_question_id
                current_id = match.right_question_id
            else:
                continue

            if other_id in component_ids:
                continue

            master = self.repository.get_master_for_question(other_id)
            if master is None or not self._is_active(master):
                continue

            relationship = (
                MasterMembershipType.EXACT
                if match.match_type is MatchType.EXACT
                else MasterMembershipType.REPHRASED
            )
            result.append((master.master_question_id, relationship, match.confidence))
        return result

    @staticmethod
    def _other_question(
        question_id: str,
        match: QuestionMatch,
    ) -> str | None:
        if match.left_question_id == question_id:
            return match.right_question_id
        if match.right_question_id == question_id:
            return match.left_question_id
        return None

    @staticmethod
    def _make_membership(
        master_id: str,
        question_id: str,
        relationship: MasterMembershipType,
        confidence: float,
    ):
        from ai_comp.domain.master_questions import MasterQuestionMembership

        return MasterQuestionMembership(
            master_question_id=master_id,
            question_id=question_id,
            relationship=relationship,
            confidence=confidence,
        )

    @staticmethod
    def _is_active(master: MasterQuestion) -> bool:
        return master.status.value == "ACTIVE"

    @staticmethod
    def _already_assigned(
        question_id: str,
        master_ids: set[str],
    ) -> MasterAssignmentResult:
        return MasterAssignmentResult(
            question_id=question_id,
            status=MasterAssignmentStatus.ALREADY_ASSIGNED,
            master_question_id=next(iter(master_ids)) if master_ids else None,
            reason="question already belongs to an existing master",
        )

    @staticmethod
    def _mark_ambiguous(
        question_ids: list[str],
        results: dict[str, MasterAssignmentResult],
        competing: tuple[str, ...],
        reason: str,
    ) -> None:
        for question_id in question_ids:
            results[question_id] = MasterAssignmentResult(
                question_id=question_id,
                status=MasterAssignmentStatus.AMBIGUOUS,
                competing_master_ids=competing,
                reason=reason,
            )
