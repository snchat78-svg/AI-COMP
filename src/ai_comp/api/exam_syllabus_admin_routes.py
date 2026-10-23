from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from http import HTTPStatus
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import APIRouter, Request
from pypdf import PdfReader
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.responses import Response

router = APIRouter(prefix="/api/v1/admin/exam-syllabi", tags=["exam-syllabus-review"])


_ALLOWED_OFFICIAL_SYLLABUS_HOSTS = frozenset({
    "rssb.rajasthan.gov.in",
    "www.rssb.rajasthan.gov.in",
    "rsmssb.rajasthan.gov.in",
    "www.rsmssb.rajasthan.gov.in",
})
_MAX_OFFICIAL_PDF_BYTES = 10 * 1024 * 1024
_MAX_OFFICIAL_PDF_PAGES = 500
_OFFICIAL_FETCH_TIMEOUT_SECONDS = 12
_MAX_REDIRECTS = 5


class OfficialSyllabusFetchError(Exception):
    """Safe, stable error code for a failed source retrieval or PDF validation."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class OfficialSyllabusPDF:
    requested_url: str
    final_url: str
    content_type: str
    document_bytes: bytes
    document_sha256: str
    byte_length: int
    page_count: int
    document_title: str


def _validate_official_syllabus_url(url: str) -> str:
    if not isinstance(url, str) or not url or url != url.strip():
        raise OfficialSyllabusFetchError("SOURCE_URL_INVALID")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        raise OfficialSyllabusFetchError("SOURCE_URL_INVALID") from None
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme.lower() != "https"
        or hostname not in _ALLOWED_OFFICIAL_SYLLABUS_HOSTS
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise OfficialSyllabusFetchError("SOURCE_HOST_NOT_ALLOWED")
    return url


class _AllowlistedOfficialRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self._redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self._redirect_count += 1
        if self._redirect_count > _MAX_REDIRECTS:
            raise OfficialSyllabusFetchError("SOURCE_REDIRECT_LIMIT")
        _validate_official_syllabus_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _validate_official_pdf_bytes(
    requested_url: str,
    final_url: str,
    payload: bytes,
    response_content_type: str,
) -> OfficialSyllabusPDF:
    _validate_official_syllabus_url(requested_url)
    _validate_official_syllabus_url(final_url)
    if not payload or len(payload) > _MAX_OFFICIAL_PDF_BYTES:
        raise OfficialSyllabusFetchError("SOURCE_PDF_SIZE_INVALID")
    media_type = (response_content_type or "").split(";", 1)[0].strip().lower()
    if media_type not in {"application/pdf", "application/octet-stream"}:
        raise OfficialSyllabusFetchError("SOURCE_CONTENT_TYPE_INVALID")
    if b"%PDF-" not in payload[:1024] or b"%%EOF" not in payload[-2048:]:
        raise OfficialSyllabusFetchError("SOURCE_PDF_SIGNATURE_INVALID")
    try:
        reader = PdfReader(io.BytesIO(payload), strict=True)
        if reader.is_encrypted:
            raise OfficialSyllabusFetchError("SOURCE_PDF_ENCRYPTED")
        page_count = len(reader.pages)
        if page_count < 1 or page_count > _MAX_OFFICIAL_PDF_PAGES:
            raise OfficialSyllabusFetchError("SOURCE_PDF_PAGE_COUNT_INVALID")
        metadata = reader.metadata
        title = str(metadata.title or "").strip()[:500] if metadata else ""
    except OfficialSyllabusFetchError:
        raise
    except Exception:
        raise OfficialSyllabusFetchError("SOURCE_PDF_UNREADABLE") from None
    return OfficialSyllabusPDF(
        requested_url=requested_url,
        final_url=final_url,
        content_type="application/pdf",
        document_bytes=payload,
        document_sha256=hashlib.sha256(payload).hexdigest(),
        byte_length=len(payload),
        page_count=page_count,
        document_title=title,
    )


def _fetch_official_syllabus_pdf(url: str) -> OfficialSyllabusPDF:
    """Fetch only an allowlisted HTTPS source, with redirects/TLS/size/time controls."""
    requested_url = _validate_official_syllabus_url(url)
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        _AllowlistedOfficialRedirectHandler(),
    )
    request = urllib.request.Request(
        requested_url,
        headers={
            "Accept": "application/pdf, application/octet-stream;q=0.8",
            "Accept-Encoding": "identity",
            "User-Agent": "AI-COMP-Official-Syllabus-Verifier/1.0",
        },
        method="GET",
    )
    try:
        with opener.open(request, timeout=_OFFICIAL_FETCH_TIMEOUT_SECONDS) as response:
            final_url = _validate_official_syllabus_url(response.geturl())
            if response.getcode() != 200:
                raise OfficialSyllabusFetchError("SOURCE_HTTP_STATUS_INVALID")
            encoding = (response.headers.get("Content-Encoding") or "identity").strip().lower()
            if encoding not in {"", "identity"}:
                raise OfficialSyllabusFetchError("SOURCE_CONTENT_ENCODING_INVALID")
            content_type = response.headers.get("Content-Type", "")
            declared_length = response.headers.get("Content-Length")
            if declared_length:
                try:
                    if int(declared_length) < 1 or int(declared_length) > _MAX_OFFICIAL_PDF_BYTES:
                        raise OfficialSyllabusFetchError("SOURCE_PDF_SIZE_INVALID")
                except ValueError:
                    raise OfficialSyllabusFetchError("SOURCE_CONTENT_LENGTH_INVALID") from None
            payload = response.read(_MAX_OFFICIAL_PDF_BYTES + 1)
            if len(payload) > _MAX_OFFICIAL_PDF_BYTES:
                raise OfficialSyllabusFetchError("SOURCE_PDF_SIZE_INVALID")
            if declared_length and int(declared_length) != len(payload):
                raise OfficialSyllabusFetchError("SOURCE_CONTENT_LENGTH_MISMATCH")
            return _validate_official_pdf_bytes(requested_url, final_url, payload, content_type)
    except OfficialSyllabusFetchError:
        raise
    except (TimeoutError, socket.timeout):
        raise OfficialSyllabusFetchError("SOURCE_FETCH_TIMEOUT") from None
    except urllib.error.HTTPError as exc:
        raise OfficialSyllabusFetchError("SOURCE_HTTP_ERROR") from None
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise OfficialSyllabusFetchError("SOURCE_FETCH_TIMEOUT") from None
        raise OfficialSyllabusFetchError("SOURCE_FETCH_FAILED") from None
    except Exception:
        raise OfficialSyllabusFetchError("SOURCE_FETCH_FAILED") from None


def _response(status: HTTPStatus, payload: dict[str, object]) -> Response:
    return Response(
        content=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        status_code=int(status),
        headers={"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


class SyllabusDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    syllabus_id: str = Field(min_length=1, max_length=128)
    exam_id: str = Field(min_length=1, max_length=128)
    source_id: str = Field(min_length=1, max_length=128)
    source_title: str = Field(min_length=1, max_length=500)
    source_url: str = Field(min_length=1, max_length=2000)
    notification_number: str = Field(default="", max_length=200)
    version_label: str = Field(min_length=1, max_length=200)
    source_evidence: str = Field(min_length=1, max_length=4000)
    document_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("syllabus_id", "exam_id", "source_id", "source_title", "version_label")
    @classmethod
    def trimmed_required(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("required fields must be trimmed and non-empty")
        return value

    @field_validator("source_url")
    @classmethod
    def https_only(cls, value: str) -> str:
        parsed = urlsplit(value)
        if value != value.strip() or parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("source_url must be an absolute HTTPS URL without embedded credentials")
        return value


class SyllabusSourceDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    decision: str
    document_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_evidence: str = Field(default="", max_length=4000)
    inventory_complete: bool = False
    inventory_review_note: str = Field(default="", max_length=2000)
    review_note: str = Field(min_length=1, max_length=2000)

    @field_validator("decision")
    @classmethod
    def allowed_decision(cls, value: str) -> str:
        if value not in {"VERIFIED", "REJECTED", "REVIEW_PENDING"}:
            raise ValueError("decision must be VERIFIED, REJECTED, or REVIEW_PENDING")
        return value

    @field_validator("review_note")
    @classmethod
    def review_note_trimmed(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("review_note must be trimmed and non-empty")
        return value

    @model_validator(mode="after")
    def verified_needs_full_evidence(self):
        if self.decision == "VERIFIED" and (
            not self.document_sha256
            or not self.source_evidence.strip()
            or not self.inventory_complete
            or not self.inventory_review_note.strip()
        ):
            raise ValueError("VERIFIED requires document SHA-256, source evidence, and a reviewed complete inventory")
        return self


class ConceptMappingReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    concept_id: str = Field(min_length=1, max_length=128)
    decision: str
    official_unit: str = Field(default="", max_length=1000)
    source_locator: str = Field(default="", max_length=500)
    source_evidence: str = Field(default="", max_length=4000)
    review_note: str = Field(min_length=1, max_length=2000)

    @field_validator("concept_id", "review_note")
    @classmethod
    def trimmed_required(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("required fields must be trimmed and non-empty")
        return value

    @field_validator("decision")
    @classmethod
    def valid_mapping_decision(cls, value: str) -> str:
        if value not in {"IN_SCOPE", "OUT_OF_SCOPE", "UNMAPPED", "NEEDS_REVIEW"}:
            raise ValueError("unsupported concept applicability decision")
        return value

    @model_validator(mode="after")
    def reviewed_decisions_need_evidence(self):
        if self.decision in {"IN_SCOPE", "OUT_OF_SCOPE"} and (
            not self.official_unit.strip() or not self.source_locator.strip() or not self.source_evidence.strip()
        ):
            raise ValueError("IN_SCOPE and OUT_OF_SCOPE require official unit, source locator, and evidence")
        return self


class SyllabusUnitDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    unit_id: str = Field(min_length=1, max_length=128)
    parent_unit_id: str | None = Field(default=None, min_length=1, max_length=128)
    unit_kind: str
    official_label: str = Field(min_length=1, max_length=1000)
    page_number: int | None = Field(default=None, ge=1, le=10000)
    source_locator: str = Field(min_length=1, max_length=500)
    source_evidence: str = Field(min_length=1, max_length=4000)
    author_note: str = Field(default="Submitted for independent review", min_length=1, max_length=2000)

    @field_validator("unit_id", "official_label", "source_locator", "source_evidence", "author_note")
    @classmethod
    def trimmed_required(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("required fields must be trimmed and non-empty")
        return value

    @field_validator("parent_unit_id")
    @classmethod
    def parent_id_trimmed(cls, value: str | None) -> str | None:
        if value is not None and (not value or value != value.strip()):
            raise ValueError("parent_unit_id must be trimmed and non-empty when supplied")
        return value

    @field_validator("unit_kind")
    @classmethod
    def kind_is_allowed(cls, value: str) -> str:
        if value not in {"UNIT", "TOPIC", "SUBTOPIC"}:
            raise ValueError("unit_kind must be UNIT, TOPIC, or SUBTOPIC")
        return value

    @model_validator(mode="after")
    def hierarchy_is_consistent(self):
        if self.unit_kind == "UNIT" and self.parent_unit_id is not None:
            raise ValueError("top-level UNIT must not have a parent")
        if self.unit_kind in {"TOPIC", "SUBTOPIC"} and self.parent_unit_id is None:
            raise ValueError("TOPIC and SUBTOPIC require a parent_unit_id")
        return self


class SyllabusUnitDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    decision: str
    review_note: str = Field(min_length=1, max_length=2000)

    @field_validator("decision")
    @classmethod
    def decision_is_allowed(cls, value: str) -> str:
        if value not in {"VERIFIED", "REJECTED", "NEEDS_REVIEW"}:
            raise ValueError("decision must be VERIFIED, REJECTED, or NEEDS_REVIEW")
        return value

    @field_validator("review_note")
    @classmethod
    def note_is_trimmed(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("review_note must be trimmed and non-empty")
        return value


def _authorized(request: Request, *, reviewer: bool) -> tuple[str | None, Response | None]:
    author = os.environ.get("AI_COMP_SYLLABUS_ADMIN_TOKEN", "").strip()
    reviewer_token = os.environ.get("AI_COMP_SYLLABUS_REVIEW_TOKEN", "").strip()
    content_author = os.environ.get("AI_COMP_CONTENT_ADMIN_TOKEN", "").strip()
    content_reviewer = os.environ.get("AI_COMP_CONTENT_REVIEW_TOKEN", "").strip()
    if not author or not reviewer_token or hmac.compare_digest(author, reviewer_token):
        return None, _response(HTTPStatus.SERVICE_UNAVAILABLE, {"error": {"code": "SYLLABUS_REVIEW_NOT_CONFIGURED", "message": "Distinct syllabus author and reviewer credentials must be configured server-side."}})
    content_tokens = tuple(token for token in (content_author, content_reviewer) if token)
    if any(hmac.compare_digest(token, content_token) for token in (author, reviewer_token) for content_token in content_tokens):
        return None, _response(HTTPStatus.SERVICE_UNAVAILABLE, {"error": {"code": "SYLLABUS_CREDENTIAL_REUSE", "message": "Syllabus credentials must not reuse one-liner author or reviewer credentials."}})
    expected = reviewer_token if reviewer else author
    header = "X-AI-COMP-Syllabus-Review-Token" if reviewer else "X-AI-COMP-Syllabus-Admin-Token"
    supplied = request.headers.get(header, "")
    if not supplied or not hmac.compare_digest(supplied, expected):
        return None, _response(HTTPStatus.UNAUTHORIZED, {"error": {"code": "SYLLABUS_AUTHENTICATION_REQUIRED", "message": "Authorized syllabus credentials are required."}})
    reviewer_id = os.environ.get("AI_COMP_SYLLABUS_REVIEWER_ID", "").strip()
    author_id = os.environ.get("AI_COMP_SYLLABUS_AUTHOR_ID", "syllabus-author").strip()
    if not reviewer_id or len(reviewer_id) > 128:
        return None, _response(HTTPStatus.SERVICE_UNAVAILABLE, {"error": {"code": "SYLLABUS_REVIEWER_ID_NOT_CONFIGURED", "message": "A server-side syllabus reviewer ID is required."}})
    if not author_id or len(author_id) > 128:
        return None, _response(HTTPStatus.SERVICE_UNAVAILABLE, {"error": {"code": "SYLLABUS_AUTHOR_ID_NOT_CONFIGURED", "message": "A server-side syllabus author ID is required."}})
    if hmac.compare_digest(reviewer_id, author_id):
        return None, _response(HTTPStatus.SERVICE_UNAVAILABLE, {"error": {"code": "SYLLABUS_ACTOR_ID_REUSE", "message": "Syllabus author and reviewer identities must be distinct server-side values."}})
    return (reviewer_id if reviewer else author_id), None


def _connection_or_error(request: Request):
    factory = getattr(request.app.state, "question_bank_connection_factory", None)
    if not callable(factory):
        return None, _response(HTTPStatus.SERVICE_UNAVAILABLE, {"error": {"code": "QUESTION_BANK_NOT_CONFIGURED", "message": "Syllabus storage is not configured for this server."}})
    try:
        return factory(), None
    except Exception:
        return None, _response(HTTPStatus.SERVICE_UNAVAILABLE, {"error": {"code": "SYLLABUS_STORE_UNAVAILABLE", "message": "Syllabus storage could not be opened."}})


@router.post("", status_code=201, name="create_syllabus_source_candidate")
def create_syllabus_source_candidate(payload: SyllabusDraft, request: Request) -> Response:
    """Author a pending syllabus record; this endpoint can never mark a source VERIFIED."""
    actor, error = _authorized(request, reviewer=False)
    if error is not None:
        return error
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            row = connection.execute(
                """INSERT INTO exam_syllabus_documents
                   (syllabus_id, exam_id, source_id, source_title, source_url, notification_number,
                    version_label, source_status, source_evidence, document_sha256, is_current)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'REVIEW_PENDING', %s, %s, TRUE)
                   RETURNING syllabus_id, exam_id, source_status""",
                (payload.syllabus_id, payload.exam_id, payload.source_id, payload.source_title, payload.source_url,
                 payload.notification_number, payload.version_label, payload.source_evidence, payload.document_sha256),
            ).fetchone()
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'SOURCE', %s, 'AUTHOR', %s, 'REVIEW_PENDING', %s, %s::jsonb)""",
                (uuid4().hex, payload.syllabus_id, payload.syllabus_id, actor, "Source candidate submitted for independent review",
                 json.dumps({"source_url": payload.source_url, "source_title": payload.source_title, "document_sha256": payload.document_sha256})),
            )
        if row is None:
            raise RuntimeError("syllabus insert returned no row")
        return _response(HTTPStatus.CREATED, {"syllabus_id": row[0], "exam_id": row[1], "source_status": row[2], "created_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_SOURCE_SAVE_FAILED", "message": "Syllabus candidate was not saved; check IDs and existing source records."}})
    finally:
        connection.close()


