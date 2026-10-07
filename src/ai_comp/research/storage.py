from hashlib import sha256
from pathlib import Path

from ai_comp.research.paper import FetchedDocument


class DocumentStorage:
    """Content-addressed local document storage."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def path_for(self, document: FetchedDocument) -> Path:
        return self.root / document.sha256

    def exists(self, document: FetchedDocument) -> bool:
        return self.path_for(document).exists()

    def write(self, document: FetchedDocument, content: bytes) -> Path:
        if document.sha256 != sha256(content).hexdigest():
            raise ValueError("content hash does not match document metadata")
        path = self.path_for(document)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(content)
        return path

    def read(self, document: FetchedDocument) -> bytes:
        path = self.path_for(document)
        content = path.read_bytes()
        if sha256(content).hexdigest() != document.sha256:
            raise ValueError("stored content hash does not match document metadata")
        return content
