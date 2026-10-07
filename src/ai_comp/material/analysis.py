from dataclasses import dataclass
from typing import Sequence

from ai_comp.domain.material_analysis import (
    ContentUnderstanding,
    ImportantFact,
    MaterialAnalysisPipeline,
    ProposedConcept,
)
from ai_comp.domain.materials import NormalizedMaterial


@dataclass(frozen=True)
class StaticMaterialAnalysisProvider:
    """Deterministic provider used by tests and local development."""

    understanding: ContentUnderstanding
    concepts: tuple[ProposedConcept, ...] = ()
    facts: tuple[ImportantFact, ...] = ()

    def understand(self, material: NormalizedMaterial) -> ContentUnderstanding:
        return self.understanding

    def extract_concepts(
        self,
        material: NormalizedMaterial,
        understanding: ContentUnderstanding,
    ) -> Sequence[ProposedConcept]:
        return self.concepts

    def extract_facts(
        self,
        material: NormalizedMaterial,
        understanding: ContentUnderstanding,
        concepts: Sequence[ProposedConcept],
    ) -> Sequence[ImportantFact]:
        return self.facts

    def analyze(self, material: NormalizedMaterial):
        return MaterialAnalysisPipeline(self).analyze(material)
