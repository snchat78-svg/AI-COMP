from ai_comp.domain.questions import QuestionExtractionResult
from ai_comp.domain.questions import QuestionKind
from ai_comp.extraction.pipeline import QuestionExtractionPipeline
from ai_comp.research.metadata import StoredDocumentMetadata
from ai_comp.research.paper import DocumentFormat, FetchedDocument
from ai_comp.research.processing import ExtractionMethod, NormalizedDocument


def normalized(text: str) -> NormalizedDocument:
    document = FetchedDocument(
        document_id="DOC1",
        candidate_id="C1",
        source_url="https://example.com/paper.pdf",
        content_type="application/pdf",
        sha256="b" * 64,
        size_bytes=50,
        storage_key="b" * 64,
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


def test_pipeline_consumes_only_normalized_documents():
    batch = QuestionExtractionPipeline().extract(
        (
            normalized(
                "1. What is 2+2?\n"
                "A) 3\n"
                "B) 4\n"
                "C) 5"
            ),
        )
    )

    assert len(batch.documents) == 1
    assert len(batch.results) == 1
    result = batch.results[0]
    assert isinstance(result, QuestionExtractionResult)
    assert result.questions[0].kind is QuestionKind.MCQ
    assert result.questions[0].options[1].text == "4"