@router.post("/{syllabus_id}/fetch-source", name="fetch_official_syllabus_source")
def fetch_official_syllabus_source(syllabus_id: str, request: Request) -> Response:
    """Fetch and persist the actual official PDF bytes; never accepts a caller-supplied URL."""
    actor, error = _authorized(request, reviewer=True)
    if error is not None:
        return error
    if not syllabus_id or syllabus_id != syllabus_id.strip() or len(syllabus_id) > 128:
        return _response(HTTPStatus.BAD_REQUEST, {"error": {"code": "INVALID_SYLLABUS_ID", "message": "syllabus_id must be trimmed and 1-128 characters."}})

    factory = getattr(request.app.state, "question_bank_connection_factory", None)
    if not callable(factory):
        return _response(HTTPStatus.SERVICE_UNAVAILABLE, {"error": {"code": "QUESTION_BANK_NOT_CONFIGURED", "message": "Syllabus storage is not configured for this server."}})

    connection = None
    try:
        connection = factory()
        source = connection.execute(
            "SELECT source_url, source_status FROM exam_syllabus_documents WHERE syllabus_id = %s",
            (syllabus_id,),
        ).fetchone()
        if source is None:
            return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
        if str(source[1]) in {"VERIFIED", "SUPERSEDED"}:
            return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_SOURCE_IMMUTABLE", "message": "Create a new syllabus version to refresh a verified or superseded document."}})
        requested_url = str(source[0])
        connection.close()
        connection = None
        try:
            fetched = _fetch_official_syllabus_pdf(requested_url)
        except OfficialSyllabusFetchError as exc:
            failure_connection = None
            try:
                failure_connection = factory()
                with failure_connection.transaction():
                    failure_connection.execute(
                        """INSERT INTO exam_syllabus_source_fetches
                           (fetch_id, syllabus_id, requested_url, fetch_status, failure_code, fetched_by)
                           VALUES (%s, %s, %s, 'FAILED', %s, %s)""",
                        (uuid4().hex, syllabus_id, requested_url, exc.code, actor),
                    )
                    failure_connection.execute(
                        """INSERT INTO exam_syllabus_review_audit
                           (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                           VALUES (%s, %s, 'SOURCE_FETCH', %s, 'REVIEWER', %s, 'FAILED', %s, %s::jsonb)""",
                        (uuid4().hex, syllabus_id, syllabus_id, actor, "Official source fetch failed safely",
                         json.dumps({"failure_code": exc.code, "requested_url": requested_url})),
                    )
            except Exception:
                pass
            finally:
                if failure_connection is not None:
                    failure_connection.close()
            return _response(HTTPStatus.BAD_GATEWAY, {"error": {"code": exc.code, "message": "The official syllabus PDF could not be safely fetched and validated."}})

        connection = factory()
        with connection.transaction():
            current = connection.execute(
                "SELECT source_url, source_status FROM exam_syllabus_documents WHERE syllabus_id = %s FOR UPDATE",
                (syllabus_id,),
            ).fetchone()
            if current is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
            if str(current[0]) != requested_url or str(current[1]) in {"VERIFIED", "SUPERSEDED"}:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_SOURCE_CHANGED", "message": "Syllabus source changed during fetch; no evidence was saved. Create a new version and retry."}})
            fetch_id = uuid4().hex
            connection.execute(
                """INSERT INTO exam_syllabus_source_fetches
                   (fetch_id, syllabus_id, requested_url, final_url, fetch_status, content_type,
                    byte_length, page_count, document_title, document_sha256, document_bytes, fetched_by)
                   VALUES (%s, %s, %s, %s, 'FETCHED', %s, %s, %s, %s, %s, %s, %s)""",
                (fetch_id, syllabus_id, fetched.requested_url, fetched.final_url, fetched.content_type,
                 fetched.byte_length, fetched.page_count, fetched.document_title,
                 fetched.document_sha256, fetched.document_bytes, actor),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'SOURCE_FETCH', %s, 'REVIEWER', %s, 'FETCHED', %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, fetch_id, actor, "Official PDF fetched with normal TLS validation and stored immutably",
                 json.dumps({"requested_url": fetched.requested_url, "final_url": fetched.final_url,
                             "content_type": fetched.content_type, "byte_length": fetched.byte_length,
                             "page_count": fetched.page_count, "document_title": fetched.document_title,
                             "document_sha256": fetched.document_sha256})),
            )
        return _response(HTTPStatus.CREATED, {
            "syllabus_id": syllabus_id,
            "fetch_id": fetch_id,
            "fetch_status": "FETCHED",
            "requested_url": fetched.requested_url,
            "final_url": fetched.final_url,
            "content_type": fetched.content_type,
            "byte_length": fetched.byte_length,
            "page_count": fetched.page_count,
            "document_title": fetched.document_title,
            "document_sha256": fetched.document_sha256,
            "fetched_by": actor,
        })
    except Exception:
        return _response(HTTPStatus.SERVICE_UNAVAILABLE, {"error": {"code": "SYLLABUS_SOURCE_FETCH_STORE_FAILED", "message": "The source fetch evidence could not be saved."}})
    finally:
        if connection is not None:
            connection.close()


