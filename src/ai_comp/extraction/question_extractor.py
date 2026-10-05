import re
from collections.abc import Iterable

from ai_comp.domain.questions import (
    AnswerKeyEntry,
    QuestionCandidate,
    QuestionExtractionResult,
    QuestionKind,
    QuestionOption,
)
from ai_comp.research.processing import NormalizedDocument


_QUESTION_RE = re.compile(
    r"^\s*(?:(?:question|q)\s*[:.-]?\s*)?(\d{1,5})\s*[).:-]\s*(.*)$",
    re.IGNORECASE,
)

_QUESTION_PAREN_RE = re.compile(
    r"^\s*\(?q(?:uestion)?\s*(\d{1,5})\)?\s*[:.-]\s*(.*)$",
    re.IGNORECASE,
)

_OPTION_RE = re.compile(
    r"^\s*\(?([A-Ha-h])\)?\s*[).:-]\s*(.*)$"
)

_HINDI_OPTION_RE = re.compile(
    r"^\s*\(?([कखगघङचछजझ])\)?\s*[).:-]\s*(.*)$"
)

_NUMBER_OPTION_RE = re.compile(
    r"^\s*\(?([1-8])\)?\s*[).:-]\s*(.*)$"
)

_ANSWER_SECTION_RE = re.compile(
    r"^\s*(?:answer\s*key|answers?|correct\s*answers?|उत्तर\s*कुंजी|उत्तर\s*तालिका)\s*[:.-]?\s*$",
    re.IGNORECASE,
)

_ANSWER_RE = re.compile(
    r"^\s*(?:q(?:uestion)?\s*)?(\d{1,5})\s*(?:[).:-]|\s+)\s*([A-Ha-hकखगघङचछजझ1-8])\s*(?:\)|[).:-])?\s*$",
    re.IGNORECASE,
)


def _question_start(line: str) -> tuple[int, str] | None:
    match = _QUESTION_PAREN_RE.match(line) or _QUESTION_RE.match(line)
    if not match:
        return None
    return int(match.group(1)), match.group(2).strip()


def _option_match(line: str) -> tuple[str, str] | None:
    for pattern in (_OPTION_RE, _HINDI_OPTION_RE, _NUMBER_OPTION_RE):
        match = pattern.match(line)
        if match:
            return match.group(1), match.group(2).strip()
    return None


def _looks_like_answer_section(line: str) -> bool:
    return bool(_ANSWER_SECTION_RE.match(line))


def _parse_answer_line(line: str, line_number: int) -> AnswerKeyEntry | None:
    match = _ANSWER_RE.match(line)
    if not match:
        return None
    return AnswerKeyEntry(
        question_number=int(match.group(1)),
        answer_key=match.group(2).upper(),
        raw_text=line.strip(),
        line_number=line_number,
    )


class QuestionExtractor:
    """Extracts observed question/options from a NormalizedDocument only."""

    def __init__(self, min_options: int = 2, max_options: int = 8) -> None:
        if min_options < 0:
            raise ValueError("min_options must be non-negative")
        if max_options < min_options:
            raise ValueError("max_options must be >= min_options")
        self.min_options = min_options
        self.max_options = max_options

    def extract(self, document: NormalizedDocument) -> QuestionExtractionResult:
        lines = document.text.splitlines()
        questions: list[QuestionCandidate] = []
        answers: list[AnswerKeyEntry] = []
        warnings: list[str] = []

        current_number: int | None = None
        current_start = 0
        current_stem: list[str] = []
        current_options: list[QuestionOption] = []
        current_raw: list[str] = []
        in_answer_section = False

        def flush(end_line: int) -> None:
            nonlocal current_number, current_start, current_stem
            nonlocal current_options, current_raw
            if current_number is None:
                return
            stem = self._clean_text(current_stem)
            options = tuple(
                option
                for option in current_options
                if option.text
            )
            if not stem:
                warnings.append(
                    f"question {current_number} has no extracted stem"
                )
            elif len(options) < self.min_options:
                warnings.append(
                    f"question {current_number} has only {len(options)} options"
                )
            else:
                if len(options) > self.max_options:
                    warnings.append(
                        f"question {current_number} has more than {self.max_options} options"
                    )
                stable_options = options[: self.max_options]
                question_id = (
                    f"{document.document_id}:q:{current_number}:{current_start}"
                )
                questions.append(
                    QuestionCandidate(
                        question_id=question_id,
                        document_id=document.document_id,
                        document_sha256=document.metadata.sha256,
                        question_number=current_number,
                        stem=stem,
                        options=stable_options,
                        kind=QuestionKind.MCQ,
                        raw_text="\n".join(current_raw).strip(),
                        start_line=current_start,
                        end_line=end_line,
                    )
                )
            current_number = None
            current_stem = []
            current_options = []
            current_raw = []

        for index, line in enumerate(lines, start=1):
            if _looks_like_answer_section(line):
                flush(index - 1)
                in_answer_section = True
                continue

            if in_answer_section:
                answer = _parse_answer_line(line, index)
                if answer is not None:
                    answers.append(answer)
                continue

            started = _question_start(line)
            if started:
                flush(index - 1)
                current_number, first_text = started
                current_start = index
                current_raw = [line]
                current_stem = [first_text] if first_text else []
                current_options = []
                continue

            option = _option_match(line) if current_number is not None else None
            if option:
                current_options.append(
                    QuestionOption(key=option[0].upper(), text=option[1])
                )
                current_raw.append(line)
                continue

            if current_number is not None and line.strip():
                if current_options:
                    last = current_options[-1]
                    current_options[-1] = QuestionOption(
                        key=last.key,
                        text=self._clean_text([last.text, line]),
                    )
                else:
                    current_stem.append(line)
                current_raw.append(line)

        flush(len(lines))
        return QuestionExtractionResult(
            document_id=document.document_id,
            questions=tuple(questions),
            answer_key_entries=tuple(answers),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _clean_text(parts: Iterable[str]) -> str:
        return " ".join(part.strip() for part in parts if part.strip())
