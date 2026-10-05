from typing import Protocol

from ai_comp.domain.master_questions import (
    MasterQuestion,
    MasterQuestionMembership,
    MasterQuestionStatus,
    MasterMembershipType,
)


class MasterQuestionRepository(Protocol):
    """Database-neutral persistence contract for canonical question groups."""

    def save_master(self, master: MasterQuestion) -> None: ...
    def get_master(self, master_question_id: str) -> MasterQuestion | None: ...
    def get_master_for_question(
        self,
        question_id: str,
    ) -> MasterQuestion | None: ...
    def list_masters(
        self,
        *,
        status: MasterQuestionStatus | None = None,
        concept_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[MasterQuestion, ...]: ...
    def save_membership(self, membership: MasterQuestionMembership) -> None: ...
    def get_membership_for_question(
        self,
        question_id: str,
    ) -> MasterQuestionMembership | None: ...
    def get_memberships_for_master(
        self,
        master_question_id: str,
    ) -> tuple[MasterQuestionMembership, ...]: ...
    def merge_masters(
        self,
        source_master_id: str,
        target_master_id: str,
        *,
        reason: str,
    ) -> int: ...
    def reassign_question(
        self,
        question_id: str,
        target_master_id: str,
        *,
        relationship: MasterMembershipType,
        confidence: float,
        reason: str,
    ) -> None: ...


class InMemoryMasterQuestionRepository:
    """Deterministic repository used by unit tests and local development."""

    def __init__(self) -> None:
        self._masters: dict[str, MasterQuestion] = {}
        self._memberships_by_question: dict[str, MasterQuestionMembership] = {}
        self._memberships_by_master: dict[
            str, dict[str, MasterQuestionMembership]
        ] = {}
        self._merge_events: list[tuple[str, str, str]] = []
        self._repair_events: list[tuple[str, str, str, str]] = []

    def save_master(self, master: MasterQuestion) -> None:
        existing = self._masters.get(master.master_question_id)
        if existing is not None and existing != master:
            raise ValueError(
                "master_question_id already exists with different data"
            )

        for other in self._masters.values():
            if (
                other.master_question_id != master.master_question_id
                and other.canonical_question_id == master.canonical_question_id
            ):
                raise ValueError(
                    "canonical question is already owned by a different master"
                )

        self._masters[master.master_question_id] = master

    def get_master(self, master_question_id: str) -> MasterQuestion | None:
        return self._masters.get(master_question_id)

    def get_master_for_question(
        self,
        question_id: str,
    ) -> MasterQuestion | None:
        membership = self._memberships_by_question.get(question_id)
        if membership is None:
            return None
        return self._masters.get(membership.master_question_id)

    def list_masters(
        self,
        *,
        status: MasterQuestionStatus | None = None,
        concept_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[MasterQuestion, ...]:
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        if offset < 0:
            raise ValueError("offset must be non-negative")

        masters = sorted(
            (
                master
                for master in self._masters.values()
                if (status is None or master.status is status)
                and (concept_id is None or master.concept_id == concept_id)
            ),
            key=lambda item: item.master_question_id,
        )
        return tuple(masters[offset : offset + limit])

    def save_membership(self, membership: MasterQuestionMembership) -> None:
        existing = self._memberships_by_question.get(membership.question_id)
        if existing is not None and existing != membership:
            raise ValueError(
                "question is already assigned to a different master question"
            )

        if membership.master_question_id not in self._masters:
            raise ValueError(
                "membership references an unknown master question"
            )

        self._memberships_by_question[membership.question_id] = membership
        self._memberships_by_master.setdefault(
            membership.master_question_id, {}
        )[membership.question_id] = membership

    def get_membership_for_question(
        self,
        question_id: str,
    ) -> MasterQuestionMembership | None:
        return self._memberships_by_question.get(question_id)

    def get_memberships_for_master(
        self,
        master_question_id: str,
    ) -> tuple[MasterQuestionMembership, ...]:
        return tuple(
            self._memberships_by_master.get(master_question_id, {}).values()
        )

    def merge_masters(
        self,
        source_master_id: str,
        target_master_id: str,
        *,
        reason: str,
    ) -> int:
        source = self._require_active_master(source_master_id)
        target = self._require_active_master(target_master_id)
        if source_master_id == target_master_id:
            raise ValueError("source and target masters must differ")

        source_members = list(
            self._memberships_by_master.get(source_master_id, {}).values()
        )
        moved = 0
        for membership in source_members:
            if self._memberships_by_question.get(membership.question_id) != membership:
                raise ValueError("master membership index is inconsistent")
            relationship = (
                MasterMembershipType.EXACT
                if membership.relationship is MasterMembershipType.CANONICAL
                else membership.relationship
            )
            replacement = MasterQuestionMembership(
                master_question_id=target_master_id,
                question_id=membership.question_id,
                relationship=relationship,
                confidence=membership.confidence,
            )
            self._memberships_by_question[membership.question_id] = replacement
            self._memberships_by_master.setdefault(
                target_master_id, {}
            )[membership.question_id] = replacement
            del self._memberships_by_master[source_master_id][membership.question_id]
            moved += 1

        self._masters[source_master_id] = MasterQuestion(
            master_question_id=source.master_question_id,
            canonical_question_id=source.canonical_question_id,
            stem=source.stem,
            options=source.options,
            kind=source.kind,
            concept_id=source.concept_id,
            status=MasterQuestionStatus.MERGED,
            merged_into_master_id=target_master_id,
        )
        self._merge_events.append((source_master_id, target_master_id, reason))
        return moved

    def reassign_question(
        self,
        question_id: str,
        target_master_id: str,
        *,
        relationship: MasterMembershipType,
        confidence: float,
        reason: str,
    ) -> None:
        target = self._require_active_master(target_master_id)
        if relationship is MasterMembershipType.CANONICAL:
            raise ValueError("canonical membership cannot be reassigned")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        current = self._memberships_by_question.get(question_id)
        if current is None:
            raise ValueError("question has no current master membership")
        if current.master_question_id == target_master_id:
            raise ValueError("question is already assigned to target master")
        if current.relationship is MasterMembershipType.CANONICAL:
            raise ValueError("canonical membership cannot be reassigned")

        existing_target = self._memberships_by_master.get(
            target_master_id, {}
        ).get(question_id)
        if existing_target is not None:
            raise ValueError("target master already contains the question")

        replacement = MasterQuestionMembership(
            master_question_id=target_master_id,
            question_id=question_id,
            relationship=relationship,
            confidence=confidence,
        )
        self._memberships_by_question[question_id] = replacement
        del self._memberships_by_master[current.master_question_id][question_id]
        self._memberships_by_master.setdefault(
            target_master_id, {}
        )[question_id] = replacement
        self._repair_events.append(
            (
                question_id,
                current.master_question_id,
                target_master_id,
                reason,
            )
        )

    def _require_active_master(self, master_question_id: str) -> MasterQuestion:
        master = self._masters.get(master_question_id)
        if master is None:
            raise ValueError(f"master question not found: {master_question_id}")
        if master.status is not MasterQuestionStatus.ACTIVE:
            raise ValueError(
                f"master question is not active: {master_question_id}"
            )
        return master
