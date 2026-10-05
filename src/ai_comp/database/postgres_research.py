from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.questions import QuestionExtractionResult
from ai_comp.research.paper import FetchedDocument, PaperCandidate
from ai_comp.research.processing import NormalizedDocument


class PostgresResearchRepository:
    """PostgreSQL persistence for paper discovery and document processing."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save_candidate(self, candidate: PaperCandidate) -> None:
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO paper_candidates (
                        candidate_id,
                        source_id,
                        url,
                        title,
                        format,
                        category_id,
                        discovered_at,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, NULLIF(%s, '')::timestamptz, %s)
                    ON CONFLICT (candidate_id) DO UPDATE SET
                        source_id = EXCLUDED.source_id,
                        url = EXCLUDED.url,
                        title = EXCLUDED.title,
                        format = EXCLUDED.format,
                        category_id = EXCLUDED.category_id,
                        discovered_at = EXCLUDED.discovered_at,
                        status = EXCLUDED.status
                    """,
                    (
                        candidate.candidate_id,
                        candidate.source_id,
                        candidate.url,
                        candidate.title,
                        candidate.format.value,
                        candidate.category_id,
                        candidate.discovered_at,
                        candidate.status.value,
                    ),
                )
        except Exception as exc:
            raise RepositoryError("failed to persist paper candidate") from exc

    def save_document(self, document: FetchedDocument) -> None:
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO documents (
                        document_id,
                        candidate_id,
                        source_url,
                        content_type,
                        sha256,
                        size_bytes,
                        storage_key,
                        declared_format,
                        detected_format
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id) DO UPDATE SET
                        candidate_id = EXCLUDED.candidate_id,
                        source_url = EXCLUDED.source_url,
                        content_type = EXCLUDED.content_type,
                        sha256 = EXCLUDED.sha256,
                        size_bytes = EXCLUDED.size_bytes,
                        storage_key = EXCLUDED.storage_key,
                        declared_format = EXCLUDED.declared_format,
                        detected_format = EXCLUDED.detected_format
                    """,
                    (
                        document.document_id,
                        document.candidate_id,
                        document.source_url,
                        document.content_type,
                        document.sha256,
                        document.size_bytes,
                        document.storage_key,
                        document.format.value,
                        document.format.value,
                    ),
                )
        except Exception as exc:
            raise RepositoryError("failed to persist document") from exc

    def save_normalized_document(self, document: NormalizedDocument) -> None:
        try:
            with self._connection.transaction():
                self.save_document(document.document)
                self._connection.execute(
                    """
                    UPDATE documents
                    SET detected_format = %s
                    WHERE document_id = %s
                    """,
                    (
                        document.metadata.detected_format.value,
                        document.document.document_id,
                    ),
                )
                self._connection.execute(
                    """
                    INSERT INTO normalized_documents (
                        document_id,
                        normalization_version,
                        extraction_method,
                        normalized_text
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (document_id) DO UPDATE SET
                        normalization_version = EXCLUDED.normalization_version,
                        extraction_method = EXCLUDED.extraction_method,
                        normalized_text = EXCLUDED.normalized_text,
                        processed_at = NOW()
                    """,
                    (
                        document.document.document_id,
                        "v1",
                        document.extraction_method.value,
                        document.text,
                    ),
                )
        except Exception as exc:
            raise RepositoryError(
                "failed to persist normalized document"
            ) from exc

    def save_extraction_result(self, result: QuestionExtractionResult) -> None:
        """Convenience transaction for Phase 3 output; repositories stay separable."""
        from ai_comp.database.postgres_answer_key import PostgresAnswerKeyRepository
        from ai_comp.database.postgres_question import PostgresQuestionRepository

        try:
            with self._connection.transaction():
                questions = PostgresQuestionRepository(self._connection)
                answers = PostgresAnswerKeyRepository(self._connection)
                for question in result.questions:
                    questions.save(question)
                answers.save_many(result.document_id, result.answer_key_entries)
        except Exception as exc:
            raise RepositoryError(
                "failed to persist question extraction result"
            ) from exc
