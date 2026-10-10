from __future__ import annotations

import json
from collections.abc import Mapping
from http import HTTPStatus
from urllib.parse import parse_qs
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.responses import Response

from ai_comp.application.preparation_guidance_http import (
    HTTPResponse,
    PreparationGuidanceHTTPAdapter,
)
from ai_comp.api.dependencies import PreparationContextUnavailable
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.preparation_request import PreparationTestRequest
from ai_comp.domain.test_engine import ScoringPolicy, TestSpecification


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


class PreparationRequestPayload(BaseModel):
    """Untrusted user choices validated before they become a durable request."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    question_count: int = Field(ge=1, le=500)
    duration_seconds: int = Field(ge=1, le=86400)
    correct_marks: float = Field(default=1.0, gt=0.0, le=1000.0)
    incorrect_marks: float = Field(default=-0.25, le=0.0, ge=-1000.0)
    unattempted_marks: float = Field(default=0.0, le=0.0, ge=-1000.0)
    mode: PersonalizedPreparationMode = PersonalizedPreparationMode.ADAPTIVE
    concept_ids: list[str] = Field(default_factory=list, max_length=100)
    exclude_question_ids: list[str] = Field(default_factory=list, max_length=2000)
    shuffle_questions: bool = False
    shuffle_seed: int | None = None
    exam_id: str | None = Field(default=None, min_length=1, max_length=128)
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value.strip()

    @field_validator("concept_ids", "exclude_question_ids")
    @classmethod
    def ids_must_be_trimmed_and_unique(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or value != value.strip() for value in values):
            raise ValueError("IDs must be non-empty trimmed strings")
        if len(set(values)) != len(values):
            raise ValueError("IDs must be unique")
        return values

    @field_validator("exam_id", "subject_id")
    @classmethod
    def optional_labels_must_be_trimmed(cls, value: str | None) -> str | None:
        if value is not None and (not value.strip() or value != value.strip()):
            raise ValueError("metadata IDs must be non-empty trimmed strings")
        return value

    @model_validator(mode="after")
    def validate_shuffle_settings(self):
        if self.shuffle_questions and self.shuffle_seed is None:
            raise ValueError("shuffle_seed is required when shuffle_questions is enabled")
        return self

    def to_request(self, learner_id: str, request_id: str) -> PreparationTestRequest:
        specification = TestSpecification(
            test_id=f"prep-{request_id}",
            title=self.title,
            question_count=self.question_count,
            duration_seconds=self.duration_seconds,
            scoring=ScoringPolicy(
                correct_marks=self.correct_marks,
                incorrect_marks=self.incorrect_marks,
                unattempted_marks=self.unattempted_marks,
            ),
            shuffle_questions=self.shuffle_questions,
            shuffle_seed=self.shuffle_seed,
        )
        return PreparationTestRequest(
            learner_id=learner_id,
            specification=specification,
            mode=self.mode,
            concept_ids=tuple(self.concept_ids),
            exclude_question_ids=tuple(self.exclude_question_ids),
            exam_id=self.exam_id,
            subject_id=self.subject_id,
        )


def _authenticated_learner_or_error(
    learner_id: str,
    request: Request,
) -> tuple[str | None, Response | None]:
    if not _valid_learner_id(learner_id):
        return None, _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_LEARNER_ID", "message": "Learner ID format is invalid."}
        })
    identity_provider = request.app.state.learner_identity_provider
    if identity_provider is None:
        return None, _json_response(HTTPStatus.UNAUTHORIZED, {
            "error": {"code": "AUTHENTICATION_REQUIRED", "message": "Authentication is required."}
        })
    try:
        authenticated_learner_id = identity_provider(request)
    except Exception:
        return None, _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {"code": "AUTHENTICATION_UNAVAILABLE", "message": "Authentication could not be verified."}
        })
    if (
        not isinstance(authenticated_learner_id, str)
        or not authenticated_learner_id
        or not authenticated_learner_id.strip()
        or authenticated_learner_id != authenticated_learner_id.strip()
    ):
        return None, _json_response(HTTPStatus.UNAUTHORIZED, {
            "error": {"code": "AUTHENTICATION_REQUIRED", "message": "Authentication is required."}
        })
    if learner_id != authenticated_learner_id:
        return None, _json_response(HTTPStatus.FORBIDDEN, {
            "error": {"code": "LEARNER_SCOPE_MISMATCH", "message": "Requested learner is not authorized."}
        })
    return authenticated_learner_id, None


def _request_record_payload(record) -> dict[str, object]:
    spec = record.request.specification
    return {
        "request_id": record.request_id,
        "learner_id": record.request.learner_id,
        "status": record.status.value,
        "test_id": spec.test_id,
        "title": spec.title,
        "question_count": spec.question_count,
        "duration_seconds": spec.duration_seconds,
        "scoring": {
            "correct_marks": spec.scoring.correct_marks,
            "incorrect_marks": spec.scoring.incorrect_marks,
            "unattempted_marks": spec.scoring.unattempted_marks,
        },
        "mode": record.request.mode.value,
        "concept_ids": list(record.request.concept_ids),
        "exclude_question_ids": list(record.request.exclude_question_ids),
        "shuffle_questions": spec.shuffle_questions,
        "shuffle_seed": spec.shuffle_seed,
        "exam_id": record.request.exam_id,
        "subject_id": record.request.subject_id,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


@router.post("/{learner_id}/preparation-requests", status_code=201, name="create_preparation_request")
def create_preparation_request(
    learner_id: str,
    payload: PreparationRequestPayload,
    request: Request,
) -> Response:
    """Persist validated settings as the learner's new active preparation request."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error

    repository = request.app.state.preparation_test_request_repository
    if repository is None:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_NOT_CONFIGURED",
                "message": "Preparation request storage is not configured.",
            }
        })

    request_id = uuid4().hex
    try:
        domain_request = payload.to_request(authenticated_learner_id, request_id)
        record = repository.save_active(request_id, domain_request)
    except ValueError as exc:
        return _json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {
            "error": {"code": "INVALID_PREPARATION_REQUEST", "message": str(exc)}
        })
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_UNAVAILABLE",
                "message": "Unable to save preparation settings.",
            }
        })
    return _json_response(HTTPStatus.CREATED, _request_record_payload(record))


@router.get("/{learner_id}/preparation-requests/active", name="get_active_preparation_request")
def get_active_preparation_request(learner_id: str, request: Request) -> Response:
    """Read back the authenticated learner's durable active preparation settings."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    repository = request.app.state.preparation_test_request_repository
    if repository is None:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_NOT_CONFIGURED",
                "message": "Preparation request storage is not configured.",
            }
        })
    try:
        record = repository.get_active_for_learner(authenticated_learner_id)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_UNAVAILABLE",
                "message": "Unable to load preparation settings.",
            }
        })
    if record is None:
        return _json_response(HTTPStatus.NOT_FOUND, {
            "error": {
                "code": "NO_ACTIVE_PREPARATION_REQUEST",
                "message": "Save preparation settings before requesting guidance.",
            }
        })
    return _json_response(HTTPStatus.OK, _request_record_payload(record))


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
