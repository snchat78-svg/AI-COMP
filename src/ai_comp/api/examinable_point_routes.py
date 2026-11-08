from __future__ import annotations

import json
from http import HTTPStatus
from uuid import uuid4

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.responses import Response

from ai_comp.api.exam_syllabus_admin_routes import _authorized, _connection_or_error, _response
from ai_comp.database.postgres_examinable_points import PostgresExaminablePointRepository
from ai_comp.database.repository import RepositoryError

router = APIRouter(prefix="/api/v1/admin/exam-syllabi", tags=["exam-syllabus-review"])

_POINT_TYPES = {
    "FACT", "DEFINITION", "FORMULA", "PROCESS", "COMPARISON",
    "CLASSIFICATION", "LOCATION", "DIAGRAM", "EXCEPTION",
    "NUMERICAL_SKILL", "OTHER",
}
_DIMENSIONS = {
    "PRESENCE", "CORRECTNESS", "ATOMICITY", "RECALL_DEPTH",
    "APPLICATION", "DISCRIMINATION", "LANGUAGE", "PROVENANCE", "DUPLICATION",
}


class ExaminablePointDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    point_id: str = Field(min_length=1, max_length=128)
    unit_id: str = Field(min_length=1, max_length=128)
    point_type: str
    point_statement: str = Field(min_length=1, max_length=2000)
    page_number: int | None = Field(default=None, ge=1, le=10000)
    source_locator: str = Field(min_length=1, max_length=500)
    source_evidence: str = Field(min_length=1, max_length=2000)
    concept_ids: list[str] = Field(default_factory=list, max_length=12)
    mapping_gap_reason: str = Field(default="", max_length=1000)
    author_note: str = Field(default="Submitted for independent review", min_length=1, max_length=2000)

    @field_validator("point_id", "unit_id", "point_statement", "source_locator", "source_evidence", "author_note")
    @classmethod
    def required_trimmed(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("required values must be trimmed and non-empty")
        return value

    @field_validator("point_type")
    @classmethod
    def point_type_allowed(cls, value: str) -> str:
        if value not in _POINT_TYPES:
            raise ValueError("unsupported examinable point type")
        return value

    @field_validator("concept_ids")
    @classmethod
    def concept_ids_unique_trimmed(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value) or any(not item or item != item.strip() for item in value):
            raise ValueError("concept_ids must be unique, trimmed and non-empty")
        return value

    @model_validator(mode="after")
    def requires_mapping_or_gap_reason(self):
        if bool(self.concept_ids) == bool(self.mapping_gap_reason.strip()):
            raise ValueError("provide one or more concept_ids OR a mapping_gap_reason")
        return self


class PointDimensionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    dimension_key: str
    assessment: str
    assessment_reason: str = Field(default="", max_length=1000)

    @field_validator("dimension_key")
    @classmethod
    def dimension_allowed(cls, value: str) -> str:
        if value not in _DIMENSIONS:
            raise ValueError("unsupported coverage dimension")
        return value

    @field_validator("assessment")
    @classmethod
    def assessment_allowed(cls, value: str) -> str:
        if value not in {"APPLICABLE", "NOT_APPLICABLE", "GAP"}:
            raise ValueError("assessment must be APPLICABLE, NOT_APPLICABLE, or GAP")
        return value

    @model_validator(mode="after")
    def reason_for_non_pass(self):
        if self.assessment in {"NOT_APPLICABLE", "GAP"} and not self.assessment_reason.strip():
            raise ValueError("NOT_APPLICABLE and GAP require an assessment_reason")
        if self.dimension_key == "PRESENCE" and self.assessment == "NOT_APPLICABLE":
            raise ValueError("PRESENCE must be APPLICABLE or GAP")
        return self


class ExaminablePointDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    decision: str
    review_note: str = Field(min_length=1, max_length=2000)
    dimensions: list[PointDimensionAssessment] = Field(min_length=9, max_length=9)

    @field_validator("decision")
    @classmethod
    def decision_allowed(cls, value: str) -> str:
        if value not in {"VERIFIED", "REJECTED", "NEEDS_REVIEW"}:
            raise ValueError("decision must be VERIFIED, REJECTED, or NEEDS_REVIEW")
        return value

    @field_validator("review_note")
    @classmethod
    def review_note_trimmed(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("review_note must be trimmed and non-empty")
        return value

    @model_validator(mode="after")
    def all_dimensions_once(self):
        keys = [item.dimension_key for item in self.dimensions]
        if len(set(keys)) != len(_DIMENSIONS) or set(keys) != _DIMENSIONS:
            raise ValueError("all nine coverage dimensions must be assessed exactly once")
        if self.decision == "VERIFIED" and any(item.assessment == "GAP" for item in self.dimensions):
            raise ValueError("a point with an open coverage-dimension GAP cannot be VERIFIED")
        return self


class PointLearningItemDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    one_liner_id: str = Field(min_length=1, max_length=128)
    author_note: str = Field(min_length=1, max_length=2000)

    @field_validator("one_liner_id", "author_note")
    @classmethod
    def values_trimmed(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("values must be trimmed and non-empty")
        return value


class PointLearningItemDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    decision: str
    review_note: str = Field(min_length=1, max_length=2000)

    @field_validator("decision")
    @classmethod
    def decision_allowed(cls, value: str) -> str:
        if value not in {"VERIFIED", "REJECTED", "NEEDS_REVIEW"}:
            raise ValueError("decision must be VERIFIED, REJECTED, or NEEDS_REVIEW")
        return value

    @field_validator("review_note")
    @classmethod
    def note_trimmed(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("review_note must be trimmed and non-empty")
        return value


def _valid_syllabus_for_point_authoring(connection, syllabus_id: str):
    source = connection.execute(
        """SELECT source_status, syllabus_inventory_complete,
                  examinable_points_inventory_complete
           FROM exam_syllabus_documents WHERE syllabus_id = %s FOR UPDATE""",
        (syllabus_id,),
    ).fetchone()
    if source is None:
        return None, _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
    if str(source[0]) != "VERIFIED" or source[1] is not True:
        return None, _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_SOURCE_NOT_READY", "message": "The official source and full UNIT/TOPIC/SUBTOPIC inventory must be independently verified first."}})
    if source[2] is True:
        return None, _response(HTTPStatus.CONFLICT, {"error": {"code": "EXAMINABLE_POINT_INVENTORY_LOCKED", "message": "Reopen the point inventory through independent review before changing it."}})
    return source, None



class PointInventoryAttestation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    review_note: str = Field(min_length=1, max_length=2000)

    @field_validator("review_note")
    @classmethod
    def note_trimmed(cls, value: str) -> str:
        if not value or value != value.strip():
            raise ValueError("review_note must be trimmed and non-empty")
        return value


@router.post("/{syllabus_id}/examinable-points", status_code=201, name="create_examinable_point_draft")
def create_examinable_point_draft(
    syllabus_id: str, payload: ExaminablePointDraft, request: Request
) -> Response:
    """Author a pending point; author identity is server-derived and cannot self-verify."""
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
            _, error = _valid_syllabus_for_point_authoring(connection, syllabus_id)
            if error is not None:
                return error
            unit = connection.execute(
                """SELECT unit_kind, review_status FROM exam_syllabus_units
                   WHERE syllabus_id = %s AND unit_id = %s""",
                (syllabus_id, payload.unit_id),
            ).fetchone()
            if unit is None or str(unit[1]) != "VERIFIED":
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_UNIT_NOT_VERIFIED", "message": "The referenced UNIT/TOPIC/SUBTOPIC must be independently VERIFIED first."}})
            existing = connection.execute(
                """SELECT review_status FROM exam_syllabus_examinable_points
                   WHERE syllabus_id = %s AND point_id = %s FOR UPDATE""",
                (syllabus_id, payload.point_id),
            ).fetchone()
            if existing is not None and str(existing[0]) == "VERIFIED":
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "EXAMINABLE_POINT_ALREADY_VERIFIED", "message": "A verified point must first be returned to NEEDS_REVIEW by an independent reviewer."}})
            connection.execute(
                """INSERT INTO exam_syllabus_examinable_points
                   (syllabus_id, point_id, unit_id, point_type, point_statement, page_number,
                    source_locator, source_evidence, mapping_status, mapping_gap_reason,
                    review_status, created_by)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'NEEDS_REVIEW', %s,
                           'NEEDS_REVIEW', %s)
                   ON CONFLICT (syllabus_id, point_id) DO UPDATE SET
                     unit_id = EXCLUDED.unit_id, point_type = EXCLUDED.point_type,
                     point_statement = EXCLUDED.point_statement, page_number = EXCLUDED.page_number,
                     source_locator = EXCLUDED.source_locator, source_evidence = EXCLUDED.source_evidence,
                     mapping_status = 'NEEDS_REVIEW', mapping_gap_reason = EXCLUDED.mapping_gap_reason,
                     review_status = 'NEEDS_REVIEW', created_by = EXCLUDED.created_by,
                     created_at = NOW(), reviewed_at = NULL, reviewed_by = NULL, review_note = ''""",
                (syllabus_id, payload.point_id, payload.unit_id, payload.point_type,
                 payload.point_statement, payload.page_number, payload.source_locator,
                 payload.source_evidence, payload.mapping_gap_reason, actor),
            )
            connection.execute(
                "DELETE FROM exam_syllabus_point_concepts WHERE syllabus_id = %s AND point_id = %s",
                (syllabus_id, payload.point_id),
            )
            for concept_id in payload.concept_ids:
                connection.execute(
                    """INSERT INTO exam_syllabus_point_concepts
                       (syllabus_id, point_id, concept_id, created_by)
                       VALUES (%s, %s, %s, %s)""",
                    (syllabus_id, payload.point_id, concept_id, actor),
                )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'EXAMINABLE_POINT', %s, 'AUTHOR', %s, 'NEEDS_REVIEW', %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, payload.point_id, actor, payload.author_note,
                 json.dumps({"unit_id": payload.unit_id, "point_type": payload.point_type,
                             "point_statement": payload.point_statement, "page_number": payload.page_number,
                             "source_locator": payload.source_locator, "source_evidence": payload.source_evidence,
                             "concept_ids": payload.concept_ids, "mapping_gap_reason": payload.mapping_gap_reason})),
            )
        return _response(HTTPStatus.CREATED, {"syllabus_id": syllabus_id, "point_id": payload.point_id,
                                              "review_status": "NEEDS_REVIEW", "created_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "EXAMINABLE_POINT_SAVE_FAILED", "message": "Point candidate was not saved; verify its identifiers, verified parent unit and source evidence."}})
    finally:
        connection.close()


@router.post("/{syllabus_id}/examinable-points/{point_id}/review", name="review_examinable_point")
def review_examinable_point(
    syllabus_id: str, point_id: str, payload: ExaminablePointDecision, request: Request
) -> Response:
    actor, error = _authorized(request, reviewer=True)
    if error is not None:
        return error
    if not syllabus_id or syllabus_id != syllabus_id.strip() or len(syllabus_id) > 128 or not point_id or point_id != point_id.strip() or len(point_id) > 128:
        return _response(HTTPStatus.BAD_REQUEST, {"error": {"code": "INVALID_EXAMINABLE_POINT_ID", "message": "Syllabus and point IDs must be trimmed and 1-128 characters."}})
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            _, error = _valid_syllabus_for_point_authoring(connection, syllabus_id)
            if error is not None:
                return error
            point = connection.execute(
                """SELECT created_by, mapping_gap_reason, review_status
                   FROM exam_syllabus_examinable_points
                   WHERE syllabus_id = %s AND point_id = %s FOR UPDATE""",
                (syllabus_id, point_id),
            ).fetchone()
            if point is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "EXAMINABLE_POINT_NOT_FOUND", "message": "Examinable point was not found."}})
            if str(point[0]) == actor:
                return _response(HTTPStatus.FORBIDDEN, {"error": {"code": "INDEPENDENT_REVIEW_REQUIRED", "message": "The point author cannot review their own examinable point."}})
            concept_rows = connection.execute(
                """SELECT concept_id FROM exam_syllabus_point_concepts
                   WHERE syllabus_id = %s AND point_id = %s FOR UPDATE""",
                (syllabus_id, point_id),
            ).fetchall()
            is_mapping_gap = bool(str(point[1]).strip())
            if is_mapping_gap and concept_rows:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "POINT_MAPPING_CONFLICT", "message": "A point cannot have both concept mappings and a mapping-gap declaration."}})
            if not is_mapping_gap and not concept_rows:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "POINT_MAPPING_REQUIRED", "message": "Map the point to at least one canonical concept or record a reviewed mapping gap."}})
            for item in payload.dimensions:
                connection.execute(
                    """INSERT INTO exam_syllabus_point_dimensions
                       (syllabus_id, point_id, dimension_key, assessment, assessment_reason, assessed_by)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (syllabus_id, point_id, dimension_key) DO UPDATE SET
                         assessment = EXCLUDED.assessment,
                         assessment_reason = EXCLUDED.assessment_reason,
                         assessed_at = NOW(), assessed_by = EXCLUDED.assessed_by""",
                    (syllabus_id, point_id, item.dimension_key, item.assessment,
                     item.assessment_reason, actor),
                )
            if payload.decision == "VERIFIED" and not any(item.assessment == "GAP" for item in payload.dimensions):
                if not is_mapping_gap:
                    connection.execute(
                        """UPDATE exam_syllabus_point_concepts
                           SET review_status = 'VERIFIED', reviewed_at = NOW(),
                               reviewed_by = %s, review_note = %s
                           WHERE syllabus_id = %s AND point_id = %s""",
                        (actor, payload.review_note, syllabus_id, point_id),
                    )
            mapping_status = "MAPPING_GAP" if is_mapping_gap else "MAPPED"
            connection.execute(
                """UPDATE exam_syllabus_examinable_points
                   SET mapping_status = %s, review_status = %s,
                       reviewed_at = NOW(), reviewed_by = %s, review_note = %s
                   WHERE syllabus_id = %s AND point_id = %s""",
                (mapping_status, payload.decision, actor, payload.review_note, syllabus_id, point_id),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'EXAMINABLE_POINT', %s, 'REVIEWER', %s, %s, %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, point_id, actor, payload.decision, payload.review_note,
                 json.dumps({"mapping_status": mapping_status, "mapping_gap_reason": point[1],
                             "dimensions": [item.model_dump() for item in payload.dimensions]})),
            )
        return _response(HTTPStatus.OK, {"syllabus_id": syllabus_id, "point_id": point_id,
                                         "review_status": payload.decision, "mapping_status": mapping_status,
                                         "reviewed_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "EXAMINABLE_POINT_REVIEW_FAILED", "message": "Point review was not saved; check mapping evidence and coverage dimensions."}})
    finally:
        connection.close()


@router.post("/{syllabus_id}/examinable-points/{point_id}/learning-items", status_code=201, name="create_point_one_liner_link")
def create_point_one_liner_link(
    syllabus_id: str, point_id: str, payload: PointLearningItemDraft, request: Request
) -> Response:
    actor, error = _authorized(request, reviewer=False)
    if error is not None:
        return error
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            point = connection.execute(
                """SELECT mapping_status, review_status
                   FROM exam_syllabus_examinable_points
                   WHERE syllabus_id = %s AND point_id = %s FOR UPDATE""",
                (syllabus_id, point_id),
            ).fetchone()
            if point is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "EXAMINABLE_POINT_NOT_FOUND", "message": "Examinable point was not found."}})
            if str(point[0]) != "MAPPED" or str(point[1]) != "VERIFIED":
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "POINT_NOT_READY_FOR_LEARNING_LINK", "message": "Only a verified, concept-mapped point can receive a learning-item link."}})
            item = connection.execute(
                """SELECT concept_id, verification_status FROM question_bank_one_liners
                   WHERE one_liner_id = %s""",
                (payload.one_liner_id,),
            ).fetchone()
            if item is None or str(item[1]) != "VERIFIED":
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "VERIFIED_ONE_LINER_REQUIRED", "message": "Only an independently VERIFIED One-Liner can be linked for coverage."}})
            mapped = connection.execute(
                """SELECT 1 FROM exam_syllabus_point_concepts
                   WHERE syllabus_id = %s AND point_id = %s
                     AND concept_id = %s AND review_status = 'VERIFIED'""",
                (syllabus_id, point_id, str(item[0])),
            ).fetchone()
            if mapped is None:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "POINT_CONCEPT_LINK_MISMATCH", "message": "The One-Liner concept is not an independently reviewed mapping for this point."}})
            connection.execute(
                """INSERT INTO exam_syllabus_point_one_liner_links
                   (syllabus_id, point_id, one_liner_id, created_by)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (syllabus_id, point_id, one_liner_id) DO NOTHING""",
                (syllabus_id, point_id, payload.one_liner_id, actor),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'POINT_LEARNING_ITEM', %s, 'AUTHOR', %s, 'NEEDS_REVIEW', %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, f"{point_id}:{payload.one_liner_id}", actor,
                 payload.author_note, json.dumps({"point_id": point_id, "one_liner_id": payload.one_liner_id})),
            )
        return _response(HTTPStatus.CREATED, {"syllabus_id": syllabus_id, "point_id": point_id,
                                              "one_liner_id": payload.one_liner_id,
                                              "review_status": "NEEDS_REVIEW", "created_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "POINT_LEARNING_LINK_SAVE_FAILED", "message": "The point-to-One-Liner link was not saved."}})
    finally:
        connection.close()


@router.post("/{syllabus_id}/examinable-points/{point_id}/learning-items/{one_liner_id}/review", name="review_point_one_liner_link")
def review_point_one_liner_link(
    syllabus_id: str, point_id: str, one_liner_id: str,
    payload: PointLearningItemDecision, request: Request
) -> Response:
    actor, error = _authorized(request, reviewer=True)
    if error is not None:
        return error
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            row = connection.execute(
                """SELECT link.created_by, one_liner.concept_id, one_liner.verification_status
                   FROM exam_syllabus_point_one_liner_links AS link
                   JOIN question_bank_one_liners AS one_liner
                     ON one_liner.one_liner_id = link.one_liner_id
                   WHERE link.syllabus_id = %s AND link.point_id = %s
                     AND link.one_liner_id = %s FOR UPDATE OF link""",
                (syllabus_id, point_id, one_liner_id),
            ).fetchone()
            if row is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "POINT_LEARNING_LINK_NOT_FOUND", "message": "Point-to-One-Liner link was not found."}})
            if str(row[0]) == actor:
                return _response(HTTPStatus.FORBIDDEN, {"error": {"code": "INDEPENDENT_REVIEW_REQUIRED", "message": "The link author cannot review their own point-to-One-Liner link."}})
            if payload.decision == "VERIFIED":
                if str(row[2]) != "VERIFIED":
                    return _response(HTTPStatus.CONFLICT, {"error": {"code": "VERIFIED_ONE_LINER_REQUIRED", "message": "The linked One-Liner must remain VERIFIED."}})
                mapped = connection.execute(
                    """SELECT 1 FROM exam_syllabus_point_concepts
                       WHERE syllabus_id = %s AND point_id = %s
                         AND concept_id = %s AND review_status = 'VERIFIED'""",
                    (syllabus_id, point_id, str(row[1])),
                ).fetchone()
                if mapped is None:
                    return _response(HTTPStatus.CONFLICT, {"error": {"code": "POINT_CONCEPT_LINK_MISMATCH", "message": "The learning item is not linked to a verified concept mapping for this point."}})
            connection.execute(
                """UPDATE exam_syllabus_point_one_liner_links
                   SET review_status = %s, reviewed_at = NOW(), reviewed_by = %s, review_note = %s
                   WHERE syllabus_id = %s AND point_id = %s AND one_liner_id = %s""",
                (payload.decision, actor, payload.review_note, syllabus_id, point_id, one_liner_id),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'POINT_LEARNING_ITEM', %s, 'REVIEWER', %s, %s, %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, f"{point_id}:{one_liner_id}", actor, payload.decision,
                 payload.review_note, json.dumps({"point_id": point_id, "one_liner_id": one_liner_id,
                                                 "concept_id": str(row[1])})),
            )
        return _response(HTTPStatus.OK, {"syllabus_id": syllabus_id, "point_id": point_id,
                                         "one_liner_id": one_liner_id, "review_status": payload.decision,
                                         "reviewed_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "POINT_LEARNING_LINK_REVIEW_FAILED", "message": "The point-to-One-Liner link review was not saved."}})
    finally:
        connection.close()



@router.post("/{syllabus_id}/examinable-points/attest-complete", name="attest_examinable_point_inventory")
def attest_examinable_point_inventory(
    syllabus_id: str, payload: PointInventoryAttestation, request: Request
) -> Response:
    """Attest only after all points, concept mappings and dimensions are independently reviewed."""
    actor, error = _authorized(request, reviewer=True)
    if error is not None:
        return error
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            source = connection.execute(
                "SELECT source_status, syllabus_inventory_complete, examinable_points_inventory_complete FROM exam_syllabus_documents WHERE syllabus_id = %s FOR UPDATE",
                (syllabus_id,),
            ).fetchone()
            if source is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
            if str(source[0]) != "VERIFIED" or source[1] is not True:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "SYLLABUS_SOURCE_NOT_READY", "message": "Verify the official source and UNIT/TOPIC/SUBTOPIC inventory first."}})
            if source[2] is True:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "EXAMINABLE_POINT_INVENTORY_ALREADY_COMPLETE", "message": "Point inventory is already attested complete."}})
            total = connection.execute(
                "SELECT COUNT(*) FROM exam_syllabus_examinable_points WHERE syllabus_id = %s",
                (syllabus_id,),
            ).fetchone()
            blockers = connection.execute(
                """SELECT COUNT(*) FROM exam_syllabus_examinable_points AS p
                   WHERE p.syllabus_id = %s AND (
                     p.review_status <> 'VERIFIED' OR p.mapping_status <> 'MAPPED'
                     OR NOT EXISTS (
                       SELECT 1 FROM exam_syllabus_point_concepts AS pc
                       WHERE pc.syllabus_id = p.syllabus_id AND pc.point_id = p.point_id
                         AND pc.review_status = 'VERIFIED'
                     )
                     OR (SELECT COUNT(*) FROM exam_syllabus_point_dimensions AS d
                         WHERE d.syllabus_id = p.syllabus_id AND d.point_id = p.point_id) <> 9
                     OR EXISTS (
                       SELECT 1 FROM exam_syllabus_point_dimensions AS d
                       WHERE d.syllabus_id = p.syllabus_id AND d.point_id = p.point_id
                         AND d.assessment = 'GAP'
                     )
                   )""",
                (syllabus_id,),
            ).fetchone()
            if total is None or int(total[0] or 0) == 0 or blockers is None or int(blockers[0] or 0) != 0:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "EXAMINABLE_POINT_INVENTORY_INCOMPLETE", "message": "All points, mappings and nine coverage dimensions must pass independent review."}})
            self_authored = connection.execute(
                "SELECT 1 FROM exam_syllabus_examinable_points WHERE syllabus_id = %s AND created_by = %s LIMIT 1",
                (syllabus_id, actor),
            ).fetchone()
            if self_authored is not None:
                return _response(HTTPStatus.FORBIDDEN, {"error": {"code": "INDEPENDENT_REVIEW_REQUIRED", "message": "A point author cannot attest the full point inventory."}})
            connection.execute(
                """UPDATE exam_syllabus_documents
                   SET examinable_points_inventory_complete = TRUE,
                       examinable_points_reviewed_at = NOW(),
                       examinable_points_reviewed_by = %s,
                       examinable_points_review_note = %s
                   WHERE syllabus_id = %s""",
                (actor, payload.review_note, syllabus_id),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'EXAMINABLE_POINT', 'INVENTORY', 'REVIEWER', %s, 'VERIFIED', %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, actor, payload.review_note,
                 json.dumps({"point_count": int(total[0]), "inventory_complete": True})),
            )
        return _response(HTTPStatus.OK, {"syllabus_id": syllabus_id, "point_count": int(total[0]),
                                         "examinable_points_inventory_complete": True, "reviewed_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "EXAMINABLE_POINT_ATTESTATION_FAILED", "message": "Point inventory attestation failed database integrity checks."}})
    finally:
        connection.close()


@router.post("/{syllabus_id}/examinable-points/reopen", name="reopen_examinable_point_inventory")
def reopen_examinable_point_inventory(
    syllabus_id: str, payload: PointInventoryAttestation, request: Request
) -> Response:
    """Reopen a previously attested point inventory with an append-only audit note."""
    actor, error = _authorized(request, reviewer=True)
    if error is not None:
        return error
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        with connection.transaction():
            row = connection.execute(
                "SELECT examinable_points_inventory_complete FROM exam_syllabus_documents WHERE syllabus_id = %s FOR UPDATE",
                (syllabus_id,),
            ).fetchone()
            if row is None:
                return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
            if row[0] is not True:
                return _response(HTTPStatus.CONFLICT, {"error": {"code": "EXAMINABLE_POINT_INVENTORY_NOT_LOCKED", "message": "Point inventory is not attested complete."}})
            connection.execute(
                """UPDATE exam_syllabus_documents
                   SET examinable_points_inventory_complete = FALSE,
                       examinable_points_reviewed_at = NULL,
                       examinable_points_reviewed_by = NULL,
                       examinable_points_review_note = ''
                   WHERE syllabus_id = %s""",
                (syllabus_id,),
            )
            connection.execute(
                """INSERT INTO exam_syllabus_review_audit
                   (audit_id, syllabus_id, entity_type, entity_id, actor_role, actor_id, decision, review_note, evidence)
                   VALUES (%s, %s, 'EXAMINABLE_POINT', 'INVENTORY', 'REVIEWER', %s, 'REOPENED', %s, %s::jsonb)""",
                (uuid4().hex, syllabus_id, actor, payload.review_note,
                 json.dumps({"inventory_complete": False, "reopened_by": actor})),
            )
        return _response(HTTPStatus.OK, {"syllabus_id": syllabus_id,
                                         "examinable_points_inventory_complete": False, "reopened_by": actor})
    except Exception:
        return _response(HTTPStatus.CONFLICT, {"error": {"code": "EXAMINABLE_POINT_REOPEN_FAILED", "message": "Point inventory was not reopened."}})
    finally:
        connection.close()


@router.get("/{syllabus_id}/examinable-point-gap-report", name="get_examinable_point_gap_report")
def get_examinable_point_gap_report(
    syllabus_id: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100000),
) -> Response:
    actor, error = _authorized(request, reviewer=True)
    if error is not None:
        return error
    if not syllabus_id or syllabus_id != syllabus_id.strip() or len(syllabus_id) > 128:
        return _response(HTTPStatus.BAD_REQUEST, {"error": {"code": "INVALID_SYLLABUS_ID", "message": "syllabus_id must be trimmed and 1-128 characters."}})
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        report = PostgresExaminablePointRepository(connection).get_gap_report(
            syllabus_id, limit=limit, offset=offset
        )
        if report is None:
            return _response(HTTPStatus.NOT_FOUND, {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}})
        report["generated_by"] = actor
        return _response(HTTPStatus.OK, report)
    except ValueError:
        return _response(HTTPStatus.BAD_REQUEST, {"error": {"code": "INVALID_GAP_REPORT_PAGE", "message": "The requested report page is invalid."}})
    except RepositoryError:
        return _response(HTTPStatus.SERVICE_UNAVAILABLE, {"error": {"code": "EXAMINABLE_POINT_REPORT_UNAVAILABLE", "message": "The examinable-point coverage report could not be read."}})
    finally:
        connection.close()
