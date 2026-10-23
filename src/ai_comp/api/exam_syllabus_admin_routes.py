from __future__ import annotations

import hmac
import json
import os
from http import HTTPStatus
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.responses import Response

router = APIRouter(prefix="/api/v1/admin/exam-syllabi", tags=["exam-syllabus-review"])


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
        if value not in {"VERIFIED", "REJECTED"}:
            raise ValueError("decision must be VERIFIED or REJECTED")
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
            if payload.decision == "VERIFIED" and payload.inventory_complete:
                inventory = connection.execute(
                    """SELECT COUNT(*), COUNT(*) FILTER (WHERE review_status <> 'VERIFIED')
                       FROM exam_syllabus_units WHERE syllabus_id = %s""",
                    (syllabus_id,),
                ).fetchone()
                if inventory is None or int(inventory[0] or 0) == 0 or int(inventory[1] or 0) != 0:
                    return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_INVENTORY_INCOMPLETE", "message": "Every unit, topic and subtopic must have a VERIFIED inventory record before the complete-inventory attestation."}})
            connection.execute(
                """UPDATE exam_syllabus_documents
                   SET source_status = %s, document_sha256 = COALESCE(%s, document_sha256),
                       source_evidence = CASE WHEN %s <> '' THEN %s ELSE source_evidence END,
                       source_checked_at = CASE WHEN %s = 'REVIEW_PENDING' THEN NULL ELSE NOW() END,
                       source_checked_by = CASE WHEN %s = 'REVIEW_PENDING' THEN NULL ELSE %s END,
                       syllabus_inventory_complete = %s,
                       inventory_reviewed_at = CASE WHEN %s THEN NOW() ELSE NULL END,
                       inventory_reviewed_by = CASE WHEN %s THEN %s ELSE NULL END,
                       inventory_review_note = CASE WHEN %s THEN %s ELSE '' END
                   WHERE syllabus_id = %s""",
                (payload.decision, payload.document_sha256, payload.source_evidence, payload.source_evidence,
                 payload.decision, payload.decision, actor, payload.inventory_complete,
                 payload.inventory_complete, payload.inventory_complete, actor, payload.inventory_complete,
                 payload.inventory_review_note, syllabus_id),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'SOURCE', %s, 'REVIEWER', %s, %s, %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, syllabus_id, actor, payload.decision, payload.review_note,
                 json.dumps({"document_sha256": payload.document_sha256, "source_evidence": payload.source_evidence,
                             "inventory_complete": payload.inventory_complete, "inventory_review_note": payload.inventory_review_note})),
            )
        return _response(HTTPStatus.OK, {"syllabus_id": syllabus_id, "source_status": payload.decision, "reviewed_by": actor})
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
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'NEEDS_REVIEW', %s)""",
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
            if str(row[6]) != "NEEDS_REVIEW":
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_UNIT_NOT_PENDING", "message": "Only a NEEDS_REVIEW inventory item can be reviewed."}})
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
