from dataclasses import dataclass

from ai_comp.domain.master_questions import MasterQuestionStatus
from ai_comp.master.repository import MasterQuestionRepository
from ai_comp.master.view import MasterQuestionView


@dataclass(frozen=True)
class MasterQuestionQuery:
    """Bounded filters for the master-question read model."""

    status: MasterQuestionStatus | None = None
    concept_id: str | None = None
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("offset must be non-negative")


class MasterQuestionReadService:
    """Builds stable master-question views from the persistence contract."""

    def __init__(self, repository: MasterQuestionRepository) -> None:
        self.repository = repository

    def get_view(self, master_question_id: str) -> MasterQuestionView | None:
        master = self.repository.get_master(master_question_id)
        if master is None:
            return None
        return self._view(master)

    def list_views(
        self,
        query: MasterQuestionQuery | None = None,
    ) -> tuple[MasterQuestionView, ...]:
        query = query or MasterQuestionQuery()
        masters = self.repository.list_masters(
            status=query.status,
            concept_id=query.concept_id,
            limit=query.limit,
            offset=query.offset,
        )
        return tuple(self._view(master) for master in masters)

    def _view(self, master) -> MasterQuestionView:
        memberships = self.repository.get_memberships_for_master(
            master.master_question_id
        )
        exact_count = sum(
            item.relationship.value == "EXACT" for item in memberships
        )
        rephrased_count = sum(
            item.relationship.value == "REPHRASED" for item in memberships
        )
        return MasterQuestionView(
            master_question_id=master.master_question_id,
            canonical_question_id=master.canonical_question_id,
            stem=master.stem,
            options=master.options,
            kind=master.kind,
            concept_id=master.concept_id,
            status=master.status.value,
            member_count=len(memberships),
            exact_count=exact_count,
            rephrased_count=rephrased_count,
        )
