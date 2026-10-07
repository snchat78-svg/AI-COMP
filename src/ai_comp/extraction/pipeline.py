from collections.abc import Iterable
from dataclasses import dataclass

from ai_comp.domain.questions import QuestionExtractionResult
from ai_comp.extraction.question_extractor import QuestionExtractor
from ai_comp.research.processing import NormalizedDocument


@dataclass(frozen=True)
class QuestionExtractionBatch:
    documents: tuple[NormalizedDocument, ...]
    results: tuple[QuestionExtractionResult, ...]


class QuestionExtractionPipeline:
    """Phase 3 boundary: normalized documents -> observed question candidates."""

    def __init__(self, extractor: QuestionExtractor | None = None) -> None:
        self.extractor = extractor or QuestionExtractor()

    def extract(
        self,
        documents: Iterable[NormalizedDocument],
    ) -> QuestionExtractionBatch:
        items = tuple(documents)
        results = tuple(self.extractor.extract(document) for document in items)
        return QuestionExtractionBatch(documents=items, results=results)
