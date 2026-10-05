from ai_comp.database.postgres_research import PostgresResearchRepository
from ai_comp.research.paper import DocumentFormat, FetchedDocument, PaperCandidate
from ai_comp.research.processing import ExtractionMethod, NormalizedDocument
from ai_comp.research.metadata import StoredDocumentMetadata


class Connection:
    def __init__(self):
        self.calls = []

    def transaction(self):
        class Tx:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
        return Tx()

    def execute(self, sql, params=()):
        self.calls.append((sql, params))

        class Result:
            def fetchone(self):
                return None
            def fetchall(self):
                return []
        return Result()


def candidate():
    return PaperCandidate(
        candidate_id="c1",
        source_id="src1",
        url="https://example.gov/paper.pdf",
        title="Paper",
        format=DocumentFormat.PDF,
        discovered_at="2024-01-01T00:00:00+00:00",
    )


def document():
    return FetchedDocument(
        document_id="d1",
        candidate_id="c1",
        source_url="https://example.gov/paper.pdf",
        content_type="application/pdf",
        sha256="a" * 64,
        size_bytes=10,
        storage_key="a" * 64,
        format=DocumentFormat.PDF,
    )


def normalized():
    doc = document()
    return NormalizedDocument(
        document=doc,
        metadata=StoredDocumentMetadata(
            document_id="d1",
            candidate_id="c1",
            source_url=doc.source_url,
            content_type=doc.content_type,
            sha256=doc.sha256,
            size_bytes=doc.size_bytes,
            storage_key=doc.storage_key,
            declared_format=DocumentFormat.PDF,
            detected_format=DocumentFormat.PDF,
        ),
        text="normalized text",
        extraction_method=ExtractionMethod.PDF_TEXT,
    )


def test_research_repository_persists_candidate_document_and_normalized_document():
    conn = Connection()
    repo = PostgresResearchRepository(conn)

    repo.save_candidate(candidate())
    repo.save_document(document())
    repo.save_normalized_document(normalized())

    sql = "
".join(item[0] for item in conn.calls)
    assert "INSERT INTO paper_candidates" in sql
    assert "INSERT INTO documents" in sql
    assert "INSERT INTO normalized_documents" in sql