@router.post("/{syllabus_id}/source-review", name="review_syllabus_source")
def review_syllabus_source(syllabus_id: str, payload: SyllabusSourceDecision, request: Request) -> Response:
    actor, error = _authorized(request, reviewer=True)
    if error is not None:
        return error
    if not syllabus_id or syllabus_id != syllabus_id.strip() or len(syllabus_id) > 128:
        return _response(HTTPStatus.BAD_REQUEST, {"error": {"code": "INVALID_SYLLABUS_ID", "message": "syllabus_id must be trimmed and 1-128 characters."}})
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            existing = connection.execute(
                "SELECT syllabus_id FROM exam_syllabus_documents WHERE syllabus_id = %s FOR UPDATE",
                (syllabus_id,),
            ).fetchone()
            if existing is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
            author_row = connection.execute(
                """SELECT actor_id FROM exam_syllabus_review_audit
                   WHERE syllabus_id = %s AND entity_type = 'SOURCE' AND entity_id = %s AND actor_role = 'AUTHOR'
                   ORDER BY created_at DESC LIMIT 1""",
                (syllabus_id, syllabus_id),
            ).fetchone()
            if author_row is None:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_AUTHOR_AUDIT_MISSING", "message": "Source candidate has no author audit record; independently re-author it before review."}})
            if str(author_row[0]) == actor:
                return _response(HTTPStatus.FORBIDDEN, {"error": {"code": "INDEPENDENT_REVIEW_REQUIRED", "message": "The source author cannot review their own syllabus candidate."}})
            fetch_evidence = None
            if payload.decision == "VERIFIED":
                fetch_evidence = connection.execute(
                    """SELECT fetch_id, document_sha256, requested_url, final_url, byte_length,
                              page_count, document_title, fetched_at
                       FROM exam_syllabus_source_fetches
                       WHERE syllabus_id = %s AND fetch_status = 'FETCHED'
                       ORDER BY fetched_at DESC LIMIT 1 FOR SHARE""",
                    (syllabus_id,),
                ).fetchone()
                if fetch_evidence is None:
                    return _response(HTTPStatus.CONFLICT, {"error": {"code": "SOURCE_FETCH_REQUIRED", "message": "The server must fetch and validate the official PDF before a source can be VERIFIED."}})
                fetched_digest = str(fetch_evidence[1]).strip()
                if not payload.document_sha256 or not hmac.compare_digest(fetched_digest, payload.document_sha256):
                    return _response(HTTPStatus.CONFLICT, {"error": {"code": "SOURCE_FETCH_DIGEST_MISMATCH", "message": "The review digest must match the server-computed digest of the stored PDF bytes."}})
            if payload.decision == "VERIFIED" and payload.inventory_complete:
                inventory = connection.execute(
                    """SELECT COUNT(*), COUNT(*) FILTER (WHERE review_status <> 'VERIFIED')
                       FROM exam_syllabus_units WHERE syllabus_id = %s""",
                    (syllabus_id,),
                ).fetchone()
                if inventory is None or int(inventory[0] or 0) == 0 or int(inventory[1] or 0) != 0:
                    return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_INVENTORY_INCOMPLETE", "message": "Every unit, topic and subtopic must have a VERIFIED inventory record before the complete-inventory attestation."}})
            digest_to_persist = str(fetch_evidence[1]).strip() if fetch_evidence is not None else payload.document_sha256
            source_evidence_to_persist = payload.source_evidence
            if fetch_evidence is not None:
                source_evidence_to_persist = (
                    f"{payload.source_evidence}\nServer-fetched evidence: fetch_id={fetch_evidence[0]}; "
                    f"sha256={str(fetch_evidence[1]).strip()}; bytes={fetch_evidence[4]}; "
                    f"pages={fetch_evidence[5]}; title={fetch_evidence[6]}; "
                    f"final_url={fetch_evidence[3]}; fetched_at={fetch_evidence[7]}"
                )
            connection.execute(
                """UPDATE exam_syllabus_documents
                   SET source_status = %s,
                       document_sha256 = CASE WHEN %s = 'VERIFIED' THEN %s ELSE COALESCE(%s, document_sha256) END,
                       source_evidence = CASE WHEN %s <> '' THEN %s ELSE source_evidence END,
                       source_checked_at = CASE WHEN %s = 'REVIEW_PENDING' THEN NULL ELSE NOW() END,
                       source_checked_by = CASE WHEN %s = 'REVIEW_PENDING' THEN NULL ELSE %s END,
                       syllabus_inventory_complete = %s,
                       inventory_reviewed_at = CASE WHEN %s THEN NOW() ELSE NULL END,
                       inventory_reviewed_by = CASE WHEN %s THEN %s ELSE NULL END,
                       inventory_review_note = CASE WHEN %s THEN %s ELSE '' END
                   WHERE syllabus_id = %s""",
                (payload.decision, payload.decision, digest_to_persist, payload.document_sha256,
                 source_evidence_to_persist, source_evidence_to_persist,
                 payload.decision, payload.decision, actor, payload.inventory_complete,
                 payload.inventory_complete, payload.inventory_complete, actor, payload.inventory_complete,
                 payload.inventory_review_note, syllabus_id),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'SOURCE', %s, 'REVIEWER', %s, %s, %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, syllabus_id, actor, payload.decision, payload.review_note,
                 json.dumps({"document_sha256": digest_to_persist, "source_evidence": source_evidence_to_persist,
                             "server_fetch_id": fetch_evidence[0] if fetch_evidence is not None else None,
                             "inventory_complete": payload.inventory_complete, "inventory_review_note": payload.inventory_review_note})),
            )
        return _response(HTTPStatus.OK, {
            "syllabus_id": syllabus_id, "source_status": payload.decision, "reviewed_by": actor,
            "document_sha256": digest_to_persist,
        })
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_SOURCE_REVIEW_FAILED", "message": "Review was not saved; verify the source evidence and database constraints."}})
    finally:
        connection.close()


