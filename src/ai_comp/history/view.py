from dataclasses import dataclass

from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.verification import VerificationStatus
from ai_comp.history.aggregator import QuestionHistory


@dataclass(frozen=True)
class HistoricalAppearanceView:
    """Read-only UI/API projection of one verified or unverified appearance."""

    appearance_id: str
    question_id: str
    exam_id: str
    conducting_body_id: str | None
    year: int
    exam_date: str | None
    shift: str | None
    question_number: int
    original_question: str
    options: tuple[tuple[str, str], ...]
    correct_answer: str | None
    source_url: str
    paper_id: str
    verification_status: VerificationStatus
    match_type: str

    @classmethod
    def from_appearance(cls, appearance: ExamAppearance) -> "HistoricalAppearanceView":
        return cls(
            appearance_id=appearance.appearance_id,
            question_id=appearance.question_id,
            exam_id=appearance.exam_id,
            conducting_body_id=appearance.conducting_body_id,
            year=appearance.year,
            exam_date=appearance.exam_date,
            shift=appearance.shift,
            question_number=appearance.question_number,
            original_question=appearance.original_question,
            options=appearance.options,
            correct_answer=appearance.correct_answer,
            source_url=appearance.source_url,
            paper_id=appearance.paper_id,
            verification_status=appearance.verification.status,
            match_type=appearance.match_type,
        )


@dataclass(frozen=True)
class HistoricalQuestionView:
    """Stable read model for the question-history screen/API."""

    question_id: str
    verified_appearance_count: int
    verified_history_text: str
    exact_appearances: tuple[HistoricalAppearanceView, ...]
    rephrased_appearances: tuple[HistoricalAppearanceView, ...]
    same_concept_appearances: tuple[HistoricalAppearanceView, ...]
    related_topic_appearances: tuple[HistoricalAppearanceView, ...]

    @classmethod
    def from_history(cls, history: QuestionHistory) -> "HistoricalQuestionView":
        convert = lambda items: tuple(
            HistoricalAppearanceView.from_appearance(item) for item in items
        )
        return cls(
            question_id=history.question_id,
            verified_appearance_count=history.verified_appearance_count,
            verified_history_text=history.verified_history_text,
            exact_appearances=convert(history.exact_appearances),
            rephrased_appearances=convert(history.rephrased_appearances),
            same_concept_appearances=convert(history.same_concept_appearances),
            related_topic_appearances=convert(history.related_topic_appearances),
        )
