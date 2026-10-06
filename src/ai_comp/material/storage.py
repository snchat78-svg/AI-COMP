from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from ai_comp.domain.materials import MaterialInput


class MaterialStorage:
    """Immutable content-addressed storage for user-provided study material."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    @staticmethod
    def material_id_for(content: bytes) -> str:
        digest = sha256(content).hexdigest()
        return f"material:{digest[:32]}"

    @staticmethod
    def sha256_for(content: bytes) -> str:
        return sha256(content).hexdigest()

    def path_for(self, content: bytes) -> Path:
        return self.root / self.sha256_for(content)

    def exists(self, content: bytes) -> bool:
        return self.path_for(content).exists()

    def write(self, material: MaterialInput) -> Path:
        digest = self.sha256_for(material.content)
        path = self.root / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(material.content)
        return path

    def read(self, sha256_digest: str) -> bytes:
        if len(sha256_digest) != 64:
            raise ValueError("sha256 must be a SHA-256 hex digest")
        path = self.root / sha256_digest
        content = path.read_bytes()
        if self.sha256_for(content) != sha256_digest:
            raise ValueError("stored material hash does not match requested hash")
        return content
