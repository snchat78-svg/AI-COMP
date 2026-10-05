from dataclasses import dataclass

from ai_comp.domain.exams import ConductingBody, Exam, PaperCategory
from ai_comp.domain.sources import SourceRecord
from ai_comp.domain.verification import SourceVerification


@dataclass(frozen=True)
class RegistrySnapshot:
    conducting_bodies: tuple[ConductingBody, ...] = ()
    exams: tuple[Exam, ...] = ()
    paper_categories: tuple[PaperCategory, ...] = ()
    sources: tuple[SourceRecord, ...] = ()
    verifications: tuple[SourceVerification, ...] = ()