@router.post("/{syllabus_id}/units", status_code=201, name="create_syllabus_unit_draft")
def create_syllabus_unit_draft(syllabus_id: str, payload: SyllabusUnitDraft, request: Request) -> Response:
    """Create an individual UNIT/TOPIC/SUBTOPIC draft; author cannot self-verify it."""
    actor, error = _authorized(request, reviewer=False)
    if error is not None:
        return error
    if not syllabus_id or syllabus_id != syllabus_id.strip() or len(syllabus_id) > 128:
        return _response(HTTPStatus.BAD_REQUEST, {"error": {"code": "INVALID_SYLLABUS_ID", "message": "syllabus_id must be trimmed and 1-128 characters."}})
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            source = connection.execute(
                "SELECT source_status, syllabus_inventory_complete FROM exam_syllabus_documents WHERE syllabus_id = %s FOR UPDATE",
                (syllabus_id,),
            ).fetchone()
            if source is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
            if str(source[0]) == "VERIFIED" or source[1] is True:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_INVENTORY_LOCKED", "message": "Reopen source review and clear the inventory-complete attestation before changing the inventory."}})
            existing_unit = connection.execute(
                """SELECT review_status FROM exam_syllabus_units
                   WHERE syllabus_id = %s AND unit_id = %s FOR UPDATE""",
                (syllabus_id, payload.unit_id),
            ).fetchone()
            if existing_unit is not None and str(existing_unit[0]) == "VERIFIED":
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_UNIT_ALREADY_VERIFIED", "message": "A verified inventory item cannot be edited until an independent reviewer returns it to NEEDS_REVIEW."}})
            expected_parent_kind = {"TOPIC": "UNIT", "SUBTOPIC": "TOPIC"}.get(payload.unit_kind)
            if expected_parent_kind is None:
                if payload.parent_unit_id is not None:
                    return _response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": {"code": "INVALID_UNIT_HIERARCHY", "message": "UNIT must be a top-level record."}})
            else:
                parent = connection.execute(
                    "SELECT unit_kind FROM exam_syllabus_units WHERE syllabus_id = %s AND unit_id = %s",
                    (syllabus_id, payload.parent_unit_id),
                ).fetchone()
                if parent is None or str(parent[0]) != expected_parent_kind:
                    return _response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": {"code": "INVALID_UNIT_HIERARCHY", "message": f"{payload.unit_kind} must reference an existing {expected_parent_kind} parent in the same syllabus."}})
            connection.execute(
                """INSERT INTO exam_syllabus_units
                   (syllabus_id, unit_id, parent_unit_id, unit_kind, official_label, page_number,
                    source_locator, source_evidence, review_status, created_by)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'NEEDS_REVIEW', %s)
                   ON CONFLICT (syllabus_id, unit_id) DO UPDATE SET
                     parent_unit_id = EXCLUDED.parent_unit_id,
                     unit_kind = EXCLUDED.unit_kind,
                     official_label = EXCLUDED.official_label,
                     page_number = EXCLUDED.page_number,
                     source_locator = EXCLUDED.source_locator,
                     source_evidence = EXCLUDED.source_evidence,
                     review_status = 'NEEDS_REVIEW',
                     created_by = EXCLUDED.created_by,
                     created_at = NOW(),
                     reviewed_at = NULL,
                     reviewed_by = NULL,
                     review_note = ''""",
                (syllabus_id, payload.unit_id, payload.parent_unit_id, payload.unit_kind, payload.official_label,
                 payload.page_number, payload.source_locator, payload.source_evidence, actor),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'SYLLABUS_UNIT', %s, 'AUTHOR', %s, 'NEEDS_REVIEW', %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, payload.unit_id, actor, payload.author_note,
                 json.dumps({"unit_kind": payload.unit_kind, "parent_unit_id": payload.parent_unit_id,
                             "official_label": payload.official_label, "page_number": payload.page_number,
                             "source_locator": payload.source_locator, "source_evidence": payload.source_evidence})),
            )
        return _response(HTTPStatus.CREATED, {"syllabus_id": syllabus_id, "unit_id": payload.unit_id,
                                              "unit_kind": payload.unit_kind, "review_status": "NEEDS_REVIEW",
                                              "created_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_UNIT_SAVE_FAILED", "message": "Syllabus unit was not saved; verify its identifiers, hierarchy and source fields."}})
    finally:
        connection.close()


