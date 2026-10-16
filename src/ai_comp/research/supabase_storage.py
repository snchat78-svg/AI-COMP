"""Private, content-addressed Supabase Storage for official exam documents.

Only server-side workers should receive the service-role key. Never expose it to
Flutter clients or log it. The database stores a private object locator and the
SHA-256 of bytes; exam-history verification is a separate stage.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


class ObjectStorageConfigurationError(ValueError):
    """Raised when private object-storage credentials/configuration are absent."""


class ObjectStorageError(RuntimeError):
    """Raised for storage API failure without echoing credentials."""


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    object_key: str
    storage_uri: str
    duplicate: bool


class SupabaseObjectStorage:
    """Upload immutable paper bytes to a private Supabase Storage bucket."""

    def __init__(
        self,
        supabase_url: str,
        service_role_key: str,
        *,
        bucket: str = "ai-comp-papers",
        max_file_bytes: int = 25 * 1024 * 1024,
        timeout_seconds: float = 20.0,
    ) -> None:
        parsed = urlparse(supabase_url.strip())
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ObjectStorageConfigurationError(
                "SUPABASE_URL must be the HTTPS project root URL"
            )
        if not service_role_key.strip():
            raise ObjectStorageConfigurationError(
                "SUPABASE_SERVICE_ROLE_KEY is required"
            )
        if not bucket or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in bucket):
            raise ObjectStorageConfigurationError(
                "bucket must use lowercase letters, digits, and hyphens"
            )
        if max_file_bytes < 1:
            raise ValueError("max_file_bytes must be positive")
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        self._key = service_role_key.strip()
        self.bucket = bucket
        self.max_file_bytes = max_file_bytes
        self.timeout_seconds = timeout_seconds
        self._bucket_ready = False

    def ensure_private_bucket(self) -> None:
        if self._bucket_ready:
            return
        payload = json.dumps(
            {
                "id": self.bucket,
                "name": self.bucket,
                "public": False,
                "file_size_limit": self.max_file_bytes,
                "allowed_mime_types": [
                    "application/pdf",
                    "text/html",
                    "text/plain",
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                ],
            }
        ).encode("utf-8")
        status, body = self._request(
            "POST",
            f"{self.base_url}/storage/v1/bucket",
            body=payload,
            content_type="application/json",
        )
        if status in (200, 201):
            self._bucket_ready = True
            return
        body_lower = body.lower()
        if status == 409 or (
            status == 400 and (
                b"already exists" in body_lower
                or b"bucketalreadyexists" in body_lower
            )
        ):
            # Existing buckets remain private; do not change their access model.
            self._bucket_ready = True
            return
        raise ObjectStorageError(
            f"Could not ensure private storage bucket (HTTP {status})"
        )

    def upload(self, digest: str, payload: bytes, content_type: str) -> StoredObject:
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("digest must be a lowercase SHA-256 hex value")
        actual_digest = sha256(payload).hexdigest()
        if actual_digest != digest:
            raise ValueError("upload bytes do not match the supplied SHA-256")
        if len(payload) > self.max_file_bytes:
            raise ObjectStorageError("paper exceeds configured maximum file size")
        if not content_type:
            content_type = "application/octet-stream"

        self.ensure_private_bucket()
        object_key = f"papers/{digest[:2]}/{digest}"
        encoded_key = "/".join(quote(piece, safe="") for piece in object_key.split("/"))
        status, _body = self._request(
            "POST",
            f"{self.base_url}/storage/v1/object/{quote(self.bucket, safe='')}/{encoded_key}",
            body=payload,
            content_type=content_type,
            additional_headers={"x-upsert": "false"},
        )
        duplicate = False
        if status in (200, 201):
            pass
        elif status == 409:
            # Since the path is content-addressed and the digest was checked,
            # an existing object means the same source bytes were stored before.
            duplicate = True
        else:
            raise ObjectStorageError(
                f"Could not upload paper object (HTTP {status})"
            )

        return StoredObject(
            bucket=self.bucket,
            object_key=object_key,
            storage_uri=f"supabase://{self.bucket}/{object_key}",
            duplicate=duplicate,
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        body: bytes,
        content_type: str,
        additional_headers: dict[str, str] | None = None,
    ) -> tuple[int, bytes]:
        headers = {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": content_type,
            "User-Agent": "AI-COMP/phase2.3",
        }
        headers.update(additional_headers or {})
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return int(response.status), response.read(2048)
        except HTTPError as exc:
            return int(exc.code), exc.read(2048)
        except (URLError, TimeoutError, OSError) as exc:
            # Don't include request headers/URLs that might contain configuration.
            raise ObjectStorageError(
                f"Supabase Storage network request failed ({type(exc).__name__})"
            ) from None


__all__ = [
    "ObjectStorageConfigurationError",
    "ObjectStorageError",
    "StoredObject",
    "SupabaseObjectStorage",
]
