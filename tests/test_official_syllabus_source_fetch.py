from __future__ import annotations

import hashlib
import io
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from ai_comp.api import exam_syllabus_admin_routes as routes
from ai_comp.api.app import create_app


class _Cursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row

    def fetchall(self):
        return []


class _Connection:
    def __init__(self, replies=()):
        self.replies = list(replies)
        self.calls = []
        self.closed = False

    @contextmanager
    def transaction(self):
        yield self

    def execute(self, query, params=()):
        self.calls.append((query, params))
        for fragment, response in self.replies:
            if fragment in query:
                return _Cursor(response)
        return _Cursor(None)

    def close(self):
        self.closed = True


def _client(factory=None):
    app = create_app(learner_identity_provider=lambda _request: "learner-1")
    app.state.question_bank_connection_factory = factory
    return TestClient(app)


def _set_review_secrets(monkeypatch):
    monkeypatch.setenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", "author-secret")
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", "reviewer-secret")
    monkeypatch.setenv("AI_COMP_SYLLABUS_AUTHOR_ID", "syllabus-author")
    monkeypatch.setenv("AI_COMP_SYLLABUS_REVIEWER_ID", "independent-reviewer")
    monkeypatch.delenv("AI_COMP_CONTENT_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("AI_COMP_CONTENT_REVIEW_TOKEN", raising=False)


def _sample_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_official_url_validator_allows_only_https_allowlisted_hosts():
    assert routes._validate_official_syllabus_url(
        "https://rssb.rajasthan.gov.in/storage/syllabus.pdf"
    ) == "https://rssb.rajasthan.gov.in/storage/syllabus.pdf"
    for url in (
        "http://rssb.rajasthan.gov.in/syllabus.pdf",
        "https://evil.example/syllabus.pdf",
        "https://rssb.rajasthan.gov.in:8443/syllabus.pdf",
        "https://rssb.rajasthan.gov.in./syllabus.pdf",
        "https://user:password@rssb.rajasthan.gov.in/syllabus.pdf",
    ):
        with pytest.raises(routes.OfficialSyllabusFetchError):
            routes._validate_official_syllabus_url(url)


def test_redirect_handler_rejects_redirect_to_unapproved_host():
    handler = routes._AllowlistedOfficialRedirectHandler()
    request = routes.urllib.request.Request("https://rssb.rajasthan.gov.in/syllabus.pdf")
    with pytest.raises(routes.OfficialSyllabusFetchError) as exc:
        handler.redirect_request(
            request, None, 302, "Found", {}, "https://evil.example/steal"
        )
    assert exc.value.code == "SOURCE_HOST_NOT_ALLOWED"


def test_pdf_validator_computes_digest_from_actual_validated_bytes():
    pdf_bytes = _sample_pdf()
    checked = routes._validate_official_pdf_bytes(
        "https://rssb.rajasthan.gov.in/syllabus.pdf",
        "https://rssb.rajasthan.gov.in/syllabus.pdf",
        pdf_bytes,
        "application/pdf; charset=binary",
    )
    assert checked.document_bytes == pdf_bytes
    assert checked.document_sha256 == hashlib.sha256(pdf_bytes).hexdigest()
    assert checked.byte_length == len(pdf_bytes)
    assert checked.page_count == 1
    assert checked.content_type == "application/pdf"


class _FakeResponse:
    def __init__(self, payload: bytes, url: str, content_type: str = "application/pdf"):
        self.payload = payload
        self.url = url
        self.position = 0
        self.headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(payload)),
            "Content-Encoding": "identity",
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self):
        return self.url

    def getcode(self):
        return 200

    def read(self, size=-1):
        if size < 0:
            size = len(self.payload)
        chunk = self.payload[self.position:self.position + size]
        self.position += len(chunk)
        return chunk


class _FakeOpener:
    def __init__(self, response):
        self.response = response
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return self.response


