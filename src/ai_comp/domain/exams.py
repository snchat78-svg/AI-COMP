from dataclasses import dataclass, field
from enum import Enum


class ExamLevel(str, Enum):
    STATE = "STATE"
    NATIONAL = "NATIONAL"


@dataclass(frozen=True)
class ConductingBody:
    body_id: str
    name: str
    level: ExamLevel
    country: str = "IN"
    state: str | None = None
    official_domains: tuple[str, ...] = ()


@dataclass(frozen=True)
class Exam:
    exam_id: str
    name: str
    conducting_body_id: str
    level: ExamLevel
    state: str | None = None
    categories: tuple[str, ...] = ()
    active: bool = True


@dataclass(frozen=True)
class PaperCategory:
    category_id: str
    name: str
    exam_id: str
    description: str = ""
    allowed_formats: tuple[str, ...] = field(default_factory=lambda: ("pdf", "html"))
