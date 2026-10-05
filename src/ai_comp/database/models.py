from dataclasses import dataclass

from ai_comp.domain.exams import ConductingBody, Exam, PaperCategory
from ai_comp.domain.sources import SourceRecord
from ai_comp.domain.verification import SourceVerification
from ai_comp.research.paper import DocumentFormat


@dataclass(frozen=True)
class RegistrySnapshot:
    conducting_bodies: tuple[ConductingBody, ...] = ()
    exams: tuple[Exam, ...] = ()
    paper_categories: tuple[PaperCategory, ...] = ()
    sources: tuple[SourceRecord, ...] = ()
    verifications: tuple[SourceVerification, ...] = ()


@dataclass(frozen=True)
class PaperRecord:
    """Persistence model for a canonical research paper."""

    paper_id: str
    candidate_id: str | None = None
    title: str | None = None
    exam_id: str | None = None
    category_id: str | None = None
    source_id: str | None = None
    canonical_url: str | None = None
    year: int | None = None
    shift: str | None = None
