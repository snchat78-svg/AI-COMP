from ai_comp.domain.questions import QuestionKind
from ai_comp.extraction.question_extractor import QuestionExtractor
from ai_comp.research.metadata import StoredDocumentMetadata
from ai_comp.research.paper import DocumentFormat, FetchedDocument
from ai_comp.research.processing import ExtractionMethod, NormalizedDocument


def make_document(text: str) -> NormalizedDocument:
    document = FetchedDocument(
        document_id="DOC1",
        candidate_id="C1",
        source_url="https://rssb.rajasthan.gov.in/paper.pdf",
        content_type="application/pdf",
        sha256="a" * 64,
        size_bytes=100,
        storage_key="a" * 64,
        format=DocumentFormat.PDF,
    )
    metadata = StoredDocumentMetadata(
        document_id="DOC1",
        candidate_id="C1",
        source_url=document.source_url,
        content_type=document.content_type,
        sha256=document.sha256,
        size_bytes=document.size_bytes,
        storage_key=document.storage_key,
        declared_format=DocumentFormat.PDF,
        detected_format=DocumentFormat.PDF,
    )
    return NormalizedDocument(
        document=document,
        metadata=metadata,
        text=text,
        extraction_method=ExtractionMethod.PDF_TEXT,
    )


def test_extracts_questions_and_options():
    text = """Question 1: भारत की राजधानी क्या है?
A) जयपुर
B) नई दिल्ली
C) भोपाल
D) लखनऊ

2. पानी का रासायनिक सूत्र क्या है?
(a) CO2
(b) H2O
(c) O2
(d) N2
"""
    result = QuestionExtractor().extract(make_document(text))

    assert len(result.questions) == 2
    assert result.questions[0].question_number == 1
    assert result.questions[0].kind is QuestionKind.MCQ
    assert result.questions[0].stem == "भारत की राजधानी क्या है?"
    assert [option.key for option in result.questions[0].options] == ["A", "B", "C", "D"]
    assert result.questions[1].options[1].text == "H2O"


def test_supports_hindi_option_labels():
    result = QuestionExtractor().extract(
        make_document(
            "1) प्रश्न यहाँ है\n"
            "(क) पहला\n"
            "(ख) दूसरा\n"
            "(ग) तीसरा\n"
            "(घ) चौथा"
        )
    )

    assert len(result.questions) == 1
    assert [x.key for x in result.questions[0].options] == ["क", "ख", "ग", "घ"]


def test_answer_key_is_separate_from_question():
    result = QuestionExtractor().extract(
        make_document(
            "1. प्रश्न क्या है?\n"
            "A) एक\n"
            "B) दो\n"
            "C) तीन\n"
            "D) चार\n\n"
            "Answer Key\n"
            "1-B\n"
            "2-C"
        )
    )

    assert len(result.questions) == 1
    assert [(x.question_number, x.answer_key) for x in result.answer_key_entries] == [
        (1, "B"),
        (2, "C"),
    ]


def test_incomplete_question_is_not_promoted_to_candidate():
    result = QuestionExtractor().extract(
        make_document(
            "1. केवल प्रश्न है\n"
            "A) पहला विकल्प\n\n"
            "2. पूरा प्रश्न\n"
            "A) पहला\n"
            "B) दूसरा"
        )
    )

    assert [x.question_number for x in result.questions] == [2]
    assert any("question 1" in warning for warning in result.warnings)


def test_source_text_is_preserved_without_answer_generation():
    result = QuestionExtractor().extract(
        make_document(
            "3. Which is a programming language?\n"
            "A) Python\n"
            "B) Mango\n"
        )
    )

    assert result.questions[0].raw_text == (
        "3. Which is a programming language?\nA) Python\nB) Mango"
    )
    assert not hasattr(result.questions[0], "answer")
