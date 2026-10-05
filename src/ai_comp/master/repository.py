from typing import Protocol

from ai_comp.domain.master_questions import (
    MasterQuestion,
    MasterQuestionMembership,
)


class MasterQuestionRepository(Protocol):
    """Database-neutral persistence contract for canonical question groups."""

    def save_master(self, master: MasterQuestion) -> None: ...
    def get_master(self, master_question_id: str) -> MasterQuestion | None: ...
    def get_master_for_question(
        self,
        question_id: str,
    ) -> MasterQuestion | None: ...
    def save_membership(self, membership: MasterQuestionMembership) -> None: ...
    def get_membership_for_question(
        self,
        question_id: str,
    ) -> MasterQuestionMembership | None: ...
    def get_memberships_for_master(
        self,
        master_question_id: str,
    ) -> tuple[MasterQuestionMembership, ...]: ...


class InMemoryMasterQuestionRepository:
    """Deterministic repository used by unit tests and local development."""

    def __init__(self) -> None:
        self._masters: dict[str, MasterQuestion] = {}
        self._memberships_by_question: dict[str, MasterQuestionMembership] = {}
        self._memberships_by_master: dict[
            str, dict[str, MasterQuestionMembership]
        ] = {}

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