@router.post("/{syllabus_id}/units/{unit_id}/review", name="review_syllabus_unit")
def review_syllabus_unit(syllabus_id: str, unit_id: str, payload: SyllabusUnitDecision, request: Request) -> Response:
    """Independently review one inventoried syllabus unit, topic or subtopic."""
    actor, error = _authorized(request, reviewer=True)
    if error is not None:
        return error
    if not syllabus_id or syllabus_id != syllabus_id.strip() or len(syllabus_id) > 128 or not unit_id or unit_id != unit_id.strip() or len(unit_id) > 128:
        return _response(HTTPStatus.BAD_REQUEST, {"error": {"code": "INVALID_SYLLABUS_UNIT_ID", "message": "Syllabus and unit IDs must be trimmed and 1-128 characters."}})
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            source = connection.execute(
                "SELECT source_status, syllabus_inventory_complete FROM exam_syllabus_documents WHERE syllabus_id = %s FOR UPDATE",
                (syllabus_id,),
            ).fetchone()
            if source is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
            if str(source[0]) == "VERIFIED" or source[1] is True:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_INVENTORY_LOCKED", "message": "Reopen source review before changing the reviewed inventory."}})
            row = connection.execute(
                """SELECT unit_id, unit_kind, official_label, page_number, source_locator, source_evidence,
                          review_status, created_by
                   FROM exam_syllabus_units
                   WHERE syllabus_id = %s AND unit_id = %s FOR UPDATE""",
                (syllabus_id, unit_id),
            ).fetchone()
            if row is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_UNIT_NOT_FOUND", "message": "Syllabus inventory item was not found."}})
            if str(row[7]) == actor:
                return _response(HTTPStatus.FORBIDDEN, {"error": {"code": "INDEPENDENT_REVIEW_REQUIRED", "message": "The unit author cannot review their own syllabus inventory item."}})
            if str(row[6]) == "VERIFIED" and payload.decision == "VERIFIED":
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_UNIT_ALREADY_VERIFIED", "message": "A verified unit must be sent back to NEEDS_REVIEW or rejected with a reason before another authoring cycle."}})
            connection.execute(
                """UPDATE exam_syllabus_units
                   SET review_status = %s, reviewed_at = NOW(), reviewed_by = %s, review_note = %s
                   WHERE syllabus_id = %s AND unit_id = %s""",
                (payload.decision, actor, payload.review_note, syllabus_id, unit_id),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'SYLLABUS_UNIT', %s, 'REVIEWER', %s, %s, %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, unit_id, actor, payload.decision, payload.review_note,
                 json.dumps({"unit_kind": row[1], "official_label": row[2], "page_number": row[3],
                             "source_locator": row[4], "source_evidence": row[5]})),
            )
        return _response(HTTPStatus.OK, {"syllabus_id": syllabus_id, "unit_id": unit_id,
                                         "review_status": payload.decision, "reviewed_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_UNIT_REVIEW_FAILED", "message": "Syllabus inventory review was not saved; check the record and database constraints."}})
    finally:
        connection.close()