def test_official_fetch_uses_tls_opener_and_computes_digest_from_streamed_bytes(monkeypatch):
    pdf_bytes = _sample_pdf()
    url = "https://rssb.rajasthan.gov.in/storage/syllabus.pdf"
    opener = _FakeOpener(_FakeResponse(pdf_bytes, url))
    received_handlers = []
    monkeypatch.setattr(
        routes.urllib.request,
        "build_opener",
        lambda *handlers: (received_handlers.extend(handlers) or opener),
    )

    result = routes._fetch_official_syllabus_pdf(url)

    assert result.document_bytes == pdf_bytes
    assert result.document_sha256 == hashlib.sha256(pdf_bytes).hexdigest()
    assert opener.request.full_url == url
    assert opener.timeout == routes._OFFICIAL_FETCH_TIMEOUT_SECONDS
    assert any(isinstance(h, routes.urllib.request.HTTPSHandler) for h in received_handlers)
    assert any(isinstance(h, routes._AllowlistedOfficialRedirectHandler) for h in received_handlers)


def test_pdf_validator_rejects_html_even_when_returned_from_allowlisted_host():
    with pytest.raises(routes.OfficialSyllabusFetchError) as exc:
        routes._validate_official_pdf_bytes(
            "https://rssb.rajasthan.gov.in/syllabus.pdf",
            "https://rssb.rajasthan.gov.in/syllabus.pdf",
            b"<!doctype html><html></html>",
            "text/html",
        )
    assert exc.value.code == "SOURCE_CONTENT_TYPE_INVALID"


