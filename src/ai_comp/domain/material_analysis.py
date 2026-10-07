from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from ai_comp.domain.materials import NormalizedMaterial


@dataclass(frozen=True)
class ContentUnderstanding:
    material_id: str
    language: str
    summary: str
    key_points: tuple[str, ...]
    subject_hints: tuple[str, ...]
    topic_hints: tuple[str, ...]
    confidence: float

    def __post_init__(self) -> None:
        if not self.material_id.strip():
            raise ValueError("material_id must not be empty")
        if not self.language.strip():
            raise ValueError("language must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class ProposedConcept:
    concept_candidate_id: str
    material_id: str
    label: str
    subject: str | None
    topic: str | None
    subtopic: str | None
    evidence_text: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.concept_candidate_id.strip():
            raise ValueError("concept_candidate_id must not be empty")
        if not self.material_id.strip() or not self.label.strip():
            raise ValueError("material_id and concept label are required")
        if not self.evidence_text.strip():
            raise ValueError("concept evidence_text must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class ImportantFact:
    fact_id: str
    material_id: str
    fact_text: str
    evidence_text: str
    importance_score: float
    confidence: float
    fact_type: str = "GENERAL"

    def __post_init__(self) -> None:
        if not self.fact_id.strip() or not self.material_id.strip():
            raise ValueError("fact_id and material_id are required")
        if not self.fact_text.strip():
            raise ValueError("fact_text must not be empty")
        if not self.evidence_text.strip():
            raise ValueError("fact evidence_text must not be empty")
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError("importance_score must be between 0 and 1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.fact_type.strip():
            raise ValueError("fact_type must not be empty")


class MaterialAnalysisProvider(Protocol):
    def understand(self, material: NormalizedMaterial) -> ContentUnderstanding: ...

    def extract_concepts(
        self,
        material: NormalizedMaterial,
        understanding: ContentUnderstanding,
    ) -> Sequence[ProposedConcept]: ...

    def extract_facts(
        self,
        material: NormalizedMaterial,
        understanding: ContentUnderstanding,
        concepts: Sequence[ProposedConcept],
    ) -> Sequence[ImportantFact]: ...


@dataclass(frozen=True)
class MaterialAnalysisResult:
    material_id: str
    understanding: ContentUnderstanding
    concepts: tuple[ProposedConcept, ...]
    facts: tuple[ImportantFact, ...]
    warnings: tuple[str, ...] = ()


class MaterialAnalysisPipeline:
    """Runs grounded material understanding before question generation."""

    def __init__(self, provider: MaterialAnalysisProvider) -> None:
        self.provider = provider

    def analyze(self, material: NormalizedMaterial) -> MaterialAnalysisResult:
        if not material.text.strip():
            raise ValueError("material text is empty")

        understanding = self.provider.understand(material)
        if understanding.material_id != material.material_id:
            raise ValueError("understanding material_id does not match input")

        concepts = tuple(
            self.provider.extract_concepts(material, understanding)
        )
        for concept in concepts:
            self._validate_evidence(
                material.text,
                concept.evidence_text,
                "concept",
            )
            if concept.material_id != material.material_id:
                raise ValueError("concept material_id does not match input")

        facts = tuple(
            self.provider.extract_facts(
                material,
                understanding,
                concepts,
            )
        )
        for fact in facts:
            self._validate_evidence(
                material.text,
                fact.evidence_text,
                "fact",
            )
            if fact.material_id != material.material_id:
                raise ValueError("fact material_id does not match input")

        warnings: list[str] = []
        if not concepts:
            warnings.append("no concepts were extracted")
        if not facts:
            warnings.append("no important facts were extracted")

        return MaterialAnalysisResult(
            material_id=material.material_id,
            understanding=understanding,
            concepts=concepts,
            facts=facts,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _validate_evidence(
        material_text: str,
        evidence_text: str,
        evidence_type: str,
    ) -> None:
        if evidence_text not in material_text:
            raise ValueError(
                f"{evidence_type} evidence_text must be grounded in material text"
            )