@router.post("/{syllabus_id}/concept-mappings", name="create_syllabus_concept_mapping_draft")
def create_syllabus_concept_mapping_draft(syllabus_id: str, payload: ConceptMappingReview, request: Request) -> Response:
    """Create a mapping proposal in NEEDS_REVIEW state; authors cannot certify it."""
    actor, error = _authorized(request, reviewer=False)
    if error is not None:
        return error
    if not syllabus_id or syllabus_id != syllabus_id.strip() or len(syllabus_id) > 128:
        return _response(HTTPStatus.BAD_REQUEST, {"error": {"code": "INVALID_SYLLABUS_ID", "message": "syllabus_id must be trimmed and 1-128 characters."}})
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            source = connection.execute(
                "SELECT syllabus_id FROM exam_syllabus_documents WHERE syllabus_id = %s FOR UPDATE",
                (syllabus_id,),
            ).fetchone()
            if source is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
            existing_mapping = connection.execute(
                """SELECT applicability_status FROM exam_concept_applicability
                   WHERE syllabus_id = %s AND concept_id = %s FOR UPDATE""",
                (syllabus_id, payload.concept_id),
            ).fetchone()
            if existing_mapping is not None and str(existing_mapping[0]) in {"IN_SCOPE", "OUT_OF_SCOPE"}:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "MAPPING_ALREADY_REVIEWED", "message": "An author cannot downgrade a reviewed mapping; an independent reviewer must return it to NEEDS_REVIEW first."}})
            connection.execute(
                """INSERT INTO exam_concept_applicability
                   (syllabus_id, concept_id, applicability_status, official_unit, source_locator,
                    source_evidence, reviewed_at, reviewed_by, review_note, updated_at)
                   VALUES (%s, %s, 'NEEDS_REVIEW', %s, %s, %s, NULL, NULL, '', NOW())
                   ON CONFLICT (syllabus_id, concept_id) DO UPDATE SET
                     applicability_status = 'NEEDS_REVIEW', official_unit = EXCLUDED.official_unit,
                     source_locator = EXCLUDED.source_locator, source_evidence = EXCLUDED.source_evidence,
                     reviewed_at = NULL, reviewed_by = NULL, review_note = '', updated_at = NOW()""",
                (syllabus_id, payload.concept_id, payload.official_unit, payload.source_locator, payload.source_evidence),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'CONCEPT_MAPPING', %s, 'AUTHOR', %s, 'NEEDS_REVIEW', %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, payload.concept_id, actor, payload.review_note,
                 json.dumps({"proposed_decision": payload.decision, "official_unit": payload.official_unit,
                             "source_locator": payload.source_locator, "source_evidence": payload.source_evidence})),
            )
        return _response(HTTPStatus.CREATED, {"syllabus_id": syllabus_id, "concept_id": payload.concept_id,
                                              "applicability_status": "NEEDS_REVIEW", "created_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_MAPPING_DRAFT_FAILED", "message": "Mapping draft was not saved; verify syllabus/concept IDs."}})
    finally:
        connection.close()


