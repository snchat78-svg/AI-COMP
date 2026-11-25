from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime, timedelta
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

_CONTENT_DELTA_SQL = """
SELECT
    one_liner_id,
    concept_id,
    question_text,
    answer_text,
    language_code,
    source_url,
    source_evidence,
    verification_status,
    importance_score,
    updated_at
FROM question_bank_one_liners
WHERE (
    %s::TIMESTAMPTZ IS NULL
    OR (updated_at, one_liner_id) > (%s::TIMESTAMPTZ, %s)
)
ORDER BY updated_at, one_liner_id
LIMIT %s
"""


def _non_negative_count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("content manifest count is invalid")
    return value


def _digest(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{32}", value) is None:
        raise ValueError("content manifest digest is invalid")
    return value


def _encode_delta_cursor(updated_at: str, one_liner_id: str) -> str:
    payload = json.dumps(
        {"v": 1, "updated_at": updated_at, "one_liner_id": one_liner_id},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_delta_cursor(cursor: str | None) -> tuple[str | None, str]:
    if cursor is None:
        return None, ""
    if not isinstance(cursor, str) or not cursor or len(cursor) > 2048:
        raise ValueError("content delta cursor is invalid")
    try:
        padded = cursor + ("=" * (-len(cursor) % 4))
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("content delta cursor is invalid") from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != {"v", "updated_at", "one_liner_id"}
        or payload.get("v") != 1
        or not isinstance(payload.get("updated_at"), str)
        or not isinstance(payload.get("one_liner_id"), str)
        or len(payload["one_liner_id"]) > 128
    ):
        raise ValueError("content delta cursor is invalid")
    try:
        parsed = datetime.fromisoformat(payload["updated_at"])
    except ValueError as exc:
        raise ValueError("content delta cursor timestamp is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("content delta cursor timestamp must include a timezone")
    return payload["updated_at"], payload["one_liner_id"]


def _iso_timestamp(value: object) -> str:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value)
    else:
        raise ValueError("content delta timestamp is invalid")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("content delta timestamp must include a timezone")
    return parsed.isoformat()


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


@router.get(
    "/{learner_id}/question-bank/content-delta",
    name="get_question_bank_content_delta",
)
def get_question_bank_content_delta(
    learner_id: str,
    request: Request,
    cursor: str | None = None,
    limit: int = 100,
) -> Response:
    """Return a bounded, keyset-paginated change feed for one-liner content.

    All review states are returned so clients can remove an item from their
    VERIFIED cache when it is rejected or returned for review. Clients must
    persist only VERIFIED records. The cursor deliberately overlaps the
    final timestamp by one microsecond to make same-timestamp writes safe;
    clients therefore must upsert by one_liner_id.
    """
    _, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    if not 1 <= limit <= 100:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_LIMIT", "message": "limit must be between 1 and 100."}
        })
    try:
        cursor_timestamp, cursor_id = _decode_delta_cursor(cursor)
    except ValueError:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_CONTENT_DELTA_CURSOR", "message": "The content sync cursor is invalid."}
        })

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
        rows = connection.execute(
            _CONTENT_DELTA_SQL,
            (cursor_timestamp, cursor_timestamp, cursor_id, limit + 1),
        ).fetchall()
        if not isinstance(rows, (list, tuple)):
            raise ValueError("content delta query returned an invalid page")
        selected = rows[:limit]
        items = []
        for row in selected:
            if len(row) != 10:
                raise ValueError("content delta row has an invalid shape")
            delta_item = {
                "one_liner_id": row[0],
                "verification_status": row[7],
                "updated_at": _iso_timestamp(row[9]),
            }
            # A downgrade is a cache tombstone, not a second way to read drafts.
            # The existing review-pending lane remains the only learner API that
            # returns full NEEDS_REVIEW/DRAFT question text.
            if row[7] == "VERIFIED":
                delta_item.update({
                    "concept_id": row[1],
                    "question_text": row[2],
                    "answer_text": row[3],
                    "language_code": row[4],
                    "source_url": row[5],
                    "source_evidence": row[6],
                    "importance_score": row[8],
                })
            items.append(delta_item)

        has_more = len(rows) > limit
        next_cursor = cursor
        if selected:
            last_timestamp = datetime.fromisoformat(items[-1]["updated_at"])
            if not has_more:
                last_timestamp -= timedelta(microseconds=1)
            next_cursor = _encode_delta_cursor(
                last_timestamp.isoformat(),
                items[-1]["one_liner_id"] if has_more else "",
            )

        return _json_response(HTTPStatus.OK, {
            "schema_version": 1,
            "items": items,
            "pagination": {
                "limit": limit,
                "returned": len(items),
                "has_more": has_more,
                "next_cursor": next_cursor,
            },
        })
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_CONTENT_DELTA_UNAVAILABLE",
                "message": "Question-bank content updates could not be loaded.",
            }
        })
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


__all__ = ["router"]
