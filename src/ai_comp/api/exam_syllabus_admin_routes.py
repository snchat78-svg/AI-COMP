from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from datetime import date, datetime
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.responses import Response

router = APIRouter(
    prefix="/api/v1/admin/question-bank/exam-syllabus",
    tags=["exam-syllabus-authoring"],
)

_SECURITY_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
}
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _json(status: int, payload: dict[str, object]) -> Response:
    return Response(
        content=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        status_code=status,
        headers=_SECURITY_HEADERS,
    )


def _error(status: int, code: str, message: str) -> Response:
    return _json(status, {"error": {"code": code, "message": message}})


def _authorize_author(request: Request) -> tuple[str | None, Response | None]:
    configured = os.environ.get("AI_COMP_SYLLABUS_ADMIN_TOKEN", "").strip()
    author_id = os.environ.get("AI_COMP_SYLLABUS_AUTHOR_ID", "").strip()
    if not configured or not author_id or len(author_id) > 128:
        return None, _error(
            503,
            "SYLLABUS_AUTHORING_NOT_CONFIGURED",
            "Syllabus authoring requires a server-side credential and author identity.",
        )
    supplied = request.headers.get("X-AI-COMP-Syllabus-Admin-Token", "")
    if not supplied or not hmac.compare_digest(supplied, configured):
        return None, _error(
            401,
            "SYLLABUS_AUTHOR_AUTHENTICATION_REQUIRED",
            "Authorized syllabus-editor credentials are required.",
        )
    return author_id, None


def _authorize_reviewer(request: Request) -> tuple[str | None, Response | None]:
    author_token = os.environ.get("AI_COMP_SYLLABUS_ADMIN_TOKEN", "").strip()
    review_token = os.environ.get("AI_COMP_SYLLABUS_REVIEW_TOKEN", "").strip()
    author_id = os.environ.get("AI_COMP_SYLLABUS_AUTHOR_ID", "").strip()
    reviewer_id = os.environ.get("AI_COMP_SYLLABUS_REVIEWER_ID", "").strip()
    if (
        not author_token
        or not review_token
        or hmac.compare_digest(author_token, review_token)
        or not author_id
        or not reviewer_id
        or author_id == reviewer_id
        or len(author_id) > 128
        or len(reviewer_id) > 128
    ):
        return None, _error(
            503,
            "SYLLABUS_REVIEW_NOT_CONFIGURED",
            "Independent syllabus review requires distinct server-side author and reviewer credentials and identities.",
        )
    supplied = request.headers.get("X-AI-COMP-Syllabus-Review-Token", "")
    if not supplied or not hmac.compare_digest(supplied, review_token):
        return None, _error(
            401,
            "SYLLABUS_REVIEW_AUTHENTICATION_REQUIRED",
            "Authorized syllabus-review credentials are required.",
        )
    return reviewer_id, None


def _connection_factory(request: Request):
    factory = getattr(request.app.state, "question_bank_connection_factory", None)
    if not callable(factory):
        return None, _error(
            503,
            "QUESTION_BANK_NOT_CONFIGURED",
            "The syllabus database is not configured for this server.",
        )
    return factory, None


def _valid_identifier(value: str, max_length: int = 128) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= max_length
        and value == value.strip()
        and all(ch.isalnum() or ch in "-_." for ch in value)
    )


def _source_url_error(source_url: str) -> str | None:
    parsed = urlsplit(source_url)
    try:
        port = parsed.port
    except ValueError:
        return "source_url contains an invalid port"
    if (
        source_url != source_url.strip()
        or parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
    ):
        return "source_url must be an absolute HTTPS URL with a hostname, standard port, and no embedded credentials"
    return None


def _matches_registered_source(source_url: str, source_row: tuple[object, ...]) -> bool:
    base_url, source_type, allowed_paths = source_row[0], source_row[1], source_row[2]
    candidate = urlsplit(source_url)
    registered = urlsplit(str(base_url))
    if (
        registered.scheme.lower() != "https"
        or not registered.hostname
        or candidate.hostname is None
        or candidate.hostname.lower() != registered.hostname.lower()
        or str(source_type) not in {"OFFICIAL_WEBSITE", "OFFICIAL_PAPER"}
    ):
        return False
    paths = allowed_paths
    if isinstance(paths, str):
        try:
            paths = json.loads(paths)
        except ValueError:
            return False
    if paths:
        if not isinstance(paths, (list, tuple)):
            return False
        normalized = [str(path).strip() for path in paths if str(path).strip()]
        if normalized and not any(
            candidate.path == prefix.rstrip("/")
            or candidate.path.startswith(prefix.rstrip("/") + "/")
            or (prefix.endswith("/") and candidate.path.startswith(prefix))
            for prefix in normalized
        ):
            return False
    else:
        prefix = registered.path.rstrip("/")
        if prefix and not (
            candidate.path == prefix or candidate.path.startswith(prefix + "/")
        ):
            return False
    return True


def _record_audit(
    connection,
    *,
    syllabus_id: str,
    actor_role: str,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    decision: str,
    note: str,
    evidence: dict[str, object] | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO exam_syllabus_review_audit (
            audit_id, syllabus_id, actor_role, actor_id, action,
            entity_type, entity_id, decision, audit_note, evidence_json
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            uuid4().hex,
            syllabus_id,
            actor_role,
            actor_id,
            action,
            entity_type,
            entity_id,
            decision,
            note,
            json.dumps(evidence or {}, ensure_ascii=False, sort_keys=True),
        ),
    )


