from ai_comp.domain.answers import AnswerResolution, AnswerResolutionStatus
from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.questions import QuestionCandidate
from ai_comp.domain.verification import SourceVerification


class ExamAppearanceBuilder:
    """Creates an exam occurrence from verified paper/question metadata."""

    def build(
        self,
        *,
        appearance_id: str,
        question: QuestionCandidate,
        exam_id: str,
        conducting_body_id: str | None,
        year: int,
        exam_date: str | None,
        shift: str | None,
        paper_id: str,
        source_url: str,
        verification: SourceVerification,
        correct_answer: str | None = None,
        answer_resolution: AnswerResolution | None = None,
        match_type: str = "EXACT",
    ) -> ExamAppearance:
        resolved_answer = self._resolved_answer(
            question,
            answer_resolution,
        )
        if correct_answer is not None and resolved_answer is not None:
            if correct_answer != resolved_answer:
                raise ValueError(
                    "correct_answer conflicts with the resolved answer key"
                )
        final_answer = correct_answer if correct_answer is not None else resolved_answer

        return ExamAppearance(
            appearance_id=appearance_id,
            question_id=question.question_id,
            exam_id=exam_id,
            conducting_body_id=conducting_body_id,
            year=year,
            exam_date=exam_date,
            shift=shift,
            question_number=question.question_number,
            original_question=question.stem,
            options=tuple((item.key, item.text) for item in question.options),
            correct_answer=final_answer,
            source_url=source_url,
            paper_id=paper_id,
            verification=verification,
            match_type=match_type,
        )

    @staticmethod
    def _resolved_answer(
        question: QuestionCandidate,
        resolution: AnswerResolution | None,
    ) -> str | None:
        if resolution is None:
            return None
        if resolution.question_id != question.question_id:
            raise ValueError("answer resolution does not belong to the question")
        if resolution.document_id != question.document_id:
            raise ValueError("answer resolution does not belong to the document")
        if resolution.status is not AnswerResolutionStatus.RESOLVED:
            return None
        return resolution.selected_option_key
