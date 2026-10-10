from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from ai_comp.application.preparation_guidance_api import PreparationGuidanceAPIService
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode


@dataclass(frozen=True)
class HTTPResponse:
    """Minimal transport response, adaptable to WSGI/ASGI or a serverless host."""

    status_code: int
    body: bytes
    headers: tuple[tuple[str, str], ...]

    def json(self) -> dict[str, Any]:
        value = json.loads(self.body.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("response body must be a JSON object")
        return value


class PreparationGuidanceHTTPAdapter:
    """Framework-neutral HTTP adapter for the preparation-guidance read endpoint.

    Route: GET /api/v1/learners/{learner_id}/preparation-guidance
    The host must authenticate the caller and pass its authorized learner ID as
    authenticated_learner_id; this adapter deliberately has no auth bypass.
    """

    route_template = "/api/v1/learners/{learner_id}/preparation-guidance"

    def __init__(self, service: PreparationGuidanceAPIService) -> None:
        self.service = service

    def handle(
        self,
        *,
        method: str,
        target: str,
        authenticated_learner_id: str | None,
        request_context: dict[str, Any] | None = None,
    ) -> HTTPResponse:
        common_headers = (
            ("Content-Type", "application/json; charset=utf-8"),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
        )

        def response(status: HTTPStatus, payload: dict[str, Any]) -> HTTPResponse:
            return HTTPResponse(
                status_code=int(status),
                body=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
                headers=common_headers,
            )

        if method.upper() != "GET":
            return response(HTTPStatus.METHOD_NOT_ALLOWED, {
                "error": {"code": "METHOD_NOT_ALLOWED", "message": "Only GET is supported."}
            })

        try:
            parsed = urlsplit(target)
        except ValueError:
            return response(HTTPStatus.BAD_REQUEST, {
                "error": {"code": "INVALID_REQUEST_TARGET", "message": "Request target is invalid."}
            })
        if parsed.scheme or parsed.netloc or not parsed.path.startswith("/") or "#" in target:
            return response(HTTPStatus.BAD_REQUEST, {
                "error": {"code": "INVALID_REQUEST_TARGET", "message": "Request target must be an origin-form path."}
            })

        parts = parsed.path.split("/")
        if (
            len(parts) != 6
            or parts[1:4] != ["api", "v1", "learners"]
            or parts[5] != "preparation-guidance"
        ):
            return response(HTTPStatus.NOT_FOUND, {
                "error": {"code": "NOT_FOUND", "message": "Endpoint not found."}
            })

        try:
            learner_id = unquote(parts[4], errors="strict")
        except (UnicodeDecodeError, ValueError):
            learner_id = ""
        if (
            not learner_id
            or len(learner_id) > 128
            or any(not (ch.isalnum() or ch in "-_.") for ch in learner_id)
        ):
            return response(HTTPStatus.BAD_REQUEST, {
                "error": {"code": "INVALID_LEARNER_ID", "message": "Learner ID format is invalid."}
            })

        if not authenticated_learner_id or not authenticated_learner_id.strip():
            return response(HTTPStatus.UNAUTHORIZED, {
                "error": {"code": "AUTHENTICATION_REQUIRED", "message": "Authentication is required."}
            })
        if learner_id != authenticated_learner_id:
            return response(HTTPStatus.FORBIDDEN, {
                "error": {"code": "LEARNER_SCOPE_MISMATCH", "message": "Requested learner is not authorized."}
            })

        query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=False)
        allowed = {"history_limit"}
        if set(query) - allowed or any(len(values) != 1 for values in query.values()):
            return response(HTTPStatus.BAD_REQUEST, {
                "error": {"code": "INVALID_QUERY", "message": "Only one history_limit query parameter is supported."}
            })
        raw_limit = query.get("history_limit", ["50"])[0]
        try:
            history_limit = int(raw_limit)
        except (TypeError, ValueError):
            return response(HTTPStatus.BAD_REQUEST, {
                "error": {"code": "INVALID_HISTORY_LIMIT", "message": "history_limit must be an integer from 1 to 500."}
            })
        if not 1 <= history_limit <= 500:
            return response(HTTPStatus.BAD_REQUEST, {
                "error": {"code": "INVALID_HISTORY_LIMIT", "message": "history_limit must be an integer from 1 to 500."}
            })

        context = request_context or {}
        required = {
            "test_id", "title", "question_count", "duration_seconds",
            "history", "question_history", "candidates", "questions",
        }
        missing = sorted(required - set(context))
        if missing:
            return response(HTTPStatus.BAD_REQUEST, {
                "error": {
                    "code": "PREPARATION_CONTEXT_REQUIRED",
                    "message": "Preparation context has not been supplied by the application layer.",
                    "missing_fields": missing,
                }
            })

        try:
            result = self.service.build_response(
                learner_id,
                test_id=context["test_id"],
                title=context["title"],
                question_count=context["question_count"],
                duration_seconds=context["duration_seconds"],
                history=context["history"],
                question_history=context["question_history"],
                candidates=context["candidates"],
                questions=context["questions"],
                history_limit=history_limit,
                current_analysis=context.get("current_analysis"),
                mode=context.get("mode", PersonalizedPreparationMode.ADAPTIVE),
                scoring=context.get("scoring"),
                shuffle_questions=context.get("shuffle_questions", False),
                shuffle_seed=context.get("shuffle_seed"),
                exclude_question_ids=context.get("exclude_question_ids", ()),
                as_of=context.get("as_of"),
                generated_at=context.get("generated_at"),
            )
        except (ValueError, KeyError, TypeError) as exc:
            return response(HTTPStatus.BAD_REQUEST, {
                "error": {"code": "INVALID_PREPARATION_CONTEXT", "message": str(exc)}
            })
        except Exception:
            # Do not expose database, learner history, or internal exception data.
            return response(HTTPStatus.INTERNAL_SERVER_ERROR, {
                "error": {"code": "INTERNAL_ERROR", "message": "Unable to build preparation guidance."}
            })

        return response(HTTPStatus.OK, result.to_payload())


__all__ = ["HTTPResponse", "PreparationGuidanceHTTPAdapter"]
