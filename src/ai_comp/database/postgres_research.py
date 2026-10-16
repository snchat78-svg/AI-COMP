from dataclasses import dataclass
import json
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.sources import SourcePriority, SourceRecord, SourceType
from ai_comp.research.paper import (
    DiscoveryStatus,
    DocumentFormat,
    FetchedDocument,
    PaperCandidate,
)
from ai_comp.research.metadata import StoredDocumentMetadata
from ai_comp.research.processing import ExtractionMethod, NormalizedDocument




@dataclass(frozen=True)
class PendingPaperCandidate:
    candidate: PaperCandidate
    source: SourceRecord


@dataclass(frozen=True)
class ProcessedPaperCandidate:
    candidate: PaperCandidate
    source: SourceRecord
    document: NormalizedDocument


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


    def list_pending_candidates(
        self,
        *,
        limit: int = 10,
        source_id: str = "all",
        retry_failed: bool = False,
    ) -> tuple[PendingPaperCandidate, ...]:
        """Load bounded official-source candidates that have not been processed."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        status_condition = (
            "pc.status IN ('DISCOVERED', 'FAILED')"
            if retry_failed
            else "pc.status = 'DISCOVERED'"
        )
        source_condition = ""
        params: list[object] = []
        if source_id != "all":
            source_condition = " AND pc.source_id = %s"
            params.append(source_id)
        try:
            rows = self._connection.execute(
                f"""
                SELECT
                    pc.candidate_id, pc.source_id, pc.url, pc.title,
                    pc.format, pc.category_id, pc.discovered_at, pc.status,
                    s.name, s.base_url, s.source_type, s.priority,
                    s.conducting_body_id, s.allowed_paths, s.notes
                FROM paper_candidates pc
                JOIN sources s ON s.source_id = pc.source_id
                WHERE {status_condition}
                  AND s.priority = 'OFFICIAL'
                  {source_condition}
                ORDER BY pc.discovered_at NULLS FIRST, pc.candidate_id
                LIMIT %s
                """,
                tuple(params + [limit]),
            ).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list pending official paper candidates") from exc

        result: list[PendingPaperCandidate] = []
        for row in rows:
            discovered_at = row[6]
            if discovered_at is None:
                timestamp = ""
            elif hasattr(discovered_at, "isoformat"):
                timestamp = discovered_at.isoformat()
            else:
                timestamp = str(discovered_at)
            allowed_paths = row[13]
            if isinstance(allowed_paths, str):
                try:
                    allowed_paths = json.loads(allowed_paths)
                except json.JSONDecodeError:
                    allowed_paths = []
            if not isinstance(allowed_paths, (list, tuple)):
                allowed_paths = []
            candidate = PaperCandidate(
                candidate_id=str(row[0]),
                source_id=str(row[1]),
                url=str(row[2]),
                title=str(row[3]),
                format=DocumentFormat(str(row[4])),
                category_id=None if row[5] is None else str(row[5]),
                discovered_at=timestamp,
                status=DiscoveryStatus(str(row[7])),
            )
            source = SourceRecord(
                source_id=str(row[1]),
                name=str(row[8]),
                base_url=str(row[9]),
                source_type=SourceType(str(row[10])),
                priority=SourcePriority(str(row[11])),
                conducting_body_id=None if row[12] is None else str(row[12]),
                allowed_paths=tuple(str(item) for item in allowed_paths),
                notes=str(row[14] or ""),
            )
            result.append(PendingPaperCandidate(candidate, source))
        return tuple(result)

    def list_processed_candidates(
        self,
        *,
        limit: int = 500,
        source_id: str = "all",
    ) -> tuple[ProcessedPaperCandidate, ...]:
        """Load fetched official candidates with normalized document content."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 5000:
            raise ValueError("limit must be between 1 and 5000")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        source_condition = ""
        params: list[object] = []
        if source_id != "all":
            source_condition = " AND pc.source_id = %s"
            params.append(source_id)
        try:
            rows = self._connection.execute(
                f"""
                SELECT
                    pc.candidate_id, pc.source_id, pc.url, pc.title,
                    pc.format, pc.category_id, pc.discovered_at, pc.status,
                    s.name, s.base_url, s.source_type, s.priority,
                    s.conducting_body_id, s.allowed_paths, s.notes,
                    d.document_id, d.source_url, d.content_type, d.sha256,
                    d.size_bytes, d.storage_key, d.declared_format,
                    d.detected_format, nd.normalization_version,
                    nd.extraction_method, nd.normalized_text
                FROM paper_candidates pc
                JOIN sources s ON s.source_id = pc.source_id
                JOIN documents d ON d.candidate_id = pc.candidate_id
                JOIN normalized_documents nd ON nd.document_id = d.document_id
                WHERE pc.status = 'FETCHED'
                  AND s.priority = 'OFFICIAL'
                  {source_condition}
                ORDER BY pc.discovered_at NULLS FIRST, pc.candidate_id
                LIMIT %s
                """,
                tuple(params + [limit]),
            ).fetchall()
        except Exception as exc:
            raise RepositoryError(
                "failed to load processed official paper candidates"
            ) from exc

        result: list[ProcessedPaperCandidate] = []
        for row in rows:
            discovered_at = row[6]
            if discovered_at is None:
                timestamp = ""
            elif hasattr(discovered_at, "isoformat"):
                timestamp = discovered_at.isoformat()
            else:
                timestamp = str(discovered_at)
            allowed_paths = row[13]
            if isinstance(allowed_paths, str):
                try:
                    allowed_paths = json.loads(allowed_paths)
                except json.JSONDecodeError:
                    allowed_paths = []
            if not isinstance(allowed_paths, (list, tuple)):
                allowed_paths = []

            candidate = PaperCandidate(
                candidate_id=str(row[0]),
                source_id=str(row[1]),
                url=str(row[2]),
                title=str(row[3]),
                format=DocumentFormat(str(row[4])),
                category_id=None if row[5] is None else str(row[5]),
                discovered_at=timestamp,
                status=DiscoveryStatus(str(row[7])),
            )
            source = SourceRecord(
                source_id=str(row[1]),
                name=str(row[8]),
                base_url=str(row[9]),
                source_type=SourceType(str(row[10])),
                priority=SourcePriority(str(row[11])),
                conducting_body_id=None if row[12] is None else str(row[12]),
                allowed_paths=tuple(str(item) for item in allowed_paths),
                notes=str(row[14] or ""),
            )
            fetched = FetchedDocument(
                document_id=str(row[15]),
                candidate_id=str(row[0]),
                source_url=str(row[16]),
                content_type=str(row[17] or ""),
                sha256=str(row[18]),
                size_bytes=int(row[19]),
                storage_key=str(row[20]),
                format=DocumentFormat(str(row[22])),
            )
            metadata = StoredDocumentMetadata(
                document_id=fetched.document_id,
                candidate_id=fetched.candidate_id,
                source_url=fetched.source_url,
                content_type=fetched.content_type,
                sha256=fetched.sha256,
                size_bytes=fetched.size_bytes,
                storage_key=fetched.storage_key,
                declared_format=DocumentFormat(str(row[21])),
                detected_format=DocumentFormat(str(row[22])),
            )
            normalized = NormalizedDocument(
                document=fetched,
                metadata=metadata,
                text=str(row[25] or ""),
                extraction_method=ExtractionMethod(str(row[24])),
            )
            result.append(ProcessedPaperCandidate(candidate, source, normalized))
        return tuple(result)

    def has_document_hash(self, digest: str) -> bool:
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("digest must be a lowercase SHA-256 hex value")
        try:
            return self._connection.execute(
                "SELECT 1 FROM documents WHERE sha256 = %s LIMIT 1",
                (digest,),
            ).fetchone() is not None
        except Exception as exc:
            raise RepositoryError("failed to check existing document hash") from exc

    def mark_candidate_status(
        self,
        candidate_id: str,
        status: DiscoveryStatus,
    ) -> None:
        if status not in {
            DiscoveryStatus.DISCOVERED,
            DiscoveryStatus.REJECTED,
            DiscoveryStatus.FETCHED,
            DiscoveryStatus.FAILED,
        }:
            raise ValueError("unsupported candidate status")
        try:
            with self._connection.transaction():
                row = self._connection.execute(
                    """
                    UPDATE paper_candidates
                    SET status = %s
                    WHERE candidate_id = %s
                    RETURNING candidate_id
                    """,
                    (status.value, candidate_id),
                ).fetchone()
                if row is None:
                    raise RepositoryError("paper candidate does not exist")
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to update paper candidate status") from exc

    def save_document(self, document: FetchedDocument) -> None:
        try:
            with self._connection.transaction():
                self._save_document_row(document)
        except Exception as exc:
            raise RepositoryError("failed to persist document") from exc

    def save_normalized_document(self, document: NormalizedDocument) -> None:
        try:
            with self._connection.transaction():
                self._save_document_row(document.document)
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

    def _save_document_row(self, document: FetchedDocument) -> None:
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
                declared_format = EXCLUDED.declared_format
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
                "unknown",
            ),
        )
