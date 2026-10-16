import json
from hashlib import sha256

import pytest

from ai_comp.research.supabase_storage import (
    ObjectStorageConfigurationError,
    ObjectStorageError,
    SupabaseObjectStorage,
)


class FakeSupabaseStorage(SupabaseObjectStorage):
    def __init__(
        self,
        *,
        bucket_status=201,
        object_status=201,
        existing_bucket_public=False,
        max_file_bytes=1024,
    ):
        super().__init__(
            "https://exampleproject.supabase.co",
            "unit-test-secret",
            max_file_bytes=max_file_bytes,
        )
        self.bucket_status = bucket_status
        self.object_status = object_status
        self.existing_bucket_public = existing_bucket_public
        self.calls = []

    def _request(
        self,
        method,
        url,
        *,
        body,
        content_type,
        additional_headers=None,
    ):
        self.calls.append((method, url, body, content_type, additional_headers or {}))
        if url.endswith("/storage/v1/bucket") and method == "POST":
            return self.bucket_status, b""
        if "/storage/v1/bucket/" in url and method == "GET":
            return 200, json.dumps({"public": self.existing_bucket_public}).encode()
        if "/storage/v1/object/" in url and method == "POST":
            if self.object_status == 409:
                return 409, b'{"error":"KeyAlreadyExists"}'
            return self.object_status, b"{}"
        return 500, b""


def test_storage_uploads_content_addressed_object_to_private_bucket():
    payload = b"%PDF-1.7 test paper bytes"
    digest = sha256(payload).hexdigest()
    store = FakeSupabaseStorage()

    result = store.upload(digest, payload, "application/pdf")

    assert result.bucket == "ai-comp-papers"
    assert result.object_key == f"papers/{digest[:2]}/{digest}"
    assert result.storage_uri == f"supabase://ai-comp-papers/{result.object_key}"
    assert result.duplicate is False
    assert store.calls[0][0:2] == (
        "POST",
        "https://exampleproject.supabase.co/storage/v1/bucket",
    )
    assert store.calls[-1][0] == "POST"
    assert store.calls[-1][3] == "application/pdf"
    assert store.calls[-1][4]["x-upsert"] == "false"


def test_existing_private_bucket_is_checked_before_use():
    payload = b"source bytes"
    store = FakeSupabaseStorage(bucket_status=409, existing_bucket_public=False)

    result = store.upload(sha256(payload).hexdigest(), payload, "text/plain")

    assert result.duplicate is False
    assert any(call[0] == "GET" and "/storage/v1/bucket/" in call[1] for call in store.calls)


def test_existing_public_bucket_is_rejected():
    store = FakeSupabaseStorage(bucket_status=409, existing_bucket_public=True)

    with pytest.raises(ObjectStorageError, match="not confirmed private"):
        store.ensure_private_bucket()


def test_existing_object_at_same_sha_is_idempotent():
    payload = b"same source bytes"
    store = FakeSupabaseStorage(object_status=409)

    first = store.upload(sha256(payload).hexdigest(), payload, "text/plain")
    second = store.upload(sha256(payload).hexdigest(), payload, "text/plain")

    assert first.object_key == second.object_key
    assert first.duplicate and second.duplicate


def test_storage_rejects_hash_mismatch_and_oversized_file_before_network():
    store = FakeSupabaseStorage(max_file_bytes=4)

    with pytest.raises(ValueError, match="do not match"):
        store.upload("0" * 64, b"different", "text/plain")
    with pytest.raises(ObjectStorageError, match="maximum file size"):
        store.upload(sha256(b"12345").hexdigest(), b"12345", "text/plain")

    assert store.calls == []


def test_storage_rejects_non_https_project_url():
    with pytest.raises(ObjectStorageConfigurationError, match="HTTPS"):
        SupabaseObjectStorage(
            "http://exampleproject.supabase.co",
            "unit-test-secret",
        )
