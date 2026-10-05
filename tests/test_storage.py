from pathlib import Path

import pytest

from ai_comp.research.paper import DocumentFormat, FetchedDocument
from ai_comp.research.storage import DocumentStorage


def document(content: bytes) -> FetchedDocument:
    from hashlib import sha256
    digest = sha256(content).hexdigest()
    return FetchedDocument("D", "C", "https://example.com/a.pdf", "application/pdf", digest, len(content), digest, DocumentFormat.PDF)


def test_storage_is_content_addressed(tmp_path: Path):
    store = DocumentStorage(tmp_path)
    doc = document(b"abc")
    path = store.write(doc, b"abc")
    assert path == tmp_path / doc.sha256
    assert store.exists(doc)


def test_storage_rejects_wrong_hash(tmp_path: Path):
    store = DocumentStorage(tmp_path)
    doc = document(b"abc")
    with pytest.raises(ValueError):
        store.write(doc, b"other")
