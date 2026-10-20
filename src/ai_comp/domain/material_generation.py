from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GeneratedQuestionStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class AnswerVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    UNCERTAIN = "UNCERTAIN"


class QuestionSourceKind(str, Enum):
    """Distinguishes model-generated items from source-backed exam history."""

    AI_GENERATED = "AI_GENERATED"
    VERIFIED_EXAM_HISTORY = "VERIFIED_EXAM_HISTORY"


@dataclass(frozen=True)
class GenerationSpecification:
    generation_id: str
    material_id: str
    fact_ids: tuple[str, ...]
    concept_ids: tuple[str, ...]
    existing_master_question_ids: tuple[str, ...] = ()
    requested_count: int = 1
    difficulty: str = "MEDIUM"
    language: str = "hi"

    def __post_init__(self) -> None:
        if not self.generation_id.strip() or not self.material_id.strip():
            raise ValueError("generation_id and material_id are required")
        if not self.fact_ids and not self.concept_ids:
            raise ValueError("generation requires at least one fact or concept")
        if self.requested_count < 1 or self.requested_count > 100:
            raise ValueError("requested_count must be between 1 and 100")
        if not self.difficulty.strip() or not self.language.strip():
            raise ValueError("difficulty and language are required")


@dataclass(frozen=True)
class GeneratedOption:
    key: str
    text: str

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.text.strip():
            raise ValueError("generated option key and text are required")


@dataclass(frozen=True)
class GeneratedMCQ:
    generated_question_id: str
    generation_id: str
    material_id: str
    stem: str
    options: tuple[GeneratedOption, ...]
    correct_option_key: str
    explanation: str
    fact_ids: tuple[str, ...]
    concept_ids: tuple[str, ...]
    difficulty: str
    importance_score: float
    answer_verification: AnswerVerificationStatus = AnswerVerificationStatus.UNCERTAIN
    answer_verification_evidence: tuple[str, ...] = ()
    status: GeneratedQuestionStatus = GeneratedQuestionStatus.REJECTED
    quality_score: float = 0.0
    duplicate_of_master_question_id: str | None = None
    source_kind: QuestionSourceKind = QuestionSourceKind.AI_GENERATED
    source_url: str | None = None
    answer_key_source_url: str | None = None
    exam_name: str | None = None
    exam_id: str | None = None
    exam_year: int | None = None
    exam_shift: str | None = None
    exam_question_number: int | None = None
    verified_appearance_count: int = 0

    def __post_init__(self) -> None:
        if not self.generated_question_id.strip() or not self.generation_id.strip():
            raise ValueError("generated question identity is required")
        if not self.material_id.strip() or not self.stem.strip():
            raise ValueError("material_id and stem are required")
        if len(self.options) != 4:
            raise ValueError("generated MCQ must contain exactly four options")
        keys = [option.key.strip().upper() for option in self.options]
        if len(set(keys)) != 4:
            raise ValueError("generated MCQ option keys must be unique")
        if self.correct_option_key.strip().upper() not in set(keys):
            raise ValueError("correct_option_key must reference an option")
        if not self.explanation.strip():
            raise ValueError("explanation is required")
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError("importance_score must be between 0 and 1")
        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError("quality_score must be between 0 and 1")
        if self.verified_appearance_count < 0:
            raise ValueError("verified_appearance_count must be non-negative")
        if self.source_kind is QuestionSourceKind.VERIFIED_EXAM_HISTORY:
            if not self.source_url or not self.source_url.startswith("https://"):
                raise ValueError("verified historical question requires an HTTPS paper URL")
            if not self.answer_key_source_url or not self.answer_key_source_url.startswith("https://"):
                raise ValueError("verified historical question requires an HTTPS answer-key URL")
            if not self.exam_name or not self.exam_name.strip() or not self.exam_id or not self.exam_id.strip():
                raise ValueError("verified historical question requires exam identity")
            if self.exam_year is None or self.exam_year < 1900:
                raise ValueError("verified historical question requires a valid exam year")
            if self.exam_question_number is None or self.exam_question_number < 1:
                raise ValueError("verified historical question requires its exam question number")
            if self.verified_appearance_count < 1:
                raise ValueError("verified historical question requires at least one verified appearance")
            if self.answer_verification is not AnswerVerificationStatus.VERIFIED:
                raise ValueError("verified historical question requires verified answer")
            if not self.answer_verification_evidence:
                raise ValueError("verified historical question requires provenance evidence")
        if self.status is GeneratedQuestionStatus.ACCEPTED:
            if self.answer_verification is not AnswerVerificationStatus.VERIFIED:
                raise ValueError("accepted question requires verified answer")
            if self.duplicate_of_master_question_id is not None:
                raise ValueError("accepted question cannot be a known duplicate")


@dataclass(frozen=True)
class AnswerVerificationResult:
    status: AnswerVerificationStatus
    evidence: tuple[str, ...] = ()
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("verification confidence must be between 0 and 1")
        if self.status is AnswerVerificationStatus.VERIFIED and not self.evidence:
            raise ValueError("verified answer requires evidence")


@dataclass(frozen=True)
class GenerationResult:
    specification: GenerationSpecification
    questions: tuple[GeneratedMCQ, ...]
    rejected_question_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
