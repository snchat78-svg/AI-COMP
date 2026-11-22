from __future__ import annotations

import hashlib
import re
from http import HTTPStatus

from fastapi import APIRouter, Request
from starlette.responses import Response

from ai_comp.api.preparation_guidance_routes import (
    _authenticated_learner_or_error,
    _json_response,
)

router = APIRouter(prefix="/api/v1/learners", tags=["question-bank-content"])

_CONTENT_MANIFEST_SQL = """
SELECT
    (SELECT COUNT(*)::INTEGER FROM concepts) AS topic_count,
    (
        SELECT COUNT(*)::INTEGER
        FROM question_bank_one_liners
        WHERE verification_status = 'VERIFIED'
    ) AS verified_one_liner_count,
    (
        SELECT COUNT(*)::INTEGER
        FROM question_bank_one_liners
        WHERE verification_status IN ('DRAFT', 'NEEDS_REVIEW')
    ) AS review_pending_one_liner_count,
    (
        SELECT MD5(COALESCE(
            STRING_AGG(
                CONCAT_WS(CHR(31), concept_id, label, subject, topic, subtopic),
                CHR(30) ORDER BY concept_id
            ),
            ''
        ))
        FROM concepts
    ) AS catalogue_revision,
    (
        SELECT MD5(COALESCE(
            STRING_AGG(
                CONCAT_WS(CHR(31), one_liner_id, content_hash, updated_at::TEXT),
                CHR(30) ORDER BY one_liner_id
            ),
            ''
        ))
        FROM question_bank_one_liners
        WHERE verification_status = 'VERIFIED'
    ) AS published_questions_revision
"""


def _non_negative_count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("content manifest count is invalid")
    return value


def _digest(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{32}", value) is None:
        raise ValueError("content manifest digest is invalid")
    return value


@router.get(
    "/{learner_id}/question-bank/content-manifest",
    name="get_question_bank_content_manifest",
)
def get_question_bank_content_manifest(learner_id: str, request: Request) -> Response:
    """Return a stable, authenticated revision for client-side content sync.

    The published revision includes only independently VERIFIED one-liners.
    Draft/review-pending rows are counted for status displays but never enter
    the published revision.
    """
    _, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error

    connection_factory = getattr(request.app.state, "question_bank_connection_factory", None)
    if not callable(connection_factory):
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_NOT_CONFIGURED",
                "message": "The topic question bank is not configured for this server.",
            }
        })

    connection = None
    try:
        connection = connection_factory()
        row = connection.execute(_CONTENT_MANIFEST_SQL).fetchone()
        if row is None or len(row) != 5:
            raise ValueError("content manifest query returned an invalid row")

        topic_count = _non_negative_count(row[0])
        verified_count = _non_negative_count(row[1])
        review_pending_count = _non_negative_count(row[2])
        catalogue_revision = _digest(row[3])
        published_questions_revision = _digest(row[4])

        revision_material = (
            "ai-comp-content-manifest-v1:"
            f"{catalogue_revision}:{published_questions_revision}"
        )
        revision = hashlib.sha256(revision_material.encode("ascii")).hexdigest()

        return _json_response(HTTPStatus.OK, {
            "schema_version": 1,
            "revision": revision,
            "catalogue_revision": catalogue_revision,
            "published_questions_revision": published_questions_revision,
            "topic_count": topic_count,
            "verified_one_liner_count": verified_count,
            "review_pending_one_liner_count": review_pending_count,
        })
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_CONTENT_MANIFEST_UNAVAILABLE",
                "message": "Question-bank content revision could not be loaded.",
            }
        })
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


__all__ = ["router"]
