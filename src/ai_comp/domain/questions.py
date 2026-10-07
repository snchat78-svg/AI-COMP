from dataclasses import dataclass
from enum import Enum


class QuestionKind(str, Enum):
    MCQ = "MCQ"
    TRUE_FALSE = "TRUE_FALSE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class QuestionOption:
    key: str
    text: str


@dataclass(frozen=True)
class QuestionCandidate:
    question_id: str
    document_id: str
    document_sha256: str
    question_number: int
    stem: str
    options: tuple[QuestionOption, ...]
    kind: QuestionKind
    raw_text: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class AnswerKeyEntry:
    question_number: int
    answer_key: str
    raw_text: str
    line_number: int


@dataclass(frozen=True)
class QuestionExtractionResult:
    document_id: str
    questions: tuple[QuestionCandidate, ...]
    answer_key_entries: tuple[AnswerKeyEntry, ...]
    warnings: tuple[str, ...] = ()
