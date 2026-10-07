from dataclasses import dataclass
from enum import Enum

from ai_comp.domain.master_questions import MasterMembershipType
from ai_comp.domain.questions import QuestionKind, QuestionOption


class MasterMaintenanceStatus(str, Enum):
    MERGED = "MERGED"
    REASSIGNED = "REASSIGNED"


@dataclass(frozen=True)
class MasterMergeResult:
    source_master_id: str
    target_master_id: str
    moved_question_count: int
    status: MasterMaintenanceStatus = MasterMaintenanceStatus.MERGED
    reason: str = ""


@dataclass(frozen=True)
class MasterRepairResult:
    question_id: str
    source_master_id: str
    target_master_id: str
    relationship: MasterMembershipType
    confidence: float
    status: MasterMaintenanceStatus = MasterMaintenanceStatus.REASSIGNED
    reason: str = ""


@dataclass(frozen=True)
class MasterQuestionView:
    master_question_id: str
    canonical_question_id: str
    stem: str
    options: tuple[QuestionOption, ...]
    kind: QuestionKind
    concept_id: str | None
    status: str
    member_count: int
    exact_count: int
    rephrased_count: int
