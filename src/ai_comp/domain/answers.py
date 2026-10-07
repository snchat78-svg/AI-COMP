from dataclasses import dataclass
from enum import Enum

from ai_comp.domain.questions import AnswerKeyEntry, QuestionCandidate


class AnswerResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    MISSING_QUESTION = "MISSING_QUESTION"
    INVALID_OPTION = "INVALID_OPTION"
    AMBIGUOUS = "AMBIGUOUS"


class AnswerResolutionMethod(str, Enum):
    DIRECT_OPTION_KEY = "DIRECT_OPTION_KEY"
    POSITIONAL_NUMERIC = "POSITIONAL_NUMERIC"
    POSITIONAL_HINDI = "POSITIONAL_HINDI"


@dataclass(frozen=True)
class AnswerResolution:
    question_id: str
    document_id: str
    question_number: int
    answer_key: str
    selected_option_key: str | None
    status: AnswerResolutionStatus
    method: AnswerResolutionMethod | None
    source_line: int
    notes: str = ""


class AnswerKeyResolver:
    """Maps source answer-key entries to extracted options without inventing answers."""

    HINDI_OPTION_ORDER = ("क", "ख", "ग", "घ", "ङ", "च", "छ", "ज", "झ")

    def resolve(
        self,
        question: QuestionCandidate | None,
        entry: AnswerKeyEntry,
    ) -> AnswerResolution:
        if question is None:
            return AnswerResolution(
                question_id="",
                document_id="",
                question_number=entry.question_number,
                answer_key=entry.answer_key,
                selected_option_key=None,
                status=AnswerResolutionStatus.MISSING_QUESTION,
                method=None,
                source_line=entry.line_number,
                notes="no extracted question has the referenced question number",
            )

        key = entry.answer_key.strip().upper()
        option_keys = tuple(option.key.upper() for option in question.options)

        if key in option_keys:
            return AnswerResolution(
                question_id=question.question_id,
                document_id=question.document_id,
                question_number=question.question_number,
                answer_key=entry.answer_key,
                selected_option_key=key,
                status=AnswerResolutionStatus.RESOLVED,
                method=AnswerResolutionMethod.DIRECT_OPTION_KEY,
                source_line=entry.line_number,
            )

        if key.isdigit():
            position = int(key)
            if 1 <= position <= len(question.options):
                return AnswerResolution(
                    question_id=question.question_id,
                    document_id=question.document_id,
                    question_number=question.question_number,
                    answer_key=entry.answer_key,
                    selected_option_key=question.options[position - 1].key,
                    status=AnswerResolutionStatus.RESOLVED,
                    method=AnswerResolutionMethod.POSITIONAL_NUMERIC,
                    source_line=entry.line_number,
                )

        if key in self.HINDI_OPTION_ORDER:
            position = self.HINDI_OPTION_ORDER.index(key)
            if position < len(question.options):
                return AnswerResolution(
                    question_id=question.question_id,
                    document_id=question.document_id,
                    question_number=question.question_number,
                    answer_key=entry.answer_key,
                    selected_option_key=question.options[position].key,
                    status=AnswerResolutionStatus.RESOLVED,
                    method=AnswerResolutionMethod.POSITIONAL_HINDI,
                    source_line=entry.line_number,
                )

        return AnswerResolution(
            question_id=question.question_id,
            document_id=question.document_id,
            question_number=question.question_number,
            answer_key=entry.answer_key,
            selected_option_key=None,
            status=AnswerResolutionStatus.INVALID_OPTION,
            method=None,
            source_line=entry.line_number,
            notes="answer key does not map to an extracted option",
        )

    def resolve_many(
        self,
        questions: tuple[QuestionCandidate, ...],
        entries: tuple[AnswerKeyEntry, ...],
    ) -> tuple[AnswerResolution, ...]:
        by_number: dict[int, list[QuestionCandidate]] = {}
        for question in questions:
            by_number.setdefault(question.question_number, []).append(question)

        resolutions = []
        for entry in entries:
            candidates = by_number.get(entry.question_number, [])
            if len(candidates) > 1:
                resolutions.append(
                    AnswerResolution(
                        question_id="",
                        document_id="",
                        question_number=entry.question_number,
                        answer_key=entry.answer_key,
                        selected_option_key=None,
                        status=AnswerResolutionStatus.AMBIGUOUS,
                        method=None,
                        source_line=entry.line_number,
                        notes="multiple extracted questions share the same question number",
                    )
                )
                continue
            question = candidates[0] if candidates else None
            resolutions.append(self.resolve(question, entry))
        return tuple(resolutions)
