from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Query, Request
from starlette.responses import Response

from ai_comp.api.exam_syllabus_admin_routes import (
    _authorized,
    _connection_or_error,
    _response,
)
from ai_comp.database.postgres_examinable_points import PostgresExaminablePointRepository
from ai_comp.database.repository import RepositoryError

router = APIRouter(prefix="/api/v1/admin/exam-syllabi", tags=["exam-syllabus-review"])


@router.get("/{syllabus_id}/examinable-point-gap-report", name="get_examinable_point_gap_report")
def get_examinable_point_gap_report(
    syllabus_id: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100000),
) -> Response:
    """Return a bounded, reviewer-only report; never infer completeness from candidate counts."""
    actor, error = _authorized(request, reviewer=True)
    if error is not None:
        return error
    if not syllabus_id or syllabus_id != syllabus_id.strip() or len(syllabus_id) > 128:
        return _response(
            HTTPStatus.BAD_REQUEST,
            {"error": {"code": "INVALID_SYLLABUS_ID", "message": "syllabus_id must be trimmed and 1-128 characters."}},
        )
    connection, error = _connection_or_error(request)
    if error is not None:
        return error
    try:
        report = PostgresExaminablePointRepository(connection).get_gap_report(
            syllabus_id, limit=limit, offset=offset
        )
        if report is None:
            return _response(
                HTTPStatus.NOT_FOUND,
                {"error": {"code": "SYLLABUS_NOT_FOUND", "message": "Syllabus candidate was not found."}},
            )
        report["generated_by"] = actor
        return _response(HTTPStatus.OK, report)
    except ValueError:
        return _response(
            HTTPStatus.BAD_REQUEST,
            {"error": {"code": "INVALID_GAP_REPORT_PAGE", "message": "The requested report page is invalid."}},
        )
    except RepositoryError:
        return _response(
            HTTPStatus.SERVICE_UNAVAILABLE,
            {"error": {"code": "EXAMINABLE_POINT_REPORT_UNAVAILABLE", "message": "The examinable-point coverage report could not be read."}},
        )
    finally:
        connection.close()