def _lock_editable_syllabus(connection, syllabus_id: str) -> tuple[str | None, Response | None]:
    row = connection.execute(
        """
        SELECT source_status
        FROM exam_syllabus_documents
        WHERE syllabus_id = %s AND is_current = TRUE
        FOR UPDATE
        """,
        (syllabus_id,),
    ).fetchone()
    if row is None:
        return None, _error(404, "SYLLABUS_DOCUMENT_NOT_FOUND", "The current syllabus document was not found.")
    status = str(row[0])
    if status not in {"DISCOVERED", "REVIEW_PENDING"}:
        return None, _error(
            409,
            "SYLLABUS_DOCUMENT_NOT_EDITABLE",
            "A verified, rejected, or superseded syllabus cannot be modified; create a new version instead.",
        )
    return status, None


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SyllabusDocumentSubmission(_StrictModel):
    syllabus_id: str = Field(min_length=1, max_length=128)
    exam_id: str = Field(min_length=1, max_length=128)
    source_id: str = Field(min_length=1, max_length=128)
    source_title: str = Field(min_length=1, max_length=300)
    source_url: str = Field(min_length=10, max_length=2000)
    notification_number: str = Field(default="", max_length=200)
    version_label: str = Field(min_length=1, max_length=120)
    source_evidence: str = Field(min_length=1, max_length=4000)
    document_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    published_on: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None

    @field_validator(
        "syllabus_id", "exam_id", "source_id", "source_title",
        "version_label", "source_evidence",
    )
    @classmethod
    def required_text_is_trimmed(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("required fields must be non-empty and trimmed")
        return value

    @field_validator("document_sha256")
    @classmethod
    def digest_must_be_lowercase_sha256(cls, value: str | None) -> str | None:
        if value is not None and not _SHA256_PATTERN.fullmatch(value):
            raise ValueError("document_sha256 must be 64 lowercase hexadecimal characters")
        return value

    @field_validator("source_url")
    @classmethod
    def source_must_use_valid_https(cls, value: str) -> str:
        issue = _source_url_error(value)
        if issue:
            raise ValueError(issue)
        return value

    @model_validator(mode="after")
    def effective_date_range_is_valid(self):
        if self.effective_to and self.effective_from and self.effective_to < self.effective_from:
            raise ValueError("effective_to must not be before effective_from")
        return self


class SyllabusInventoryUnit(_StrictModel):
    unit_id: str = Field(min_length=1, max_length=128)
    parent_unit_id: str | None = Field(default=None, max_length=128)
    unit_kind: Literal["UNIT", "TOPIC", "SUBTOPIC", "SECTION", "ANNEX"]
    official_label: str = Field(min_length=1, max_length=500)
    source_locator: str = Field(min_length=1, max_length=500)
    source_evidence: str = Field(min_length=1, max_length=4000)
    order_index: int = Field(ge=0, le=100000)

    @field_validator("unit_id", "official_label", "source_locator", "source_evidence")
    @classmethod
    def text_is_trimmed(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("text fields must be non-empty and trimmed")
        return value

    @field_validator("parent_unit_id")
    @classmethod
    def parent_is_trimmed(cls, value: str | None) -> str | None:
        if value is not None and (not value.strip() or value != value.strip()):
            raise ValueError("parent_unit_id must be non-empty and trimmed")
        return value


class SubmitInventoryPayload(_StrictModel):
    units: list[SyllabusInventoryUnit] = Field(min_length=1, max_length=2000)
    submission_note: str = Field(min_length=1, max_length=2000)

    @field_validator("submission_note")
    @classmethod
    def note_is_trimmed(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("submission_note must not be blank")
        return value


class ConceptApplicabilityDraft(_StrictModel):
    concept_id: str = Field(min_length=1, max_length=128)
    proposed_status: Literal["IN_SCOPE", "OUT_OF_SCOPE"]
    official_unit: str = Field(min_length=1, max_length=500)
    source_locator: str = Field(min_length=1, max_length=500)
    source_evidence: str = Field(min_length=1, max_length=4000)

    @field_validator("concept_id", "official_unit", "source_locator", "source_evidence")
    @classmethod
    def evidence_fields_are_trimmed(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("mapping fields must be non-empty and trimmed")
        return value


class SubmitApplicabilityPayload(_StrictModel):
    mappings: list[ConceptApplicabilityDraft] = Field(min_length=1, max_length=5000)
    submission_note: str = Field(min_length=1, max_length=2000)


class UnitConceptMappingDraft(_StrictModel):
    unit_id: str = Field(min_length=1, max_length=128)
    concept_id: str = Field(min_length=1, max_length=128)
    source_locator: str = Field(min_length=1, max_length=500)
    source_evidence: str = Field(min_length=1, max_length=4000)

    @field_validator("unit_id", "concept_id", "source_locator", "source_evidence")
    @classmethod
    def mapping_fields_are_trimmed(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("mapping fields must be non-empty and trimmed")
        return value


class SubmitUnitConceptMappingsPayload(_StrictModel):
    mappings: list[UnitConceptMappingDraft] = Field(min_length=1, max_length=10000)
    submission_note: str = Field(min_length=1, max_length=2000)


class ReviewNotePayload(_StrictModel):
    decision: Literal["VERIFIED", "REJECTED", "NEEDS_REVIEW"]
    review_note: str = Field(min_length=1, max_length=2000)

    @field_validator("review_note")
    @classmethod
    def note_is_trimmed(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("review_note must be non-empty and trimmed")
        return value


class ReviewApplicabilityPayload(_StrictModel):
    decision: Literal["IN_SCOPE", "OUT_OF_SCOPE", "UNMAPPED", "NEEDS_REVIEW"]
    source_locator: str = Field(default="", max_length=500)
    source_evidence: str = Field(default="", max_length=4000)
    review_note: str = Field(min_length=1, max_length=2000)

    @field_validator("source_locator", "source_evidence", "review_note")
    @classmethod
    def optional_evidence_is_trimmed(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("fields must be trimmed")
        return value

    @model_validator(mode="after")
    def final_scope_decisions_require_evidence(self):
        if self.decision in {"IN_SCOPE", "OUT_OF_SCOPE"}:
            if not self.source_locator.strip() or not self.source_evidence.strip():
                raise ValueError("IN_SCOPE and OUT_OF_SCOPE decisions require source locator and evidence")
        if not self.review_note.strip():
            raise ValueError("review_note must not be blank")
        return self


class ReviewUnitConceptPayload(_StrictModel):
    decision: Literal["VERIFIED", "REJECTED", "NEEDS_REVIEW"]
    source_locator: str = Field(min_length=1, max_length=500)
    source_evidence: str = Field(min_length=1, max_length=4000)
    review_note: str = Field(min_length=1, max_length=2000)

    @field_validator("source_locator", "source_evidence", "review_note")
    @classmethod
    def all_review_text_is_trimmed(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("review evidence and note must be non-empty and trimmed")
        return value


class FinalizeSyllabusPayload(_StrictModel):
    confirmed_document_sha256: str = Field(min_length=64, max_length=64)
    source_evidence: str = Field(min_length=1, max_length=4000)
    source_review_note: str = Field(min_length=20, max_length=3000)
    inventory_review_note: str = Field(min_length=20, max_length=3000)

    @field_validator("confirmed_document_sha256")
    @classmethod
    def digest_must_be_sha256(cls, value: str) -> str:
        if not _SHA256_PATTERN.fullmatch(value):
            raise ValueError("confirmed_document_sha256 must be 64 lowercase hexadecimal characters")
        return value

    @field_validator("source_evidence", "source_review_note", "inventory_review_note")
    @classmethod
    def review_text_must_be_trimmed(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("review evidence and notes must be non-empty and trimmed")
        return value


@router.post("/documents", status_code=201, name="submit_exam_syllabus_document")
def submit_exam_syllabus_document(payload: SyllabusDocumentSubmission, request: Request) -> Response:
    """Create a pending source candidate; author credentials can never mark it VERIFIED."""
    author_id, error = _authorize_author(request)
    if error is not None:
        return error
    factory, error = _connection_factory(request)
    if error is not None:
        return error
    connection = None
    try:
        connection = factory()
        with connection.transaction():
            exam = connection.execute(
                "SELECT exam_id FROM exams WHERE exam_id = %s AND active = TRUE",
                (payload.exam_id,),
            ).fetchone()
            if exam is None:
                return _error(404, "EXAM_NOT_FOUND", "The active exam was not found.")
            source = connection.execute(
                "SELECT base_url, source_type, allowed_paths FROM sources WHERE source_id = %s",
                (payload.source_id,),
            ).fetchone()
            if source is None:
                return _error(404, "OFFICIAL_SOURCE_NOT_FOUND", "Register the source host before submitting its syllabus.")
            if not _matches_registered_source(payload.source_url, source):
                return _error(
                    422,
                    "SYLLABUS_SOURCE_HOST_NOT_ALLOWED",
                    "The URL host/path must match a registered official source with an HTTPS URL.",
                )
            connection.execute(
                """
                INSERT INTO exam_syllabus_documents (
                    syllabus_id, exam_id, source_id, source_title, source_url,
                    notification_number, version_label, source_status,
                    source_evidence, document_sha256, syllabus_inventory_complete,
                    is_current, published_on, effective_from, effective_to
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, 'REVIEW_PENDING',
                    %s, %s, FALSE, TRUE, %s, %s, %s
                )
                """,
                (
                    payload.syllabus_id,
                    payload.exam_id,
                    payload.source_id,
                    payload.source_title,
                    payload.source_url,
                    payload.notification_number,
                    payload.version_label,
                    payload.source_evidence,
                    payload.document_sha256,
                    payload.published_on,
                    payload.effective_from,
                    payload.effective_to,
                ),
            )
            _record_audit(
                connection,
                syllabus_id=payload.syllabus_id,
                actor_role="AUTHOR",
                actor_id=author_id,
                action="SOURCE_SUBMITTED",
                entity_type="SYLLABUS_DOCUMENT",
                entity_id=payload.syllabus_id,
                decision="SUBMITTED",
                note="Source candidate submitted for independent review.",
                evidence={
                    "source_id": payload.source_id,
                    "source_url": payload.source_url,
                    "source_title": payload.source_title,
                    "notification_number": payload.notification_number,
                    "version_label": payload.version_label,
                    "document_sha256_supplied_by_author": payload.document_sha256,
                },
            )
        return _json(201, {
            "syllabus_id": payload.syllabus_id,
            "exam_id": payload.exam_id,
            "source_status": "REVIEW_PENDING",
            "syllabus_inventory_complete": False,
            "message": "Source candidate saved for independent review; it is not learner-ready.",
        })
    except Exception as exc:
        if getattr(exc, "sqlstate", None) == "23505":
            return _error(409, "SYLLABUS_DOCUMENT_CONFLICT", "That syllabus ID, source URL, or current exam version already exists.")
        return _error(503, "SYLLABUS_DOCUMENT_SAVE_FAILED", "The source candidate could not be saved.")
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.post("/documents/{syllabus_id}/inventory", name="submit_exam_syllabus_inventory")
def submit_exam_syllabus_inventory(
    syllabus_id: str,
    payload: SubmitInventoryPayload,
    request: Request,
) -> Response:
    """Submit the entire extracted inventory as pending; the author cannot attest completeness."""
    if not _valid_identifier(syllabus_id):
        return _error(400, "INVALID_SYLLABUS_ID", "syllabus_id format is invalid.")
    author_id, error = _authorize_author(request)
    if error is not None:
        return error
    ids = [unit.unit_id for unit in payload.units]
    if len(ids) != len(set(ids)):
        return _error(422, "DUPLICATE_INVENTORY_UNIT", "Every unit_id must be unique within one inventory submission.")
    prior: set[str] = set()
    for unit in payload.units:
        if unit.parent_unit_id is not None and unit.parent_unit_id not in prior:
            return _error(422, "INVALID_INVENTORY_HIERARCHY", "A parent unit must appear earlier in the submitted inventory.")
        prior.add(unit.unit_id)

    factory, error = _connection_factory(request)
    if error is not None:
        return error
    connection = None
    try:
        connection = factory()
        with connection.transaction():
            _, error = _lock_editable_syllabus(connection, syllabus_id)
            if error is not None:
                return error
            count_row = connection.execute(
                "SELECT COUNT(*) FROM exam_syllabus_inventory_units WHERE syllabus_id = %s",
                (syllabus_id,),
            ).fetchone()
            if count_row is not None and int(count_row[0]) > 0:
                return _error(409, "SYLLABUS_INVENTORY_ALREADY_SUBMITTED", "Inventory is a versioned snapshot; create a new syllabus version to replace it.")
            for unit in payload.units:
                connection.execute(
                    """
                    INSERT INTO exam_syllabus_inventory_units (
                        syllabus_id, unit_id, parent_unit_id, unit_kind,
                        official_label, source_locator, source_evidence,
                        order_index, review_status, authored_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'NEEDS_REVIEW', %s)
                    """,
                    (
                        syllabus_id, unit.unit_id, unit.parent_unit_id, unit.unit_kind,
                        unit.official_label, unit.source_locator, unit.source_evidence,
                        unit.order_index, author_id,
                    ),
                )
            _record_audit(
                connection,
                syllabus_id=syllabus_id,
                actor_role="AUTHOR",
                actor_id=author_id,
                action="INVENTORY_SUBMITTED",
                entity_type="SYLLABUS_INVENTORY",
                entity_id=syllabus_id,
                decision="SUBMITTED",
                note=payload.submission_note,
                evidence={"unit_count": len(payload.units), "unit_ids": ids},
            )
        return _json(201, {
            "syllabus_id": syllabus_id,
            "submitted_unit_count": len(payload.units),
            "review_status": "NEEDS_REVIEW",
            "inventory_complete": False,
        })
    except Exception:
        return _error(503, "SYLLABUS_INVENTORY_SAVE_FAILED", "The submitted inventory could not be saved.")
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.post("/documents/{syllabus_id}/concept-applicability", name="submit_exam_concept_applicability")
def submit_exam_concept_applicability(
    syllabus_id: str,
    payload: SubmitApplicabilityPayload,
    request: Request,
) -> Response:
    """Submit scope proposals; every proposal remains NEEDS_REVIEW until reviewer action."""
    if not _valid_identifier(syllabus_id):
        return _error(400, "INVALID_SYLLABUS_ID", "syllabus_id format is invalid.")
    author_id, error = _authorize_author(request)
    if error is not None:
        return error
    concepts = [item.concept_id for item in payload.mappings]
    if len(concepts) != len(set(concepts)):
        return _error(422, "DUPLICATE_CONCEPT_MAPPING", "Each concept_id must appear once in a complete applicability submission.")
    factory, error = _connection_factory(request)
    if error is not None:
        return error
    connection = None
    try:
        connection = factory()
        with connection.transaction():
            _, error = _lock_editable_syllabus(connection, syllabus_id)
            if error is not None:
                return error
            count_row = connection.execute(
                "SELECT COUNT(*) FROM exam_concept_applicability WHERE syllabus_id = %s",
                (syllabus_id,),
            ).fetchone()
            if count_row is not None and int(count_row[0]) > 0:
                return _error(409, "SYLLABUS_APPLICABILITY_ALREADY_SUBMITTED", "Applicability is a versioned snapshot; use a new syllabus version to replace it.")
            for item in payload.mappings:
                connection.execute(
                    """
                    INSERT INTO exam_concept_applicability (
                        syllabus_id, concept_id, applicability_status, proposed_status,
                        official_unit, source_locator, source_evidence, authored_by
                    ) VALUES (%s, %s, 'NEEDS_REVIEW', %s, %s, %s, %s, %s)
                    """,
                    (
                        syllabus_id, item.concept_id, item.proposed_status, item.official_unit,
                        item.source_locator, item.source_evidence, author_id,
                    ),
                )
            _record_audit(
                connection,
                syllabus_id=syllabus_id,
                actor_role="AUTHOR",
                actor_id=author_id,
                action="CONCEPT_APPLICABILITY_SUBMITTED",
                entity_type="CONCEPT_APPLICABILITY",
                entity_id=syllabus_id,
                decision="SUBMITTED",
                note=payload.submission_note,
                evidence={
                    "concept_count": len(payload.mappings),
                    "proposed_in_scope": sum(x.proposed_status == "IN_SCOPE" for x in payload.mappings),
                    "proposed_out_of_scope": sum(x.proposed_status == "OUT_OF_SCOPE" for x in payload.mappings),
                },
            )
        return _json(201, {
            "syllabus_id": syllabus_id,
            "submitted_concept_count": len(payload.mappings),
            "review_status": "NEEDS_REVIEW",
        })
    except Exception:
        return _error(503, "SYLLABUS_APPLICABILITY_SAVE_FAILED", "The concept applicability proposals could not be saved.")
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.post("/documents/{syllabus_id}/unit-concept-mappings", name="submit_exam_unit_concept_mappings")
def submit_exam_unit_concept_mappings(
    syllabus_id: str,
    payload: SubmitUnitConceptMappingsPayload,
    request: Request,
) -> Response:
    """Submit source-located unit-to-concept links; all links start pending."""
    if not _valid_identifier(syllabus_id):
        return _error(400, "INVALID_SYLLABUS_ID", "syllabus_id format is invalid.")
    author_id, error = _authorize_author(request)
    if error is not None:
        return error
    keys = [(x.unit_id, x.concept_id) for x in payload.mappings]
    if len(keys) != len(set(keys)):
        return _error(422, "DUPLICATE_UNIT_CONCEPT_MAPPING", "Each unit/concept pair must appear only once.")
    factory, error = _connection_factory(request)
    if error is not None:
        return error
    connection = None
    try:
        connection = factory()
        with connection.transaction():
            _, error = _lock_editable_syllabus(connection, syllabus_id)
            if error is not None:
                return error
            count_row = connection.execute(
                "SELECT COUNT(*) FROM exam_syllabus_unit_concepts WHERE syllabus_id = %s",
                (syllabus_id,),
            ).fetchone()
            if count_row is not None and int(count_row[0]) > 0:
                return _error(409, "UNIT_CONCEPT_MAPPINGS_ALREADY_SUBMITTED", "Unit-to-concept mappings are a versioned snapshot; use a new syllabus version to replace them.")
            for item in payload.mappings:
                connection.execute(
                    """
                    INSERT INTO exam_syllabus_unit_concepts (
                        syllabus_id, unit_id, concept_id, source_locator,
                        source_evidence, review_status, authored_by
                    ) VALUES (%s, %s, %s, %s, %s, 'NEEDS_REVIEW', %s)
                    """,
                    (
                        syllabus_id, item.unit_id, item.concept_id, item.source_locator,
                        item.source_evidence, author_id,
                    ),
                )
            _record_audit(
                connection,
                syllabus_id=syllabus_id,
                actor_role="AUTHOR",
                actor_id=author_id,
                action="UNIT_CONCEPT_MAPPINGS_SUBMITTED",
                entity_type="UNIT_CONCEPT_MAPPING",
                entity_id=syllabus_id,
                decision="SUBMITTED",
                note=payload.submission_note,
                evidence={"mapping_count": len(payload.mappings), "mapping_pairs": keys},
            )
        return _json(201, {
            "syllabus_id": syllabus_id,
            "submitted_mapping_count": len(payload.mappings),
            "review_status": "NEEDS_REVIEW",
        })
    except Exception:
        return _error(503, "UNIT_CONCEPT_MAPPING_SAVE_FAILED", "The unit-to-concept mappings could not be saved.")
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.get("/documents/{syllabus_id}/review-package", name="get_exam_syllabus_review_package")
def get_exam_syllabus_review_package(syllabus_id: str, request: Request) -> Response:
    """Let an authenticated reviewer inspect the entire pending evidence bundle."""
    if not _valid_identifier(syllabus_id):
        return _error(400, "INVALID_SYLLABUS_ID", "syllabus_id format is invalid.")
    _, error = _authorize_reviewer(request)
    if error is not None:
        return error
    factory, error = _connection_factory(request)
    if error is not None:
        return error
    connection = None
    try:
        connection = factory()
        doc = connection.execute(
            """
            SELECT syllabus_id, exam_id, source_id, source_title, source_url,
                   notification_number, version_label, source_status, source_evidence,
                   document_sha256, syllabus_inventory_complete
            FROM exam_syllabus_documents
            WHERE syllabus_id = %s AND is_current = TRUE
            """,
            (syllabus_id,),
        ).fetchone()
        if doc is None:
            return _error(404, "SYLLABUS_DOCUMENT_NOT_FOUND", "The current syllabus document was not found.")
        units = connection.execute(
            """
            SELECT unit_id, parent_unit_id, unit_kind, official_label, source_locator,
                   source_evidence, order_index, review_status, reviewed_by, review_note
            FROM exam_syllabus_inventory_units
            WHERE syllabus_id = %s
            ORDER BY order_index, unit_id
            """,
            (syllabus_id,),
        ).fetchall()
        applicability = connection.execute(
            """
            SELECT concept_id, proposed_status, applicability_status, official_unit,
                   source_locator, source_evidence, reviewed_by, review_note
            FROM exam_concept_applicability
            WHERE syllabus_id = %s
            ORDER BY concept_id
            """,
            (syllabus_id,),
        ).fetchall()
        links = connection.execute(
            """
            SELECT unit_id, concept_id, source_locator, source_evidence,
                   review_status, reviewed_by, review_note
            FROM exam_syllabus_unit_concepts
            WHERE syllabus_id = %s
            ORDER BY unit_id, concept_id
            """,
            (syllabus_id,),
        ).fetchall()
        return _json(200, {
            "document": {
                "syllabus_id": str(doc[0]), "exam_id": str(doc[1]), "source_id": str(doc[2]),
                "source_title": str(doc[3]), "source_url": str(doc[4]),
                "notification_number": str(doc[5] or ""), "version_label": str(doc[6]),
                "source_status": str(doc[7]), "source_evidence": str(doc[8] or ""),
                "document_sha256": None if doc[9] is None else str(doc[9]).strip(),
                "syllabus_inventory_complete": bool(doc[10]),
            },
            "inventory_units": [{
                "unit_id": str(r[0]), "parent_unit_id": None if r[1] is None else str(r[1]),
                "unit_kind": str(r[2]), "official_label": str(r[3]), "source_locator": str(r[4]),
                "source_evidence": str(r[5]), "order_index": int(r[6]), "review_status": str(r[7]),
                "reviewed_by": None if r[8] is None else str(r[8]), "review_note": str(r[9] or ""),
            } for r in units],
            "concept_applicability": [{
                "concept_id": str(r[0]), "proposed_status": None if r[1] is None else str(r[1]),
                "applicability_status": str(r[2]), "official_unit": str(r[3] or ""),
                "source_locator": str(r[4] or ""), "source_evidence": str(r[5] or ""),
                "reviewed_by": None if r[6] is None else str(r[6]), "review_note": str(r[7] or ""),
            } for r in applicability],
            "unit_concept_mappings": [{
                "unit_id": str(r[0]), "concept_id": str(r[1]), "source_locator": str(r[2]),
                "source_evidence": str(r[3]), "review_status": str(r[4]),
                "reviewed_by": None if r[5] is None else str(r[5]), "review_note": str(r[6] or ""),
            } for r in links],
        })
    except Exception:
        return _error(503, "SYLLABUS_REVIEW_PACKAGE_UNAVAILABLE", "The syllabus review package could not be loaded.")
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.post("/documents/{syllabus_id}/inventory-units/{unit_id}/review", name="review_exam_syllabus_inventory_unit")
def review_exam_syllabus_inventory_unit(
    syllabus_id: str,
    unit_id: str,
    payload: ReviewNotePayload,
    request: Request,
) -> Response:
    if not _valid_identifier(syllabus_id) or not _valid_identifier(unit_id):
        return _error(400, "INVALID_INVENTORY_UNIT_ID", "Syllabus and unit identifiers must be trimmed and valid.")
    reviewer_id, error = _authorize_reviewer(request)
    if error is not None:
        return error
    factory, error = _connection_factory(request)
    if error is not None:
        return error
    connection = None
    try:
        connection = factory()
        with connection.transaction():
            current = connection.execute(
                """
                SELECT source_locator, source_evidence
                FROM exam_syllabus_inventory_units
                WHERE syllabus_id = %s AND unit_id = %s
                FOR UPDATE
                """,
                (syllabus_id, unit_id),
            ).fetchone()
            if current is None:
                return _error(404, "SYLLABUS_INVENTORY_UNIT_NOT_FOUND", "The inventory unit was not found.")
            connection.execute(
                """
                UPDATE exam_syllabus_inventory_units
                SET review_status = %s, reviewed_at = NOW(), reviewed_by = %s,
                    review_note = %s, updated_at = NOW()
                WHERE syllabus_id = %s AND unit_id = %s
                """,
                (payload.decision, reviewer_id, payload.review_note, syllabus_id, unit_id),
            )
            _record_audit(
                connection, syllabus_id=syllabus_id, actor_role="REVIEWER",
                actor_id=reviewer_id, action="INVENTORY_UNIT_REVIEWED",
                entity_type="INVENTORY_UNIT", entity_id=unit_id, decision=payload.decision,
                note=payload.review_note,
                evidence={"source_locator": str(current[0]), "source_evidence": str(current[1])},
            )
        return _json(200, {
            "syllabus_id": syllabus_id, "unit_id": unit_id,
            "review_status": payload.decision, "reviewed_by": reviewer_id,
        })
    except Exception:
        return _error(503, "SYLLABUS_INVENTORY_REVIEW_FAILED", "The inventory unit review could not be saved.")
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.post("/documents/{syllabus_id}/concepts/{concept_id}/review", name="review_exam_concept_applicability")
def review_exam_concept_applicability(
    syllabus_id: str,
    concept_id: str,
    payload: ReviewApplicabilityPayload,
    request: Request,
) -> Response:
    if not _valid_identifier(syllabus_id) or not _valid_identifier(concept_id):
        return _error(400, "INVALID_CONCEPT_MAPPING_ID", "Syllabus and concept identifiers must be trimmed and valid.")
    reviewer_id, error = _authorize_reviewer(request)
    if error is not None:
        return error
    factory, error = _connection_factory(request)
    if error is not None:
        return error
    connection = None
    try:
        connection = factory()
        with connection.transaction():
            current = connection.execute(
                """
                SELECT proposed_status, source_locator, source_evidence
                FROM exam_concept_applicability
                WHERE syllabus_id = %s AND concept_id = %s
                FOR UPDATE
                """,
                (syllabus_id, concept_id),
            ).fetchone()
            if current is None:
                return _error(404, "CONCEPT_APPLICABILITY_NOT_FOUND", "The concept applicability proposal was not found.")
            locator = payload.source_locator or str(current[1] or "")
            evidence = payload.source_evidence or str(current[2] or "")
            if payload.decision in {"IN_SCOPE", "OUT_OF_SCOPE"} and (
                not locator.strip() or not evidence.strip()
            ):
                return _error(422, "CONCEPT_REVIEW_EVIDENCE_REQUIRED", "Final scope decisions require a precise source locator and evidence.")
            connection.execute(
                """
                UPDATE exam_concept_applicability
                SET applicability_status = %s, source_locator = %s, source_evidence = %s,
                    reviewed_at = NOW(), reviewed_by = %s, review_note = %s, updated_at = NOW()
                WHERE syllabus_id = %s AND concept_id = %s
                """,
                (
                    payload.decision, locator, evidence, reviewer_id, payload.review_note,
                    syllabus_id, concept_id,
                ),
            )
            _record_audit(
                connection, syllabus_id=syllabus_id, actor_role="REVIEWER",
                actor_id=reviewer_id, action="CONCEPT_APPLICABILITY_REVIEWED",
                entity_type="CONCEPT_APPLICABILITY", entity_id=concept_id,
                decision=payload.decision, note=payload.review_note,
                evidence={"source_locator": locator, "source_evidence": evidence,
                          "author_proposal": None if current[0] is None else str(current[0])},
            )
        return _json(200, {
            "syllabus_id": syllabus_id, "concept_id": concept_id,
            "applicability_status": payload.decision, "reviewed_by": reviewer_id,
        })
    except Exception:
        return _error(503, "CONCEPT_APPLICABILITY_REVIEW_FAILED", "The concept applicability review could not be saved.")
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.post(
    "/documents/{syllabus_id}/unit-concept-mappings/{unit_id}/{concept_id}/review",
    name="review_exam_unit_concept_mapping",
)
def review_exam_unit_concept_mapping(
    syllabus_id: str,
    unit_id: str,
    concept_id: str,
    payload: ReviewUnitConceptPayload,
    request: Request,
) -> Response:
    if not all(_valid_identifier(x) for x in (syllabus_id, unit_id, concept_id)):
        return _error(400, "INVALID_UNIT_CONCEPT_MAPPING_ID", "Syllabus, unit and concept identifiers must be trimmed and valid.")
    reviewer_id, error = _authorize_reviewer(request)
    if error is not None:
        return error
    factory, error = _connection_factory(request)
    if error is not None:
        return error
    connection = None
    try:
        connection = factory()
        with connection.transaction():
            current = connection.execute(
                """
                SELECT review_status
                FROM exam_syllabus_unit_concepts
                WHERE syllabus_id = %s AND unit_id = %s AND concept_id = %s
                FOR UPDATE
                """,
                (syllabus_id, unit_id, concept_id),
            ).fetchone()
            if current is None:
                return _error(404, "UNIT_CONCEPT_MAPPING_NOT_FOUND", "The unit-to-concept mapping was not found.")
            connection.execute(
                """
                UPDATE exam_syllabus_unit_concepts
                SET review_status = %s, source_locator = %s, source_evidence = %s,
                    reviewed_at = NOW(), reviewed_by = %s, review_note = %s, updated_at = NOW()
                WHERE syllabus_id = %s AND unit_id = %s AND concept_id = %s
                """,
                (
                    payload.decision, payload.source_locator, payload.source_evidence,
                    reviewer_id, payload.review_note, syllabus_id, unit_id, concept_id,
                ),
            )
            _record_audit(
                connection, syllabus_id=syllabus_id, actor_role="REVIEWER",
                actor_id=reviewer_id, action="UNIT_CONCEPT_MAPPING_REVIEWED",
                entity_type="UNIT_CONCEPT_MAPPING", entity_id=f"{unit_id}:{concept_id}",
                decision=payload.decision, note=payload.review_note,
                evidence={"unit_id": unit_id, "concept_id": concept_id,
                          "source_locator": payload.source_locator, "source_evidence": payload.source_evidence},
            )
        return _json(200, {
            "syllabus_id": syllabus_id, "unit_id": unit_id, "concept_id": concept_id,
            "review_status": payload.decision, "reviewed_by": reviewer_id,
        })
    except Exception:
        return _error(503, "UNIT_CONCEPT_MAPPING_REVIEW_FAILED", "The unit-to-concept mapping review could not be saved.")
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.post("/documents/{syllabus_id}/finalize", name="finalize_exam_syllabus_review")
def finalize_exam_syllabus_review(
    syllabus_id: str,
    payload: FinalizeSyllabusPayload,
    request: Request,
) -> Response:
    """Release a syllabus only after source, every concept, and every official unit are independently reviewed."""
    if not _valid_identifier(syllabus_id):
        return _error(400, "INVALID_SYLLABUS_ID", "syllabus_id format is invalid.")
    reviewer_id, error = _authorize_reviewer(request)
    if error is not None:
        return error
    factory, error = _connection_factory(request)
    if error is not None:
        return error
    connection = None
    try:
        connection = factory()
        with connection.transaction():
            doc = connection.execute(
                """
                SELECT source_status, document_sha256
                FROM exam_syllabus_documents
                WHERE syllabus_id = %s AND is_current = TRUE
                FOR UPDATE
                """,
                (syllabus_id,),
            ).fetchone()
            if doc is None:
                return _error(404, "SYLLABUS_DOCUMENT_NOT_FOUND", "The current syllabus document was not found.")
            if str(doc[0]) == "VERIFIED":
                return _error(409, "SYLLABUS_ALREADY_VERIFIED", "A verified syllabus cannot be finalized a second time.")
            if str(doc[0]) in {"REJECTED", "SUPERSEDED"}:
                return _error(409, "SYLLABUS_NOT_REVIEWABLE", "A rejected or superseded syllabus cannot be finalized.")

            unit_stats = connection.execute(
                """
                SELECT
                    COUNT(*)::INTEGER,
                    COUNT(*) FILTER (
                        WHERE u.review_status <> 'VERIFIED'
                           OR u.reviewed_at IS NULL
                           OR u.reviewed_by IS NULL
                           OR btrim(u.reviewed_by) = ''
                           OR btrim(u.review_note) = ''
                    )::INTEGER,
                    COUNT(*) FILTER (
                        WHERE NOT EXISTS (
                            SELECT 1 FROM exam_syllabus_unit_concepts AS uc
                            WHERE uc.syllabus_id = u.syllabus_id
                              AND uc.unit_id = u.unit_id
                              AND uc.review_status = 'VERIFIED'
                              AND uc.reviewed_at IS NOT NULL
                              AND uc.reviewed_by IS NOT NULL
                              AND btrim(uc.reviewed_by) <> ''
                              AND btrim(uc.source_locator) <> ''
                              AND btrim(uc.source_evidence) <> ''
                              AND btrim(uc.review_note) <> ''
                        )
                    )::INTEGER
                FROM exam_syllabus_inventory_units AS u
                WHERE u.syllabus_id = %s
                """,
                (syllabus_id,),
            ).fetchone()
            scope_stats = connection.execute(
                """
                SELECT
                    COUNT(*)::INTEGER,
                    COUNT(*) FILTER (
                        WHERE a.concept_id IS NULL
                           OR a.applicability_status NOT IN ('IN_SCOPE', 'OUT_OF_SCOPE')
                           OR a.reviewed_at IS NULL
                           OR a.reviewed_by IS NULL
                           OR btrim(a.reviewed_by) = ''
                           OR btrim(a.source_locator) = ''
                           OR btrim(a.source_evidence) = ''
                           OR btrim(a.review_note) = ''
                    )::INTEGER,
                    COUNT(*) FILTER (
                        WHERE a.applicability_status = 'IN_SCOPE'
                          AND NOT EXISTS (
                              SELECT 1 FROM exam_syllabus_unit_concepts AS uc
                              WHERE uc.syllabus_id = %s
                                AND uc.concept_id = c.concept_id
                                AND uc.review_status = 'VERIFIED'
                          )
                    )::INTEGER
                FROM concepts AS c
                LEFT JOIN exam_concept_applicability AS a
                  ON a.syllabus_id = %s AND a.concept_id = c.concept_id
                """,
                (syllabus_id, syllabus_id),
            ).fetchone()
            pending_unit_mappings = connection.execute(
                """
                SELECT COUNT(*)::INTEGER
                FROM exam_syllabus_unit_concepts
                WHERE syllabus_id = %s AND review_status = 'NEEDS_REVIEW'
                """,
                (syllabus_id,),
            ).fetchone()
            unit_count, unreviewed_units, units_without_verified_link = (
                int(unit_stats[0] or 0), int(unit_stats[1] or 0), int(unit_stats[2] or 0)
            )
            concept_count, incomplete_scope, in_scope_without_link = (
                int(scope_stats[0] or 0), int(scope_stats[1] or 0), int(scope_stats[2] or 0)
            )
            pending_links = int(pending_unit_mappings[0] or 0) if pending_unit_mappings else 0
            missing = []
            if unit_count == 0:
                missing.append("complete official unit inventory")
            if unreviewed_units:
                missing.append("all inventory units independently reviewed")
            if units_without_verified_link:
                missing.append("a verified concept mapping for every official unit")
            if concept_count == 0 or incomplete_scope:
                missing.append("a reviewed IN_SCOPE/OUT_OF_SCOPE decision for every canonical concept")
            if in_scope_without_link:
                missing.append("a verified unit mapping for every IN_SCOPE concept")
            if pending_links:
                missing.append("all submitted unit-to-concept mapping proposals reviewed")
            if not payload.source_evidence.strip():
                missing.append("source evidence")
            if missing:
                return _json(409, {
                    "error": {
                        "code": "SYLLABUS_REVIEW_GATES_NOT_MET",
                        "message": "The syllabus remains pending; required independent-review gates are incomplete.",
                        "missing_gates": missing,
                    }
                })
            connection.execute(
                """
                UPDATE exam_syllabus_documents
                SET source_status = 'VERIFIED',
                    document_sha256 = %s,
                    source_evidence = %s,
                    source_checked_at = NOW(),
                    source_checked_by = %s,
                    syllabus_inventory_complete = TRUE,
                    inventory_reviewed_at = NOW(),
                    inventory_reviewed_by = %s,
                    inventory_review_note = %s
                WHERE syllabus_id = %s
                """,
                (
                    payload.confirmed_document_sha256,
                    payload.source_evidence,
                    reviewer_id,
                    reviewer_id,
                    payload.inventory_review_note,
                    syllabus_id,
                ),
            )
            _record_audit(
                connection, syllabus_id=syllabus_id, actor_role="REVIEWER",
                actor_id=reviewer_id, action="SYLLABUS_FINALIZED",
                entity_type="SYLLABUS_INVENTORY", entity_id=syllabus_id,
                decision="VERIFIED", note=payload.source_review_note,
                evidence={
                    "confirmed_document_sha256": payload.confirmed_document_sha256,
                    "previous_document_sha256": None if doc[1] is None else str(doc[1]).strip(),
                    "source_evidence": payload.source_evidence,
                    "inventory_review_note": payload.inventory_review_note,
                    "unit_count": unit_count,
                    "canonical_concept_count": concept_count,
                },
            )
        return _json(200, {
            "syllabus_id": syllabus_id,
            "source_status": "VERIFIED",
            "syllabus_inventory_complete": True,
            "reviewed_by": reviewer_id,
            "unit_count": unit_count,
            "canonical_concept_count": concept_count,
            "selection_ready": True,
        })
    except Exception:
        return _error(503, "SYLLABUS_FINALIZATION_FAILED", "The source and complete syllabus inventory could not be finalized.")
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


__all__ = ["router"]
