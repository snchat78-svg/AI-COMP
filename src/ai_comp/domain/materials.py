from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MaterialFormat(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    UNKNOWN = "unknown"


class MaterialSource(str, Enum):
    USER_UPLOAD = "USER_UPLOAD"
    USER_NOTE = "USER_NOTE"


@dataclass(frozen=True)
class MaterialInput:
    filename: str
    content_type: str
    content: bytes
    source: MaterialSource = MaterialSource.USER_UPLOAD

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError("filename must not be empty")
        if not self.content:
            raise ValueError("material content must not be empty")
        if not self.content_type.strip():
            raise ValueError("content_type must not be empty")


@dataclass(frozen=True)
class NormalizedMaterial:
    material_id: str
    filename: str
    source: MaterialSource
    format: MaterialFormat
    content_type: str
    sha256: str
    size_bytes: int
    text: str
    extraction_method: str
    storage_key: str
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.material_id.strip():
            raise ValueError("material_id must not be empty")
        if len(self.sha256) != 64:
            raise ValueError("sha256 must be a SHA-256 hex digest")
        if self.size_bytes < 1:
            raise ValueError("size_bytes must be positive")
        if not self.storage_key.strip():
            raise ValueError("storage_key must not be empty")