def test_fetch_source_endpoint_uses_database_url_and_stores_immutable_evidence(monkeypatch):
    _set_review_secrets(monkeypatch)
    pdf_bytes = _sample_pdf()
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    fetched = routes.OfficialSyllabusPDF(
        requested_url="https://rssb.rajasthan.gov.in/storage/syllabus.pdf",
        final_url="https://rssb.rajasthan.gov.in/storage/syllabus.pdf",
        content_type="application/pdf",
        document_bytes=pdf_bytes,
        document_sha256=digest,
        byte_length=len(pdf_bytes),
        page_count=1,
        document_title="Synthetic test fixture",
    )
    fetched_urls = []
    monkeypatch.setattr(
        routes,
        "_fetch_official_syllabus_pdf",
        lambda url: (fetched_urls.append(url) or fetched),
    )

    lookup = _Connection([
        ("SELECT source_url, source_status", ("https://rssb.rajasthan.gov.in/storage/syllabus.pdf", "REVIEW_PENDING")),
    ])
    writer = _Connection([
        ("SELECT source_url, source_status", ("https://rssb.rajasthan.gov.in/storage/syllabus.pdf", "REVIEW_PENDING")),
    ])
    connections = iter((lookup, writer))
    app = _client(lambda: next(connections))
    response = app.post(
        "/api/v1/admin/exam-syllabi/test-syllabus/fetch-source",
        headers={"X-AI-COMP-Syllabus-Review-Token": "reviewer-secret"},
        json={"url": "https://evil.example/should-not-be-used"},
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert fetched_urls == [fetched.requested_url]
    assert payload["document_sha256"] == digest
    assert payload["page_count"] == 1
    assert any("INSERT INTO exam_syllabus_source_fetches" in q for q, _ in writer.calls)
    fetch_insert = next((q, p) for q, p in writer.calls if "INSERT INTO exam_syllabus_source_fetches" in q)
    assert fetch_insert[1][2] == fetched.requested_url
    assert fetch_insert[1][9] == pdf_bytes
    assert any("'SOURCE_FETCH'" in q for q, _ in writer.calls)
    assert lookup.closed and writer.closed


def test_fetch_source_endpoint_fails_closed_without_reviewer_credentials(monkeypatch):
    monkeypatch.delenv("AI_COMP_SYLLABUS_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("AI_COMP_SYLLABUS_REVIEW_TOKEN", raising=False)
    response = _client().post("/api/v1/admin/exam-syllabi/test-syllabus/fetch-source")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SYLLABUS_REVIEW_NOT_CONFIGURED"


def test_source_review_cannot_verify_using_only_reviewer_supplied_sha(monkeypatch):
    _set_review_secrets(monkeypatch)
    connection = _Connection([
        ("SELECT syllabus_id FROM exam_syllabus_documents", ("test-syllabus",)),
        ("SELECT actor_id FROM exam_syllabus_review_audit", ("syllabus-author",)),
        # A FAILED fetch is latest; no FETCHED evidence is available.
        ("FROM exam_syllabus_source_fetches", ("failed-fetch", None, "https://rssb.rajasthan.gov.in/syllabus.pdf", None, None, None, "", "2026-10-23T10:00:00Z", "FAILED")),
    ])
    response = _client(lambda: connection).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/source-review",
        headers={"X-AI-COMP-Syllabus-Review-Token": "reviewer-secret"},
        json={
            "decision": "VERIFIED",
            "document_sha256": "a" * 64,
            "source_evidence": "Reviewer supplied a digest, but no valid fetch exists",
            "inventory_complete": True,
            "inventory_review_note": "Test claim only",
            "review_note": "Cannot approve on manual digest alone",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SOURCE_FETCH_REQUIRED"
    assert not any("UPDATE exam_syllabus_documents" in q for q, _ in connection.calls)


def test_fetch_evidence_migration_keeps_successful_pdf_bytes_and_audit_immutable():
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[1]
        / "database"
        / "migrations"
        / "0026_phase6_56_source_fetch_evidence.sql"
    ).read_text(encoding="utf-8")
    assert "document_bytes BYTEA" in migration
    assert "document_sha256 CHAR(64)" in migration
    assert "BEFORE UPDATE OR DELETE" in migration
    assert "BEFORE TRUNCATE" in migration
    assert "SOURCE_FETCH" in migration


def test_fetch_rejects_mismatched_content_length(monkeypatch):
    pdf_bytes = _sample_pdf()
    url = "https://rssb.rajasthan.gov.in/storage/syllabus.pdf"
    response = _FakeResponse(pdf_bytes, url)
    response.headers["Content-Length"] = str(len(pdf_bytes) + 1)
    opener = _FakeOpener(response)
    monkeypatch.setattr(routes.urllib.request, "build_opener", lambda *handlers: opener)

    with pytest.raises(routes.OfficialSyllabusFetchError) as exc:
        routes._fetch_official_syllabus_pdf(url)
    assert exc.value.code == "SOURCE_CONTENT_LENGTH_MISMATCH"


def test_failed_official_fetch_is_persisted_and_audited(monkeypatch):
    _set_review_secrets(monkeypatch)
    url = "https://rssb.rajasthan.gov.in/storage/syllabus.pdf"
    monkeypatch.setattr(
        routes,
        "_fetch_official_syllabus_pdf",
        lambda _url: (_ for _ in ()).throw(routes.OfficialSyllabusFetchError("SOURCE_FETCH_FAILED")),
    )
    lookup = _Connection([
        ("SELECT source_url, source_status", (url, "REVIEW_PENDING")),
    ])
    failure = _Connection([])
    connections = iter((lookup, failure))
    response = _client(lambda: next(connections)).post(
        "/api/v1/admin/exam-syllabi/test-syllabus/fetch-source",
        headers={"X-AI-COMP-Syllabus-Review-Token": "reviewer-secret"},
    )

    assert response.status_code == 502, response.text
    assert response.json()["error"]["code"] == "SOURCE_FETCH_FAILED"
    failed_insert = next((params for query, params in failure.calls if "INSERT INTO exam_syllabus_source_fetches" in query))
    audit_insert = next((params for query, params in failure.calls if "'SOURCE_FETCH'" in query))
    assert failed_insert[0] == audit_insert[2]
    assert failed_insert[3] == "SOURCE_FETCH_FAILED"
    assert lookup.closed and failure.closed
