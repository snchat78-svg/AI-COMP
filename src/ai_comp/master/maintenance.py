from ai_comp.domain.master_questions import (
    MasterMembershipType,
    MasterQuestionStatus,
)
from ai_comp.master.repository import MasterQuestionRepository
from ai_comp.master.view import MasterMergeResult, MasterRepairResult


class MasterQuestionMaintenanceService:
    """Controlled maintenance operations for canonical question groups."""

    def __init__(self, repository: MasterQuestionRepository) -> None:
        self.repository = repository

    def merge(
        self,
        source_master_id: str,
        target_master_id: str,
        *,
        reason: str,
    ) -> MasterMergeResult:
        if not reason.strip():
            raise ValueError("merge reason must not be empty")
        if source_master_id == target_master_id:
            raise ValueError("source and target masters must differ")

        moved = self.repository.merge_masters(
            source_master_id,
            target_master_id,
            reason=reason.strip(),
        )
        return MasterMergeResult(
            source_master_id=source_master_id,
            target_master_id=target_master_id,
            moved_question_count=moved,
            reason=reason.strip(),
        )

    def repair(
        self,
        question_id: str,
        target_master_id: str,
        *,
        relationship: MasterMembershipType,
        confidence: float,
        reason: str,
    ) -> MasterRepairResult:
        if relationship is MasterMembershipType.CANONICAL:
            raise ValueError(
                "canonical membership cannot be moved by ordinary repair"
            )
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not reason.strip():
            raise ValueError("repair reason must not be empty")

        membership = self.repository.get_membership_for_question(question_id)
        if membership is None:
            raise ValueError("question has no current master membership")
        if membership.master_question_id == target_master_id:
            raise ValueError("question is already assigned to target master")

        self.repository.reassign_question(
            question_id,
            target_master_id,
            relationship=relationship,
            confidence=confidence,
            reason=reason.strip(),
        )
        return MasterRepairResult(
            question_id=question_id,
            source_master_id=membership.master_question_id,
            target_master_id=target_master_id,
            relationship=relationship,
            confidence=confidence,
            reason=reason.strip(),
        )
