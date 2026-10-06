from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ai_comp.domain.matching import MatchEvidence, MatchType


class MaterialProbeType(str, Enum):
    QUESTION_TEXT = "QUESTION_TEXT"
    CONCEPT = "CONCEPT"


@dataclass(frozen=True)
class MaterialQuestionProbe:
    probe_id: str
    material_id: str
    text: str
    evidence_text: str
    probe_type: MaterialProbeType = MaterialProbeType.QUESTION_TEXT

    def __post_init__(self) -> None:
        if not self.probe_id.strip():
            raise ValueError("probe_id must not be empty")
        if not self.material_id.strip():
            raise ValueError("material_id must not be empty")
        if not self.text.strip():
            raise ValueError("probe text must not be empty")
        if not self.evidence_text.strip():
            raise ValueError("probe evidence_text must not be empty")
        if self.evidence_text not in self.text:
            raise ValueError("probe evidence_text must be grounded in probe text")


@dataclass(frozen=True)
class MaterialQuestionMatch:
    material_id: str
    probe_id: str
    probe_type: MaterialProbeType
    master_question_id: str
    match_type: MatchType
    confidence: float
    verified_appearance_count: int
    evidence: tuple[MatchEvidence, ...] = ()

    def __post_init__(self) -> None:
        if not self.material_id.strip() or not self.probe_id.strip():
            raise ValueError("material_id and probe_id are required")
        if not self.master_question_id.strip():
            raise ValueError("master_question_id must not be empty")
        if self.match_type is MatchType.NO_MATCH:
            raise ValueError("persisted material matches cannot be NO_MATCH")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.verified_appearance_count < 1:
            raise ValueError("material matches require verified appearance evidence")


@dataclass(frozen=True)
class MaterialMatchingResult:
    material_id: str
    existing_question_matches: tuple[MaterialQuestionMatch, ...]
    same_concept_matches: tuple[MaterialQuestionMatch, ...]
    related_topic_matches: tuple[MaterialQuestionMatch, ...]
    unmatched_question_probe_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def has_existing_question(self) -> bool:
        return bool(self.existing_question_matches)

    @property
    def existing_question_match_count(self) -> int:
        return len(self.existing_question_matches)
