from dataclasses import dataclass
from enum import Enum

from ai_comp.domain.questions import QuestionKind, QuestionOption


class MasterQuestionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MERGED = "MERGED"
    RETIRED = "RETIRED"


class MasterMembershipType(str, Enum):
    CANONICAL = "CANONICAL"
    EXACT = "EXACT"
    REPHRASED = "REPHRASED"


class MasterAssignmentStatus(str, Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    ALREADY_ASSIGNED = "ALREADY_ASSIGNED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class MasterQuestion:
    """Canonical question identity used by the master question database."""

    master_question_id: str
    canonical_question_id: str
    stem: str
    options: tuple[QuestionOption, ...]
    kind: QuestionKind
    concept_id: str | None = None
    status: MasterQuestionStatus = MasterQuestionStatus.ACTIVE
    merged_into_master_id: str | None = None

    def __post_init__(self) -> None:
        if not self.master_question_id:
            raise ValueError("master_question_id must not be empty")
        if not self.canonical_question_id:
            raise ValueError("canonical_question_id must not be empty")
        if self.status is MasterQuestionStatus.MERGED and not self.merged_into_master_id:
            raise ValueError("merged master questions require merged_into_master_id")
        if self.status is not MasterQuestionStatus.MERGED and self.merged_into_master_id:
            raise ValueError(
                "only merged master questions may reference merged_into_master_id"
            )


@dataclass(frozen=True)
class MasterQuestionMembership:
    """Links one observed question to exactly one master identity."""

    master_question_id: str
    question_id: str
    relationship: MasterMembershipType
    confidence: float

    def __post_init__(self) -> None:
        if not self.master_question_id or not self.question_id:
            raise ValueError("master_question_id and question_id are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class MasterAssignmentResult:
    question_id: str
    status: MasterAssignmentStatus
    master_question_id: str | None = None
    relationship: MasterMembershipType | None = None
    competing_master_ids: tuple[str, ...] = ()
    reason: str = ""
