from __future__ import annotations

import json
from collections.abc import Mapping
from http import HTTPStatus
from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from starlette.responses import Response

from ai_comp.application.preparation_guidance_http import (
    HTTPResponse,
    PreparationGuidanceHTTPAdapter,
)
from ai_comp.api.dependencies import PreparationContextUnavailable


router = APIRouter(prefix="/api/v1/learners", tags=["preparation-guidance"])

JSON_SECURITY_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
}


def _json_response(status: int | HTTPStatus, payload: dict[str, object]) -> Response:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return Response(
        content=body,
        status_code=int(status),
        headers=JSON_SECURITY_HEADERS,
    )


def _from_adapter(response: HTTPResponse) -> Response:
    return Response(
        content=response.body,
        status_code=response.status_code,
        headers=dict(response.headers),
    )


def _valid_learner_id(learner_id: str) -> bool:
    return (
        bool(learner_id)
        and len(learner_id) <= 128
        and all(ch.isalnum() or ch in "-_." for ch in learner_id)
    )


def _validate_query_string(query_string: str) -> Response | None:
    """Reject invalid parameters before asking a provider to load learner data."""
    try:
        query = parse_qs(query_string, keep_blank_values=True, strict_parsing=False)
    except ValueError:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {
                "code": "INVALID_QUERY",
                "message": "Only one history_limit query parameter is supported.",
            }
        })

    if set(query) - {"history_limit"} or any(len(values) != 1 for values in query.values()):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {
                "code": "INVALID_QUERY",
                "message": "Only one history_limit query parameter is supported.",
            }
        })

    try:
        history_limit = int(query.get("history_limit", ["50"])[0])
    except (TypeError, ValueError):
        history_limit = 0

    if not 1 <= history_limit <= 500:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {
                "code": "INVALID_HISTORY_LIMIT",
                "message": "history_limit must be an integer from 1 to 500.",
            }
        })
    return None


@router.get("/{learner_id}/preparation-guidance", name="preparation_guidance")
def get_preparation_guidance(learner_id: str, request: Request) -> Response:
    """Mount the Phase 6.29 HTTP contract on a real FastAPI route."""
    if not _valid_learner_id(learner_id):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {
                "code": "INVALID_LEARNER_ID",
                "message": "Learner ID format is invalid.",
            }
        })

    identity_provider = request.app.state.learner_identity_provider
    if identity_provider is None:
        return _json_response(HTTPStatus.UNAUTHORIZED, {
            "error": {
                "code": "AUTHENTICATION_REQUIRED",
                "message": "Authentication is required.",
            }
        })

    try:
        authenticated_learner_id = identity_provider(request)
    except Exception:
        # Fail closed without disclosing authentication-provider internals.
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "AUTHENTICATION_UNAVAILABLE",
                "message": "Authentication could not be verified.",
            }
        })

    if (
        not isinstance(authenticated_learner_id, str)
        or not authenticated_learner_id
        or not authenticated_learner_id.strip()
        or authenticated_learner_id != authenticated_learner_id.strip()
    ):
        return _json_response(HTTPStatus.UNAUTHORIZED, {
            "error": {
                "code": "AUTHENTICATION_REQUIRED",
                "message": "Authentication is required.",
            }
        })

    if learner_id != authenticated_learner_id:
        return _json_response(HTTPStatus.FORBIDDEN, {
            "error": {
                "code": "LEARNER_SCOPE_MISMATCH",
                "message": "Requested learner is not authorized.",
            }
        })

    invalid_query = _validate_query_string(request.url.query)
    if invalid_query is not None:
        return invalid_query

    service = request.app.state.preparation_guidance_api_service
    context_provider = request.app.state.preparation_context_provider
    if service is None or context_provider is None:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_GUIDANCE_NOT_CONFIGURED",
                "message": "Preparation guidance is not configured for this server.",
            }
        })

    try:
        context = context_provider.load_context(learner_id, request=request)
    except PreparationContextUnavailable:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_CONTEXT_UNAVAILABLE",
                "message": "No preparation context is currently available.",
            }
        })
    except Exception:
        return _json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {
            "error": {
                "code": "PREPARATION_CONTEXT_LOAD_FAILED",
                "message": "Unable to load preparation context.",
            }
        })

    if not isinstance(context, Mapping):
        return _json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {
            "error": {
                "code": "INVALID_PREPARATION_CONTEXT_PROVIDER",
                "message": "The preparation context provider returned an invalid result.",
            }
        })

    required_fields = {
        "test_id",
        "title",
        "question_count",
        "duration_seconds",
        "history",
        "question_history",
        "candidates",
        "questions",
    }
    if required_fields - set(context):
        # This is a server-side provider/configuration failure, not a client error.
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_CONTEXT_UNAVAILABLE",
                "message": "Required preparation context is not ready.",
            }
        })

    target = request.url.path
    if request.url.query:
        target = f"{target}?{request.url.query}"

    adapter = PreparationGuidanceHTTPAdapter(service)
    adapted = adapter.handle(
        method=request.method,
        target=target,
        authenticated_learner_id=authenticated_learner_id,
        request_context=dict(context),
    )
    return _from_adapter(adapted)


__all__ = ["get_preparation_guidance", "router"]
