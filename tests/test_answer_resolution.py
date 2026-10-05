from ai_comp.domain.questions import AnswerKeyEntry, QuestionCandidate, QuestionKind, QuestionOption
from ai_comp.domain.answers import AnswerKeyResolver, AnswerResolutionMethod, AnswerResolutionStatus


def question():
    return QuestionCandidate(
        question_id="q1",
        document_id="doc1",
        document_sha256="a" * 64,
        question_number=1,
        stem="राजस्थान का उदाहरण?",
        options=(
            QuestionOption("A", "एक"),
            QuestionOption("B", "दो"),
            QuestionOption("C", "तीन"),
        ),
        kind=QuestionKind.MCQ,
        raw_text="1. राजस्थान का उदाहरण?",
        start_line=1,
        end_line=4,
    )


def test_answer_key_direct_option_is_resolved():
    result = AnswerKeyResolver().resolve(question(), AnswerKeyEntry(1, "B", "1-B", 10))
    assert result.status is AnswerResolutionStatus.RESOLVED
    assert result.selected_option_key == "B"
    assert result.method is AnswerResolutionMethod.DIRECT_OPTION_KEY


def test_numeric_answer_key_uses_option_position():
    result = AnswerKeyResolver().resolve(question(), AnswerKeyEntry(1, "2", "1-2", 10))
    assert result.status is AnswerResolutionStatus.RESOLVED
    assert result.selected_option_key == "B"
    assert result.method is AnswerResolutionMethod.POSITIONAL_NUMERIC


def test_hindi_answer_key_uses_option_position():
    result = AnswerKeyResolver().resolve(question(), AnswerKeyEntry(1, "ग", "1-ग", 10))
    assert result.status is AnswerResolutionStatus.RESOLVED
    assert result.selected_option_key == "C"
    assert result.method is AnswerResolutionMethod.POSITIONAL_HINDI


def test_invalid_answer_key_is_not_guessed():
    result = AnswerKeyResolver().resolve(question(), AnswerKeyEntry(1, "Z", "1-Z", 10))
    assert result.status is AnswerResolutionStatus.INVALID_OPTION
    assert result.selected_option_key is None


def test_missing_question_is_not_guessed():
    result = AnswerKeyResolver().resolve(None, AnswerKeyEntry(9, "A", "9-A", 10))
    assert result.status is AnswerResolutionStatus.MISSING_QUESTION
    assert result.selected_option_key is None