@router.post("/{syllabus_id}/concept-mappings/review", name="review_syllabus_concept_mapping")
def review_syllabus_concept_mapping(syllabus_id: str, payload: ConceptMappingReview, request: Request) -> Response:
    actor, error = _authorized(request, reviewer=True)
    if error is not None:
        return error
    if not syllabus_id or syllabus_id != syllabus_id.strip() or len(syllabus_id) > 128:
        return _response(HTTPStatus.BAD_REQUEST, {"error": {"code": "INVALID_SYLLABUS_ID", "message": "syllabus_id must be trimmed and 1-128 characters."}})
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            source = connection.execute(
                "SELECT source_status FROM exam_syllabus_documents WHERE syllabus_id = %s FOR UPDATE",
                (syllabus_id,),
            ).fetchone()
            if source is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
            if str(source[0]) != "VERIFIED":
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_SOURCE_NOT_VERIFIED", "message": "Concept mappings can be reviewed only after the source and complete inventory are verified."}})
            author_row = connection.execute(
                """SELECT actor_id FROM exam_syllabus_review_audit
                   WHERE syllabus_id = %s AND entity_type = 'CONCEPT_MAPPING'
                     AND entity_id = %s AND actor_role = 'AUTHOR'
                   ORDER BY created_at DESC LIMIT 1""",
                (syllabus_id, payload.concept_id),
            ).fetchone()
            if author_row is None:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "MAPPING_DRAFT_NOT_FOUND", "message": "Create a mapping draft before independent review."}})
            if str(author_row[0]) == actor:
                return _response(HTTPStatus.FORBIDDEN, {"error": {"code": "INDEPENDENT_REVIEW_REQUIRED", "message": "The mapping author cannot review their own concept mapping."}})
            pending = connection.execute(
                """SELECT applicability_status FROM exam_concept_applicability
                   WHERE syllabus_id = %s AND concept_id = %s FOR UPDATE""",
                (syllabus_id, payload.concept_id),
            ).fetchone()
            if pending is None or str(pending[0]) != "NEEDS_REVIEW":
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "MAPPING_NOT_PENDING", "message": "Only an existing NEEDS_REVIEW mapping draft can be reviewed."}})
            connection.execute(
                """UPDATE exam_concept_applicability
                   SET applicability_status = %s, official_unit = %s, source_locator = %s,
                       source_evidence = %s, reviewed_at = NOW(), reviewed_by = %s,
                       review_note = %s, updated_at = NOW()
                   WHERE syllabus_id = %s AND concept_id = %s""",
                (payload.decision, payload.official_unit, payload.source_locator, payload.source_evidence,
                 actor, payload.review_note, syllabus_id, payload.concept_id),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'CONCEPT_MAPPING', %s, 'REVIEWER', %s, %s, %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, payload.concept_id, actor, payload.decision, payload.review_note,
                 json.dumps({"official_unit": payload.official_unit, "source_locator": payload.source_locator,
                             "source_evidence": payload.source_evidence})),
            )
        return _response(HTTPStatus.OK, {"syllabus_id": syllabus_id, "concept_id": payload.concept_id,
                                         "applicability_status": payload.decision, "reviewed_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_MAPPING_REVIEW_FAILED", "message": "Mapping review was not saved; verify concept ID and source evidence."}})
    finally:
        connection.close()
