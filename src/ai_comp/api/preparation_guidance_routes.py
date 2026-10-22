from __future__ import annotations

import hmac
import json
import logging
import os
from collections.abc import Mapping
from typing import Literal
import time
from http import HTTPStatus
from urllib.parse import parse_qs
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from ai_comp.analysis.personalized_preparation import PersonalizedPreparationService
from ai_comp.application.adaptive_practice_recommendations import (
    AdaptivePracticeRecommendationPlanner,
    NoAdaptivePracticeSignal,
)

from ai_comp.domain.test_engine import TestResult, TestSession, TestSessionStatus
from ai_comp.test_engine import TestEngine
from starlette.responses import Response

from ai_comp.application.preparation_guidance_http import (
    HTTPResponse,
    PreparationGuidanceHTTPAdapter,
)
from ai_comp.api.dependencies import PreparationContextUnavailable
from ai_comp.database.postgres_topic_question_bank import PostgresTopicQuestionBankRepository
from ai_comp.api.preparation_client_contract import (
    AdaptivePreparationRecommendationResponse,
    AnswerReviewResponse,
    COMMON_API_ERROR_RESPONSES,
    CompletedTestAnalyticsResponse,
    CurrentQuestionResponse,
    PreparationResultsSummaryResponse,
    PreparationSessionHistoryResponse,
    PreparationTestRequestResponse,
    PreparationTestSessionResponse,
    QuestionBankReadinessResponse,
    QuestionBankSubjectsResponse,
    QuestionBankTopicsResponse,
    PreviousYearQuestionsResponse,
    TopicOneLinerItem,
    TopicOneLinerListResponse,
    TopicPracticeGenerationResponse,
    SubmittedTestResponse,
)
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.preparation_request import PreparationRequestStatus, PreparationTestRequest
from ai_comp.domain.test_engine import ScoringPolicy, TestSpecification


router = APIRouter(prefix="/api/v1/learners", tags=["preparation-guidance"])
content_admin_router = APIRouter(prefix="/api/v1/admin/question-bank", tags=["question-bank-authoring"])

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


class SaveTopicOneLinerPayload(BaseModel):
    """Direct content-editor entry for a topic-linked short Q&A item."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    concept_id: str = Field(min_length=1, max_length=128)
    question_text: str = Field(min_length=1, max_length=1000)
    answer_text: str = Field(min_length=1, max_length=2000)
    language_code: str = Field(default="hi", min_length=2, max_length=20)
    source_url: str | None = Field(default=None, max_length=2000)
    source_evidence: str = Field(default="", max_length=4000)
    verification_status: Literal["DRAFT", "NEEDS_REVIEW", "VERIFIED", "REJECTED"] = "NEEDS_REVIEW"
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("concept_id", "question_text", "answer_text", "language_code")
    @classmethod
    def required_text_must_be_trimmed(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("required text fields must be non-empty and trimmed")
        return value

    @field_validator("source_url")
    @classmethod
    def source_must_be_https(cls, value: str | None) -> str | None:
        if value is not None and (not value.startswith("https://") or value != value.strip()):
            raise ValueError("source_url must be an absolute HTTPS URL")
        return value

    @model_validator(mode="after")
    def verified_items_need_source_evidence(self):
        if self.verification_status == "VERIFIED":
            if self.source_url is None or not self.source_evidence.strip():
                raise ValueError("VERIFIED one-liners require an HTTPS source URL and source evidence")
        return self


class GenerateTopicPracticePayload(BaseModel):
    """User-selected subject/time/count for generation-grounded mixed practice."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    subject_id: str = Field(min_length=1, max_length=200)
    question_count: int = Field(ge=1, le=500)
    duration_seconds: int = Field(ge=1, le=86400)
    language_code: str = Field(default="hi", min_length=2, max_length=20)

    @field_validator("subject_id", "language_code")
    @classmethod
    def labels_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field must not be blank")
        return value


class AdaptivePracticeRecommendationPayload(BaseModel):
    """Only test settings come from the client; learner history remains server-owned."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question_count: int = Field(default=20, ge=1, le=500)
    duration_seconds: int = Field(default=1800, ge=1, le=86400)
    correct_marks: float = Field(default=1.0, gt=0.0, le=1000.0)
    incorrect_marks: float = Field(default=-0.25, le=0.0, ge=-1000.0)
    unattempted_marks: float = Field(default=0.0, le=0.0, ge=-1000.0)
    max_concepts: int = Field(default=8, ge=1, le=20)


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
    except Exception as exc:
        # Log only the exception class: never include Authorization headers,
        # bearer tokens, learner IDs, or exception messages in production logs.
        logging.getLogger(__name__).warning(
            "Learner authentication verification unavailable (exception_type=%s)",
            type(exc).__name__,
        )
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


def _valid_request_id(request_id: str) -> bool:
    return (
        bool(request_id)
        and len(request_id) <= 128
        and all(ch.isalnum() or ch in "-_." for ch in request_id)
    )


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


@router.post("/{learner_id}/preparation-requests", status_code=201, name="create_preparation_request", responses={**COMMON_API_ERROR_RESPONSES, 201: {"model": PreparationTestRequestResponse, "description": "Persisted active preparation request."}})
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


@router.post(
    "/{learner_id}/preparation-recommendations",
    status_code=201,
    name="create_adaptive_practice_recommendation",
    responses={**COMMON_API_ERROR_RESPONSES, 201: {"model": AdaptivePreparationRecommendationResponse, "description": "Adaptive request saved for the authenticated learner."}},
)
def create_adaptive_practice_recommendation(
    learner_id: str,
    payload: AdaptivePracticeRecommendationPayload,
    request: Request,
) -> Response:
    """Persist a next-test request derived from this learner's saved outcomes.

    Existing analytics, question-pool eligibility, and adaptive composition remain
    the sources of truth; this endpoint only connects those existing contracts.
    """
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error

    analytics_provider = request.app.state.completed_test_analytics_provider
    context_provider = request.app.state.preparation_context_provider
    request_repository = request.app.state.preparation_test_request_repository
    count_eligible = getattr(context_provider, "count_eligible_questions", None)
    if (
        analytics_provider is None
        or request_repository is None
        or not callable(count_eligible)
    ):
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "ADAPTIVE_PRACTICE_NOT_CONFIGURED",
                "message": "Adaptive recommendations require learner analytics, eligible question-pool counting, and request storage.",
            }
        })

    try:
        report = analytics_provider.build_report(authenticated_learner_id)
        if not isinstance(report, Mapping) or report.get("learner_id") != authenticated_learner_id:
            raise ValueError("analytics report is outside the authenticated learner scope")
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_ANALYTICS_UNAVAILABLE",
                "message": "Saved learner performance could not be analyzed.",
            }
        })

    try:
        recommendation = AdaptivePracticeRecommendationPlanner().plan(
            authenticated_learner_id,
            report,
            max_concepts=payload.max_concepts,
        )
    except NoAdaptivePracticeSignal:
        return _json_response(HTTPStatus.CONFLICT, {
            "error": {
                "code": "NO_ADAPTIVE_PRACTICE_SIGNAL",
                "message": "Complete a test first; there is not enough saved performance or mistake history to recommend focused practice.",
            }
        })
    except (TypeError, ValueError):
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_ANALYTICS_INVALID",
                "message": "Saved learner analytics did not satisfy the recommendation contract.",
            }
        })

    try:
        available_count = count_eligible(recommendation.concept_ids)
        if (
            isinstance(available_count, bool)
            or not isinstance(available_count, int)
            or available_count < 0
        ):
            raise ValueError("eligible question count is invalid")
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "ADAPTIVE_QUESTION_POOL_UNAVAILABLE",
                "message": "Eligible verified questions could not be counted.",
            }
        })

    if available_count == 0:
        return _json_response(HTTPStatus.CONFLICT, {
            "error": {
                "code": "NO_ELIGIBLE_ADAPTIVE_QUESTIONS",
                "message": "No accepted, answer-verified, non-duplicate questions are available for the recommended concepts. Existing preparation settings were not changed.",
            }
        })

    # Match the user's request when possible; otherwise use every eligible
    # question in the bounded pool rather than inventing or duplicating items.
    effective_count = min(payload.question_count, available_count)
    request_id = uuid4().hex
    specification = TestSpecification(
        test_id=f"adaptive-{request_id}",
        title="Adaptive practice — weak topics and previous mistakes",
        question_count=effective_count,
        duration_seconds=payload.duration_seconds,
        scoring=ScoringPolicy(
            correct_marks=payload.correct_marks,
            incorrect_marks=payload.incorrect_marks,
            unattempted_marks=payload.unattempted_marks,
        ),
    )
    domain_request = PreparationTestRequest(
        learner_id=authenticated_learner_id,
        specification=specification,
        mode=PersonalizedPreparationMode.ADAPTIVE,
        concept_ids=recommendation.concept_ids,
    )
    try:
        record = request_repository.save_active(request_id, domain_request)
    except ValueError:
        return _json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {
            "error": {
                "code": "INVALID_ADAPTIVE_PREPARATION_REQUEST",
                "message": "The generated adaptive practice request was invalid.",
            }
        })
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_UNAVAILABLE",
                "message": "The recommendation was calculated but could not be saved.",
            }
        })

    response_payload = _request_record_payload(record)
    response_payload["recommendation"] = {
        "strategy": "WEAK_TOPICS_THEN_REPEATED_CONCEPTS_THEN_PREVIOUS_MISTAKES",
        "source": "PERSISTED_LEARNER_TEST_HISTORY",
        "focus_concept_ids": list(recommendation.concept_ids),
        "focus_reasons": {
            concept_id: list(reasons)
            for concept_id, reasons in recommendation.focus_reasons
        },
        "revision_question_ids": list(recommendation.revision_question_ids),
        "completed_test_count": recommendation.completed_test_count,
        "weak_topic_count": recommendation.weak_topic_count,
        "repeated_concept_count": recommendation.repeated_concept_count,
        "requested_question_count": payload.question_count,
        "eligible_question_count_in_configured_pool": available_count,
        "effective_question_count": effective_count,
        "question_count_adjusted": effective_count != payload.question_count,
        "availability_scope": "configured_eligible_pool",
    }
    return _json_response(HTTPStatus.CREATED, response_payload)


@router.get("/{learner_id}/preparation-requests/active", name="get_active_preparation_request", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": PreparationTestRequestResponse, "description": "Current saved preparation request."}})
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



@router.get("/{learner_id}/preparation-requests", name="list_preparation_requests")
def list_preparation_requests(learner_id: str, request: Request) -> Response:
    """Return bounded, learner-scoped preparation request history."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error

    try:
        query = parse_qs(request.url.query, keep_blank_values=True, strict_parsing=False)
    except ValueError:
        query = {"__invalid__": ["1"]}
    if (
        set(query) - {"limit", "offset", "status"}
        or any(len(values) != 1 for values in query.values())
    ):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {
                "code": "INVALID_REQUEST_HISTORY_QUERY",
                "message": "Only one limit, offset, and status parameter is supported.",
            }
        })
    try:
        limit = int(query.get("limit", ["50"])[0])
        offset = int(query.get("offset", ["0"])[0])
    except (TypeError, ValueError):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {
                "code": "INVALID_REQUEST_HISTORY_QUERY",
                "message": "limit and offset must be integers.",
            }
        })
    if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {
                "code": "INVALID_REQUEST_HISTORY_QUERY",
                "message": "limit must be 1-100 and offset must be 0-100000.",
            }
        })
    status = None
    if "status" in query:
        try:
            status = PreparationRequestStatus(query["status"][0])
        except ValueError:
            return _json_response(HTTPStatus.BAD_REQUEST, {
                "error": {
                    "code": "INVALID_REQUEST_STATUS",
                    "message": "status must be ACTIVE, SUPERSEDED, or CANCELLED.",
                }
            })

    repository = request.app.state.preparation_test_request_repository
    if repository is None:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_NOT_CONFIGURED",
                "message": "Preparation request storage is not configured.",
            }
        })
    try:
        records = repository.list_for_learner(
            authenticated_learner_id, limit=limit + 1, offset=offset, status=status
        )
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_UNAVAILABLE",
                "message": "Unable to load preparation request history.",
            }
        })
    selected = records[:limit]
    return _json_response(HTTPStatus.OK, {
        "items": [_request_record_payload(record) for record in selected],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "returned": len(selected),
            "has_more": len(records) > limit,
        },
    })


@router.post(
    "/{learner_id}/preparation-requests/{request_id}/activate",
    name="activate_preparation_request",
)
def activate_preparation_request(
    learner_id: str,
    request_id: str,
    request: Request,
) -> Response:
    """Reactivate a superseded request; cancelled requests are terminal."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    if not _valid_request_id(request_id):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_REQUEST_ID", "message": "Request ID format is invalid."}
        })
    repository = request.app.state.preparation_test_request_repository
    if repository is None:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_NOT_CONFIGURED",
                "message": "Preparation request storage is not configured.",
            }
        })
    try:
        record = repository.activate_for_learner(authenticated_learner_id, request_id)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_UNAVAILABLE",
                "message": "Unable to activate preparation settings.",
            }
        })
    if record is None:
        return _json_response(HTTPStatus.NOT_FOUND, {
            "error": {
                "code": "PREPARATION_REQUEST_NOT_FOUND",
                "message": "Preparation request was not found.",
            }
        })
    if record.status is PreparationRequestStatus.CANCELLED:
        return _json_response(HTTPStatus.CONFLICT, {
            "error": {
                "code": "CANCELLED_PREPARATION_REQUEST",
                "message": "Cancelled requests cannot be reactivated; create a new request.",
            }
        })
    return _json_response(HTTPStatus.OK, _request_record_payload(record))


@router.post(
    "/{learner_id}/preparation-requests/{request_id}/cancel",
    name="cancel_preparation_request",
)
def cancel_preparation_request(
    learner_id: str,
    request_id: str,
    request: Request,
) -> Response:
    """Cancel an active or historical request; repeated cancellation is idempotent."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    if not _valid_request_id(request_id):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_REQUEST_ID", "message": "Request ID format is invalid."}
        })
    repository = request.app.state.preparation_test_request_repository
    if repository is None:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_NOT_CONFIGURED",
                "message": "Preparation request storage is not configured.",
            }
        })
    try:
        record = repository.cancel_for_learner(authenticated_learner_id, request_id)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_UNAVAILABLE",
                "message": "Unable to cancel preparation settings.",
            }
        })
    if record is None:
        return _json_response(HTTPStatus.NOT_FOUND, {
            "error": {
                "code": "PREPARATION_REQUEST_NOT_FOUND",
                "message": "Preparation request was not found.",
            }
        })
    return _json_response(HTTPStatus.OK, _request_record_payload(record))



class TestSessionAnswerPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    option_key: str = Field(min_length=1, max_length=10)


def _test_result_payload(result: TestResult | None) -> dict[str, object] | None:
    if result is None:
        return None
    return {
        "test_id": result.test_id,
        "session_id": result.session_id,
        "status": result.status.value,
        "total_questions": result.total_questions,
        "attempted_questions": result.attempted_questions,
        "correct_answers": result.correct_answers,
        "incorrect_answers": result.incorrect_answers,
        "unattempted_questions": result.unattempted_questions,
        "raw_score": result.raw_score,
        "max_score": result.max_score,
        "percentage": result.percentage,
        "accuracy": result.accuracy,
        "timed_out": result.timed_out,
    }


def _test_session_payload(session: TestSession, *, remaining_seconds: float | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "session_id": session.session_id,
        "test_id": session.test_id,
        "status": session.status.value,
        "question_count": len(session.question_ids),
        "question_ids": list(session.question_ids),
        "current_question_number": session.current_index + 1,
        "answered_question_count": len(session.answers),
        "review_question_count": len(session.review_question_ids),
        "review_question_ids": list(session.review_question_ids),
        "started_at": session.started_at,
        "deadline_at": session.deadline_at,
        "submitted_at": session.submitted_at,
        "result": _test_result_payload(session.result),
    }
    if remaining_seconds is not None:
        payload["remaining_seconds"] = max(0.0, remaining_seconds)
    return payload



def _sync_finished_session_learning(
    learner_id: str,
    session: TestSession,
    record: dict[str, object],
    request: Request,
) -> Response | None:
    if session.status not in (TestSessionStatus.SUBMITTED, TestSessionStatus.EXPIRED) or session.result is None:
        return None
    recorder = request.app.state.completed_test_learning_recorder
    if recorder is None:
        return None
    try:
        recorder.record(learner_id, session, record["questions"])
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "LEARNING_HISTORY_SYNC_UNAVAILABLE",
                "message": "Test result is saved, but learner history synchronization is unavailable; retry the request.",
            }
        })
    return None


def _session_engine_for_learner(learner_id: str, session_id: str, request: Request):
    factory = request.app.state.preparation_test_session_repository_factory
    if factory is None:
        return None, None, _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_SESSION_STORE_NOT_CONFIGURED",
                "message": "Preparation session storage is not configured.",
            }
        })
    try:
        repository = factory(learner_id)
        record = repository.get_record_for_learner(session_id)
        if record is None:
            return None, None, _json_response(HTTPStatus.NOT_FOUND, {
                "error": {
                    "code": "PREPARATION_SESSION_NOT_FOUND",
                    "message": "Preparation session was not found.",
                }
            })
        engine = TestEngine(repository=repository, clock=time.time)
        engine.restore_context(record["specification"], record["questions"])
        current_session = engine.get_session(session_id)
        sync_error = _sync_finished_session_learning(learner_id, current_session, record, request)
        if sync_error is not None:
            return None, None, sync_error
        return engine, record, None
    except KeyError:
        return None, None, _json_response(HTTPStatus.NOT_FOUND, {
            "error": {
                "code": "PREPARATION_SESSION_NOT_FOUND",
                "message": "Preparation session was not found.",
            }
        })
    except Exception:
        return None, None, _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_SESSION_STORE_UNAVAILABLE",
                "message": "Unable to load preparation session.",
            }
        })


def _session_exception_response(exc: Exception) -> Response:
    message = str(exc).lower()
    if isinstance(exc, ValueError):
        invalid_answer = "option" in message
        status = HTTPStatus.UNPROCESSABLE_ENTITY if invalid_answer else HTTPStatus.CONFLICT
        code = "INVALID_TEST_ANSWER" if invalid_answer else "TEST_SESSION_STATE_CONFLICT"
        detail = (
            "Selected option is not valid for the current question."
            if invalid_answer else "The requested action is not valid for the current test state."
        )
        return _json_response(status, {"error": {"code": code, "message": detail}})
    return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
        "error": {
            "code": "PREPARATION_SESSION_UNAVAILABLE",
            "message": "The preparation session could not be updated.",
        }
    })


@router.post("/{learner_id}/preparation-sessions", status_code=201, name="create_preparation_session", responses={**COMMON_API_ERROR_RESPONSES, 201: {"model": PreparationTestSessionResponse, "description": "A persisted test session and selected-question snapshot."}})
def create_preparation_session(learner_id: str, request: Request) -> Response:
    """Create a persisted, ready-to-start session from active saved settings."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    context_provider = request.app.state.preparation_context_provider
    request_repository = request.app.state.preparation_test_request_repository
    session_factory = request.app.state.preparation_test_session_repository_factory
    if context_provider is None or request_repository is None or session_factory is None:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_SESSION_NOT_CONFIGURED",
                "message": "Preparation session creation is not configured.",
            }
        })

    try:
        active_request = request_repository.get_active_for_learner(authenticated_learner_id)
        if active_request is None or active_request.status is not PreparationRequestStatus.ACTIVE:
            return _json_response(HTTPStatus.CONFLICT, {
                "error": {
                    "code": "NO_ACTIVE_PREPARATION_REQUEST",
                    "message": "Save or activate preparation settings before creating a test.",
                }
            })
        context = context_provider.load_context(authenticated_learner_id, request=request)
        required = {
            "test_id", "title", "question_count", "duration_seconds",
            "history", "question_history", "candidates", "questions",
        }
        if not isinstance(context, Mapping) or required - set(context):
            return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
                "error": {
                    "code": "PREPARATION_CONTEXT_UNAVAILABLE",
                    "message": "Verified question and learner context is not ready.",
                }
            })
        spec = active_request.request.specification
        if context["test_id"] != spec.test_id:
            return _json_response(HTTPStatus.CONFLICT, {
                "error": {
                    "code": "PREPARATION_REQUEST_CHANGED",
                    "message": "Preparation settings changed during test creation; retry with the active request.",
                }
            })

        questions = context["questions"]
        candidates = context["candidates"]
        if not questions or not candidates:
            return _json_response(HTTPStatus.CONFLICT, {
                "error": {
                    "code": "NO_ELIGIBLE_PREPARATION_QUESTIONS",
                    "message": (
                        "No accepted, answer-verified questions are available yet. "
                        "The verified question bank must be populated before a test can start."
                    ),
                }
            })

        # A request for 20 questions should still work when only 3 accepted,
        # answer-verified, non-duplicate questions are currently available.
        # Respect exclusions before calculating the effective count, and never
        # invent or duplicate questions to fill the requested size.
        excluded_ids = set(active_request.request.exclude_question_ids)
        available_ids = {
            candidate.question_id
            for candidate in candidates
            if candidate.question_id not in excluded_ids
        }
        effective_question_count = min(spec.question_count, len(available_ids))
        if effective_question_count < 1:
            return _json_response(HTTPStatus.CONFLICT, {
                "error": {
                    "code": "NO_ELIGIBLE_PREPARATION_QUESTIONS",
                    "message": (
                        "No eligible verified questions remain for this test. "
                        "Remove exclusions or populate the verified question bank."
                    ),
                }
            })

        session_id = f"session-{uuid4().hex}"
        plan = PersonalizedPreparationService().build_plan(
            authenticated_learner_id,
            test_id=spec.test_id,
            title=spec.title,
            question_count=effective_question_count,
            duration_seconds=spec.duration_seconds,
            history=context["history"],
            question_history=context["question_history"],
            candidates=context["candidates"],
            questions=context["questions"],
            mode=active_request.request.mode,
            scoring=spec.scoring,
            shuffle_questions=spec.shuffle_questions,
            shuffle_seed=spec.shuffle_seed,
            exclude_question_ids=active_request.request.exclude_question_ids,
            as_of=active_request.request.as_of,
        )
        question_by_id = {
            question.generated_question_id: question
            for question in context["questions"]
        }
        selected_questions = tuple(
            question_by_id[question_id] for question_id in plan.question_ids
        )
        # Persist only the composed test snapshot, not the entire eligible pool.
        repository = session_factory(
            authenticated_learner_id,
            preparation_request_id=active_request.request_id,
            specification=plan.test_specification,
            questions=selected_questions,
            new_session_id=session_id,
        )
        engine = TestEngine(repository=repository, clock=time.time)
        session = engine.create_session(
            plan.test_specification,
            plan.ranked_candidates,
            selected_questions,
            session_id=session_id,
        )
        response_payload = _test_session_payload(session)
        response_payload["preparation_request_id"] = active_request.request_id
        response_payload["requested_question_count"] = spec.question_count
        response_payload["question_count_adjusted"] = effective_question_count != spec.question_count
        response_payload["mode"] = plan.mode.value
        response_payload["focus_concept_ids"] = list(plan.focus_concept_ids)
        response_payload["revision_question_ids"] = list(plan.revision_question_ids)
        return _json_response(HTTPStatus.CREATED, response_payload)
    except PreparationContextUnavailable:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_CONTEXT_UNAVAILABLE",
                "message": "Verified question and learner context is not ready.",
            }
        })
    except ValueError:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "TEST_COMPOSITION_UNAVAILABLE",
                "message": "A complete eligible question set could not be composed.",
            }
        })
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_SESSION_CREATION_FAILED",
                "message": "Unable to create a preparation session.",
            }
        })



def _session_history_item(record: dict[str, object]) -> dict[str, object]:
    session = record["session"]
    specification = record["specification"]
    return {
        "session_id": session.session_id,
        "preparation_request_id": record["preparation_request_id"],
        "test_id": session.test_id,
        "title": specification.title,
        "mode": record["mode"],
        "status": session.status.value,
        "question_count": len(session.question_ids),
        "answered_question_count": len(session.answers),
        "review_question_count": len(session.review_question_ids),
        "created_at": record["created_at"].isoformat(),
        "updated_at": record["updated_at"].isoformat(),
        "started_at": session.started_at,
        "submitted_at": session.submitted_at,
        "result": _test_result_payload(session.result),
    }


def _parse_session_history_query(request: Request):
    try:
        query = parse_qs(request.url.query, keep_blank_values=True, strict_parsing=False)
    except ValueError:
        return None, _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_SESSION_HISTORY_QUERY", "message": "Invalid history query."}
        })
    if set(query) - {"limit", "offset", "status"} or any(len(values) != 1 for values in query.values()):
        return None, _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_SESSION_HISTORY_QUERY", "message": "Only one limit, offset, and status parameter is supported."}
        })
    try:
        limit = int(query.get("limit", ["50"])[0])
        offset = int(query.get("offset", ["0"])[0])
    except (TypeError, ValueError):
        return None, _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_SESSION_HISTORY_QUERY", "message": "limit and offset must be integers."}
        })
    if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
        return None, _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_SESSION_HISTORY_QUERY", "message": "limit must be 1-100 and offset 0-100000."}
        })
    status = None
    if "status" in query:
        try:
            status = TestSessionStatus(query["status"][0])
        except ValueError:
            return None, _json_response(HTTPStatus.BAD_REQUEST, {
                "error": {"code": "INVALID_SESSION_STATUS", "message": "status must be CREATED, IN_PROGRESS, SUBMITTED, EXPIRED, or CANCELLED."}
            })
    return {"limit": limit, "offset": offset, "status": status}, None


def _learner_session_repository(learner_id: str, request: Request):
    factory = request.app.state.preparation_test_session_repository_factory
    if factory is None:
        return None, _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_SESSION_STORE_NOT_CONFIGURED",
                "message": "Preparation session storage is not configured.",
            }
        })
    try:
        return factory(learner_id), None
    except Exception:
        return None, _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_SESSION_STORE_UNAVAILABLE",
                "message": "Unable to load preparation sessions.",
            }
        })


@router.get("/{learner_id}/preparation-sessions", name="list_preparation_sessions", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": PreparationSessionHistoryResponse, "description": "Paginated learner session history."}})
def list_preparation_sessions(learner_id: str, request: Request) -> Response:
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    query, error = _parse_session_history_query(request)
    if error is not None:
        return error
    repository, error = _learner_session_repository(authenticated_learner_id, request)
    if error is not None:
        return error
    try:
        records = repository.list_for_learner(
            limit=query["limit"] + 1,
            offset=query["offset"],
            status=query["status"],
        )
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_SESSION_HISTORY_UNAVAILABLE",
                "message": "Unable to load test session history.",
            }
        })
    selected = records[:query["limit"]]
    return _json_response(HTTPStatus.OK, {
        "items": [_session_history_item(record) for record in selected],
        "pagination": {
            "limit": query["limit"],
            "offset": query["offset"],
            "returned": len(selected),
            "has_more": len(records) > query["limit"],
        },
    })


@router.get("/{learner_id}/preparation-results", name="list_preparation_results", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": PreparationSessionHistoryResponse, "description": "Paginated completed-test result history."}})
def list_preparation_results(learner_id: str, request: Request) -> Response:
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    query, error = _parse_session_history_query(request)
    if error is not None:
        return error
    if query["status"] not in (None, TestSessionStatus.SUBMITTED, TestSessionStatus.EXPIRED):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {
                "code": "INVALID_RESULT_STATUS",
                "message": "Results only support SUBMITTED or EXPIRED session status.",
            }
        })
    repository, error = _learner_session_repository(authenticated_learner_id, request)
    if error is not None:
        return error
    try:
        records = repository.list_for_learner(
            limit=query["limit"] + 1,
            offset=query["offset"],
            status=query["status"],
            results_only=True,
        )
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_RESULTS_UNAVAILABLE",
                "message": "Unable to load completed test results.",
            }
        })
    selected = records[:query["limit"]]
    return _json_response(HTTPStatus.OK, {
        "items": [_session_history_item(record) for record in selected],
        "pagination": {
            "limit": query["limit"],
            "offset": query["offset"],
            "returned": len(selected),
            "has_more": len(records) > query["limit"],
        },
    })


@router.get("/{learner_id}/preparation-results/summary", name="get_preparation_results_summary", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": PreparationResultsSummaryResponse, "description": "Aggregate saved test results."}})
def get_preparation_results_summary(learner_id: str, request: Request) -> Response:
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    repository, error = _learner_session_repository(authenticated_learner_id, request)
    if error is not None:
        return error
    try:
        summary = repository.get_history_summary()
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_RESULTS_UNAVAILABLE",
                "message": "Unable to aggregate test results.",
            }
        })
    return _json_response(HTTPStatus.OK, {
        "learner_id": authenticated_learner_id,
        **summary,
    })


@router.get("/{learner_id}/preparation-sessions/{session_id}", name="get_preparation_session", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": PreparationTestSessionResponse, "description": "Persisted session state without answer keys."}})
def get_preparation_session(learner_id: str, session_id: str, request: Request) -> Response:
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    engine, _, error = _session_engine_for_learner(authenticated_learner_id, session_id, request)
    if error is not None:
        return error
    try:
        session = engine.get_session(session_id)
        return _json_response(HTTPStatus.OK, _test_session_payload(
            session, remaining_seconds=engine.remaining_seconds(session_id)
        ))
    except Exception as exc:
        return _session_exception_response(exc)


@router.post("/{learner_id}/preparation-sessions/{session_id}/start", name="start_preparation_session", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": PreparationTestSessionResponse, "description": "Started session with remaining time."}})
def start_preparation_session(learner_id: str, session_id: str, request: Request) -> Response:
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    engine, _, error = _session_engine_for_learner(authenticated_learner_id, session_id, request)
    if error is not None:
        return error
    try:
        session = engine.start(session_id)
        return _json_response(HTTPStatus.OK, _test_session_payload(
            session, remaining_seconds=engine.remaining_seconds(session_id)
        ))
    except Exception as exc:
        return _session_exception_response(exc)


@router.get("/{learner_id}/preparation-sessions/{session_id}/current-question", name="get_preparation_session_question", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": CurrentQuestionResponse, "description": "Current question and options; answer keys are never included."}})
def get_preparation_session_question(learner_id: str, session_id: str, request: Request) -> Response:
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    engine, _, error = _session_engine_for_learner(authenticated_learner_id, session_id, request)
    if error is not None:
        return error
    try:
        session = engine.get_session(session_id)
        question = engine.current_question(session_id)
        saved_answer = next(
            (answer for answer in session.answers if answer.question_id == question.generated_question_id),
            None,
        )
        return _json_response(HTTPStatus.OK, {
            "session_id": session_id,
            "question_number": session.current_index + 1,
            "question_count": len(session.question_ids),
            "question_id": question.generated_question_id,
            "stem": question.stem,
            "options": [{"key": option.key, "text": option.text} for option in question.options],
            # Return only the learner's own saved choice, never the correct answer.
            "selected_option_key": saved_answer.selected_option_key if saved_answer is not None else None,
            "review_marked": question.generated_question_id in session.review_question_ids,
            "remaining_seconds": max(0.0, (session.deadline_at or 0.0) - time.time()),
            "source_kind": question.source_kind.value,
            "source_url": question.source_url,
            "answer_key_source_url": question.answer_key_source_url,
            "exam_name": question.exam_name,
            "exam_id": question.exam_id,
            "exam_year": question.exam_year,
            "exam_shift": question.exam_shift,
            "exam_question_number": question.exam_question_number,
            "verified_appearance_count": question.verified_appearance_count,
        })
    except Exception as exc:
        return _session_exception_response(exc)


@router.post("/{learner_id}/preparation-sessions/{session_id}/answer", name="answer_preparation_session_question", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": PreparationTestSessionResponse, "description": "Updated session state after recording a selected option."}})
def answer_preparation_session_question(
    learner_id: str, session_id: str, payload: TestSessionAnswerPayload, request: Request
) -> Response:
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    engine, _, error = _session_engine_for_learner(authenticated_learner_id, session_id, request)
    if error is not None:
        return error
    try:
        session = engine.answer(session_id, payload.option_key)
        return _json_response(HTTPStatus.OK, _test_session_payload(
            session, remaining_seconds=engine.remaining_seconds(session_id)
        ))
    except Exception as exc:
        return _session_exception_response(exc)


def _navigate_preparation_session(
    learner_id: str, session_id: str, request: Request, *, direction: str
) -> Response:
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    engine, _, error = _session_engine_for_learner(authenticated_learner_id, session_id, request)
    if error is not None:
        return error
    try:
        if direction == "next":
            session = engine.next(session_id)
        elif direction == "previous":
            session = engine.previous(session_id)
        elif direction == "review":
            session = engine.toggle_review(session_id)
        else:
            raise ValueError("unsupported navigation")
        return _json_response(HTTPStatus.OK, _test_session_payload(
            session, remaining_seconds=engine.remaining_seconds(session_id)
        ))
    except Exception as exc:
        return _session_exception_response(exc)


@router.post("/{learner_id}/preparation-sessions/{session_id}/next", name="next_preparation_session_question", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": PreparationTestSessionResponse, "description": "Updated session state after moving to the next question."}})
def next_preparation_session_question(learner_id: str, session_id: str, request: Request) -> Response:
    return _navigate_preparation_session(learner_id, session_id, request, direction="next")


@router.post("/{learner_id}/preparation-sessions/{session_id}/previous", name="previous_preparation_session_question", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": PreparationTestSessionResponse, "description": "Updated session state after moving to the previous question."}})
def previous_preparation_session_question(learner_id: str, session_id: str, request: Request) -> Response:
    return _navigate_preparation_session(learner_id, session_id, request, direction="previous")


@router.post("/{learner_id}/preparation-sessions/{session_id}/review", name="toggle_preparation_session_review", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": PreparationTestSessionResponse, "description": "Updated session state after toggling a review marker."}})
def toggle_preparation_session_review(learner_id: str, session_id: str, request: Request) -> Response:
    return _navigate_preparation_session(learner_id, session_id, request, direction="review")


@router.post("/{learner_id}/preparation-sessions/{session_id}/submit", name="submit_preparation_session", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": SubmittedTestResponse, "description": "Submitted session and persisted result."}})
def submit_preparation_session(learner_id: str, session_id: str, request: Request) -> Response:
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    engine, _, error = _session_engine_for_learner(authenticated_learner_id, session_id, request)
    if error is not None:
        return error
    try:
        result = engine.submit(session_id)
        final_session = engine.get_session(session_id)
        record = engine.repository.get_record_for_learner(session_id)
        if record is None:
            return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
                "error": {
                    "code": "PREPARATION_SESSION_STORE_UNAVAILABLE",
                    "message": "Test was saved but its snapshot could not be reloaded.",
                }
            })
        sync_error = _sync_finished_session_learning(learner_id, final_session, record, request)
        if sync_error is not None:
            return sync_error
        return _json_response(HTTPStatus.OK, {
            "session": _test_session_payload(final_session),
            "result": _test_result_payload(result),
        })
    except Exception as exc:
        return _session_exception_response(exc)


@router.get(
    "/{learner_id}/preparation-sessions/{session_id}/answer-review",
    name="get_preparation_session_answer_review",
    responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": AnswerReviewResponse, "description": "Review with correct answers, only after submission/expiry."}},
)
def get_preparation_session_answer_review(
    learner_id: str, session_id: str, request: Request
) -> Response:
    """Return the saved answer key and explanations only after test completion."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    engine, record, error = _session_engine_for_learner(
        authenticated_learner_id, session_id, request
    )
    if error is not None:
        return error

    try:
        session = engine.get_session(session_id)
        if (
            session.status not in (TestSessionStatus.SUBMITTED, TestSessionStatus.EXPIRED)
            or session.result is None
        ):
            return _json_response(HTTPStatus.CONFLICT, {
                "error": {
                    "code": "ANSWER_REVIEW_NOT_AVAILABLE",
                    "message": "Answer review is available after a test has been submitted or expires.",
                }
            })

        questions_by_id = {
            question.generated_question_id: question
            for question in record["questions"]
        }
        answers_by_id = {answer.question_id: answer for answer in session.answers}
        items: list[dict[str, object]] = []
        for index, question_id in enumerate(session.question_ids):
            question = questions_by_id.get(question_id)
            if question is None:
                return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
                    "error": {
                        "code": "PREPARATION_SESSION_SNAPSHOT_INVALID",
                        "message": "The saved question snapshot is incomplete.",
                    }
                })

            answer = answers_by_id.get(question_id)
            selected_key = answer.selected_option_key if answer is not None else None
            selected_text = (
                next((option.text for option in question.options if option.key == selected_key), None)
                if selected_key is not None else None
            )
            correct_key = question.correct_option_key
            correct_text = next(
                (option.text for option in question.options if option.key == correct_key),
                None,
            )
            outcome = (
                "UNATTEMPTED" if answer is None
                else "CORRECT" if selected_key == correct_key
                else "INCORRECT"
            )
            items.append({
                "question_number": index + 1,
                "question_id": question_id,
                "stem": question.stem,
                "options": [{"key": option.key, "text": option.text} for option in question.options],
                "selected_option_key": selected_key,
                "selected_option_text": selected_text,
                "correct_option_key": correct_key,
                "correct_option_text": correct_text,
                "outcome": outcome,
                "explanation": question.explanation,
                "fact_ids": list(question.fact_ids),
                "concept_ids": list(question.concept_ids),
                "difficulty": question.difficulty,
                "answer_verification": question.answer_verification.value,
                "answer_verification_evidence": list(question.answer_verification_evidence),
                "review_marked": question_id in session.review_question_ids,
                "answered_at_seconds": (
                    answer.answered_at_seconds if answer is not None else None
                ),
            })

        result = _test_result_payload(session.result)
        return _json_response(HTTPStatus.OK, {
            "session_id": session_id,
            "test_id": session.test_id,
            "status": session.status.value,
            "title": record["specification"].title,
            "submitted_at": session.submitted_at,
            "result": result,
            "summary": {
                "total_questions": len(items),
                "correct_answers": sum(item["outcome"] == "CORRECT" for item in items),
                "incorrect_answers": sum(item["outcome"] == "INCORRECT" for item in items),
                "unattempted_questions": sum(item["outcome"] == "UNATTEMPTED" for item in items),
            },
            "questions": items,
        })
    except Exception as exc:
        return _session_exception_response(exc)


@router.get("/{learner_id}/preparation-results/analytics", name="get_preparation_results_analytics", responses={**COMMON_API_ERROR_RESPONSES, 200: {"model": CompletedTestAnalyticsResponse, "description": "Analytics calculated from persisted learner outcomes."}})
def get_preparation_results_analytics(learner_id: str, request: Request) -> Response:
    """Return weak topics and revision priorities from persisted learner outcomes."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error

    provider = request.app.state.completed_test_analytics_provider
    if provider is None:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_ANALYTICS_NOT_CONFIGURED",
                "message": "Completed-test analytics are not configured for this server.",
            }
        })

    try:
        report = provider.build_report(authenticated_learner_id)
        if not isinstance(report, dict) or report.get("learner_id") != authenticated_learner_id:
            raise ValueError("analytics provider returned an invalid learner report")
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_ANALYTICS_UNAVAILABLE",
                "message": "Unable to calculate completed-test analytics.",
            }
        })
    return _json_response(HTTPStatus.OK, report)


@router.get(
    "/{learner_id}/question-bank/readiness",
    name="get_question_bank_readiness",
    responses={
        **COMMON_API_ERROR_RESPONSES,
        200: {
            "model": QuestionBankReadinessResponse,
            "description": "Bounded count of questions eligible for real practice tests by verified source.",
        },
    },
)
def get_question_bank_readiness(
    learner_id: str,
    request: Request,
    subject_id: str | None = None,
) -> Response:
    """Return aggregate pool counts, optionally for the selected subject."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    if subject_id is not None and (
        not subject_id.strip() or subject_id != subject_id.strip() or len(subject_id) > 200
    ):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_SUBJECT", "message": "subject_id must be trimmed and 1-200 characters."}
        })

    context_provider = request.app.state.preparation_context_provider
    readiness_provider = getattr(context_provider, "get_question_bank_readiness", None)
    if not callable(readiness_provider):
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_READINESS_NOT_CONFIGURED",
                "message": "Question-bank readiness is not configured for this server.",
            }
        })
    try:
        readiness = (
            readiness_provider()
            if subject_id is None
            else readiness_provider(subject_id=subject_id)
        )
        payload = QuestionBankReadinessResponse.model_validate({
            **readiness,
            "learner_id": authenticated_learner_id,
        }).model_dump(mode="json", exclude_none=True)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_READINESS_UNAVAILABLE",
                "message": "Eligible question counts could not be loaded.",
            }
        })
    return _json_response(HTTPStatus.OK, payload)


@content_admin_router.post(
    "/one-liners",
    status_code=201,
    name="create_topic_one_liner",
    responses={
        **COMMON_API_ERROR_RESPONSES,
        201: {"model": TopicOneLinerItem, "description": "Created or deduplicated topic-linked one-liner Q&A."},
    },
)
def create_topic_one_liner(payload: SaveTopicOneLinerPayload, request: Request) -> Response:
    """Create/update a one-liner via a separate server-side content-admin token.

    The learner Firebase token is not a content-editing permission. Configure
    AI_COMP_CONTENT_ADMIN_TOKEN as a secret on the API host; never embed it in
    the Android app or commit it to the repository.
    """
    configured_token = os.environ.get("AI_COMP_CONTENT_ADMIN_TOKEN", "").strip()
    if not configured_token:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_CONTENT_AUTHORING_NOT_CONFIGURED",
                "message": "Content authoring is not configured on this server.",
            }
        })
    supplied_token = request.headers.get("X-AI-COMP-Content-Admin-Token", "")
    if not supplied_token or not hmac.compare_digest(supplied_token, configured_token):
        return _json_response(HTTPStatus.UNAUTHORIZED, {
            "error": {
                "code": "CONTENT_ADMIN_AUTHENTICATION_REQUIRED",
                "message": "Authorized content-editor credentials are required.",
            }
        })
    connection_factory = getattr(request.app.state, "question_bank_connection_factory", None)
    if not callable(connection_factory):
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_NOT_CONFIGURED",
                "message": "The topic question bank is not configured for this server.",
            }
        })

    from datetime import datetime, timezone
    from ai_comp.database.postgres_topic_question_bank import PostgresTopicQuestionBankRepository
    from ai_comp.domain.topic_question_bank import OneLinerVerificationStatus, TopicOneLinerQA

    status = OneLinerVerificationStatus(payload.verification_status)
    item = TopicOneLinerQA(
        one_liner_id=uuid4().hex,
        concept_id=payload.concept_id,
        question_text=payload.question_text,
        answer_text=payload.answer_text,
        language_code=payload.language_code,
        source_url=payload.source_url,
        source_evidence=payload.source_evidence,
        verification_status=status,
        importance_score=payload.importance_score,
        reviewed_at=datetime.now(timezone.utc) if status is OneLinerVerificationStatus.VERIFIED else None,
    )
    connection = None
    try:
        connection = connection_factory()
        saved = PostgresTopicQuestionBankRepository(connection).save_one_liner(item)
        response_payload = TopicOneLinerItem.model_validate({
            "one_liner_id": saved.one_liner_id,
            "concept_id": saved.concept_id,
            "question_text": saved.question_text,
            "answer_text": saved.answer_text,
            "language_code": saved.language_code,
            "source_url": saved.source_url,
            "source_evidence": saved.source_evidence,
            "verification_status": saved.verification_status.value,
            "importance_score": saved.importance_score,
            "reviewed_at": saved.reviewed_at,
            "created_at": saved.created_at,
            "updated_at": saved.updated_at,
        }).model_dump(mode="json")
        return _json_response(HTTPStatus.CREATED, response_payload)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_ONE_LINER_SAVE_FAILED",
                "message": "The one-liner could not be saved. Verify the concept exists and check server-side database diagnostics.",
            }
        })
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.get(
    "/{learner_id}/question-bank/subjects",
    name="list_question_bank_subjects",
    responses={
        **COMMON_API_ERROR_RESPONSES,
        200: {"model": QuestionBankSubjectsResponse, "description": "Subjects already represented by canonical concepts."},
    },
)
def list_question_bank_subjects(learner_id: str, request: Request) -> Response:
    """List available subject labels from the existing concept taxonomy."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
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
        rows = PostgresTopicQuestionBankRepository(connection).list_subjects(limit=100, offset=0)
        payload = QuestionBankSubjectsResponse.model_validate({
            "items": [
                {"subject_id": subject, "subject_label": subject, "concept_count": count}
                for subject, count in rows
            ]
        }).model_dump(mode="json")
        return _json_response(HTTPStatus.OK, payload)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_SUBJECTS_UNAVAILABLE",
                "message": "Question-bank subjects could not be loaded.",
            }
        })
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.get(
    "/{learner_id}/question-bank/topics",
    name="list_question_bank_topics",
    responses={
        **COMMON_API_ERROR_RESPONSES,
        200: {"model": QuestionBankTopicsResponse, "description": "Bounded topic/subtopic list for a selected subject."},
    },
)
def list_question_bank_topics(
    learner_id: str,
    request: Request,
    subject: str,
    limit: int = 50,
    offset: int = 0,
) -> Response:
    """List canonical topic concepts for one selected subject."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    if not subject.strip() or subject != subject.strip() or len(subject) > 200:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_SUBJECT", "message": "subject must be trimmed and 1-200 characters."}
        })
    if exam_id is not None and (
        not exam_id.strip() or exam_id != exam_id.strip() or len(exam_id) > 128
    ):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_EXAM_ID", "message": "exam_id must be trimmed and 1-128 characters."}
        })
    if exam_year is not None and not 1900 <= exam_year <= 2200:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_EXAM_YEAR", "message": "exam_year must be between 1900 and 2200."}
        })
    if exam_shift is not None and (
        not exam_shift.strip() or exam_shift != exam_shift.strip() or len(exam_shift) > 100
    ):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_EXAM_SHIFT", "message": "exam_shift must be trimmed and 1-100 characters."}
        })
    if source_domain is not None and (
        not source_domain.strip()
        or source_domain != source_domain.strip()
        or len(source_domain) > 253
        or any(not (ch.isalnum() or ch in ".-") for ch in source_domain)
        or source_domain.startswith(".")
        or source_domain.endswith(".")
    ):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_SOURCE_DOMAIN", "message": "source_domain must be a plain domain name."}
        })
    if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_PAGINATION", "message": "limit must be 1-100 and offset 0-100000."}
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
        repository = PostgresTopicQuestionBankRepository(connection)
        rows = repository.list_topics(subject, limit=limit + 1, offset=offset)
        selected = rows[:limit]
        payload = QuestionBankTopicsResponse.model_validate({
            "items": [
                {
                    "concept_id": item.concept_id,
                    "label": item.label,
                    "subject": item.subject,
                    "topic": item.topic,
                    "subtopic": item.subtopic,
                    "verified_one_liner_count": item.verified_one_liner_count,
                }
                for item in selected
            ],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "returned": len(selected),
                "has_more": len(rows) > limit,
            },
        }).model_dump(mode="json")
        return _json_response(HTTPStatus.OK, payload)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_TOPICS_UNAVAILABLE",
                "message": "Topics for the selected subject could not be loaded.",
            }
        })
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.get(
    "/{learner_id}/question-bank/one-liners",
    name="list_topic_one_liners",
    responses={
        **COMMON_API_ERROR_RESPONSES,
        200: {"model": TopicOneLinerListResponse, "description": "Source-reviewed direct question-and-answer one-liners for one canonical topic."},
    },
)
def list_topic_one_liners(
    learner_id: str,
    request: Request,
    concept_id: str,
    language_code: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Response:
    """List only verified one-liners; Q&A are distinct from historical MCQs."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    if not concept_id.strip() or concept_id != concept_id.strip() or len(concept_id) > 128:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_CONCEPT_ID", "message": "concept_id must be trimmed and 1-128 characters."}
        })
    if language_code is not None and (
        not language_code.strip() or language_code != language_code.strip() or len(language_code) > 20
    ):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_LANGUAGE_CODE", "message": "language_code must be a trimmed language code."}
        })
    if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_PAGINATION", "message": "limit must be 1-100 and offset 0-100000."}
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
        repository = PostgresTopicQuestionBankRepository(connection)
        rows = repository.list_one_liners(
            concept_id,
            limit=limit + 1,
            offset=offset,
            verified_only=True,
            language_code=language_code,
        )
        selected = rows[:limit]
        payload = TopicOneLinerListResponse.model_validate({
            "items": [
                {
                    "one_liner_id": item.one_liner_id,
                    "concept_id": item.concept_id,
                    "question_text": item.question_text,
                    "answer_text": item.answer_text,
                    "language_code": item.language_code,
                    "source_url": item.source_url,
                    "source_evidence": item.source_evidence,
                    "verification_status": item.verification_status.value,
                    "importance_score": item.importance_score,
                    "reviewed_at": item.reviewed_at,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
                for item in selected
            ],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "returned": len(selected),
                "has_more": len(rows) > limit,
            },
        }).model_dump(mode="json")
        return _json_response(HTTPStatus.OK, payload)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_ONE_LINERS_UNAVAILABLE",
                "message": "Verified one-liners for this topic could not be loaded.",
            }
        })
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.get(
    "/{learner_id}/question-bank/previous-papers",
    name="list_verified_previous_paper_questions",
    responses={
        **COMMON_API_ERROR_RESPONSES,
        200: {"model": PreviousYearQuestionsResponse, "description": "Source-backed past-paper questions with options and verified official-key answers."},
    },
)
def list_verified_previous_paper_questions(
    learner_id: str,
    request: Request,
    concept_id: str,
    subject_id: str | None = None,
    exam_id: str | None = None,
    exam_year: int | None = None,
    exam_shift: str | None = None,
    source_domain: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Response:
    """Browse eligible official past-paper MCQs separately from one-liner Q&A."""
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
    if error is not None:
        return error
    if not concept_id.strip() or concept_id != concept_id.strip() or len(concept_id) > 128:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_CONCEPT_ID", "message": "concept_id must be trimmed and 1-128 characters."}
        })
    if subject_id is not None and (
        not subject_id.strip() or subject_id != subject_id.strip() or len(subject_id) > 200
    ):
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_SUBJECT", "message": "subject_id must be trimmed and 1-200 characters."}
        })
    if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
        return _json_response(HTTPStatus.BAD_REQUEST, {
            "error": {"code": "INVALID_PAGINATION", "message": "limit must be 1-100 and offset 0-100000."}
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
        from ai_comp.database.postgres_verified_history_question import PostgresVerifiedHistoryQuestionRepository

        connection = connection_factory()
        result_page = PostgresVerifiedHistoryQuestionRepository(connection).list_eligible_page(
            limit=limit,
            offset=offset,
            concept_ids=(concept_id,),
            subject_id=subject_id,
            exam_id=exam_id,
            exam_year=exam_year,
            exam_shift=exam_shift,
            source_domain=source_domain,
        )
        page = result_page.items
        payload = PreviousYearQuestionsResponse.model_validate({
            "items": [
                {
                    "question_id": item.generated_question_id.removeprefix("verified-history:"),
                    "stem": item.stem,
                    "options": [{"key": option.key, "text": option.text} for option in item.options],
                    "correct_option_key": item.correct_option_key,
                    "explanation": item.explanation,
                    "exam_name": item.exam_name,
                    "exam_id": item.exam_id,
                    "exam_year": item.exam_year,
                    "exam_shift": item.exam_shift,
                    "exam_question_number": item.exam_question_number,
                    "source_url": item.source_url,
                    "answer_key_source_url": item.answer_key_source_url,
                    "verified_appearance_count": item.verified_appearance_count,
                    "concept_ids": list(item.concept_ids),
                }
                for item in page
            ],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "returned": len(page),
                "total_count": result_page.total_count,
                "has_more": offset + len(page) < result_page.total_count,
            },
        }).model_dump(mode="json")
        return _json_response(HTTPStatus.OK, payload)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_PREVIOUS_PAPERS_UNAVAILABLE",
                "message": "Verified previous-paper questions for this topic could not be loaded.",
            }
        })
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


@router.post(
    "/{learner_id}/question-bank/generate-practice",
    status_code=201,
    name="generate_subject_practice",
    responses={
        **COMMON_API_ERROR_RESPONSES,
        201: {"model": TopicPracticeGenerationResponse, "description": "Generated, answer-verified subject alternatives and persisted test settings."},
    },
)
def generate_subject_practice(
    learner_id: str,
    payload: GenerateTopicPracticePayload,
    request: Request,
) -> Response:
    """Generate new MCQs from reviewed one-liners and verified past-paper answers.

    Existing questions/history are used as source evidence, never as permission
    to invent exam appearances. AI-generated alternatives remain in generated
    storage, while the past-paper store remains read-only.
    """
    authenticated_learner_id, error = _authenticated_learner_or_error(learner_id, request)
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

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_GENERATION_NOT_CONFIGURED",
                "message": "AI question generation is not configured. Add the model API key to the server's secret environment, not to the app or repository.",
            }
        })

    from ai_comp.application.topic_practice_generation import TopicPracticeAlternativeGenerator
    from ai_comp.database.postgres_generated_question import PostgresGeneratedQuestionRepository
    from ai_comp.database.postgres_verified_history_question import PostgresVerifiedHistoryQuestionRepository
    from ai_comp.domain.test_engine import ScoringPolicy, TestSpecification
    from ai_comp.domain.preparation_request import PreparationTestRequest
    from ai_comp.material.gemini import GeminiMaterialAnalysisConfig
    from ai_comp.material.gemini_generation import GeminiAnswerVerifier, GeminiQuestionGenerationProvider

    try:
        from google import genai
        config = GeminiMaterialAnalysisConfig(
            model=os.environ.get("AI_COMP_GEMINI_MODEL", "gemini-3.8-flash").strip()
            or "gemini-3.8-flash"
        )
        client = genai.Client(api_key=api_key)
        question_provider = GeminiQuestionGenerationProvider(config, client=client)
        answer_verifier = GeminiAnswerVerifier(config, client=client)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_GENERATION_NOT_CONFIGURED",
                "message": "The configured question-generation provider could not be initialized.",
            }
        })

    connection = None
    try:
        connection = connection_factory()
        bank_repository = PostgresTopicQuestionBankRepository(connection)
        topics = bank_repository.list_topics(payload.subject_id, limit=500, offset=0)
        one_liners = bank_repository.list_verified_one_liners_for_subject(
            payload.subject_id,
            limit=300,
            offset=0,
            language_code=payload.language_code,
        )
        previous_questions = PostgresVerifiedHistoryQuestionRepository(connection).list_eligible(
            limit=1000,
            concept_ids=(),
            subject_id=payload.subject_id,
        )
        existing_generated = PostgresGeneratedQuestionRepository(connection).list_accepted(
            limit=1000,
            concept_ids=(),
            subject_id=payload.subject_id,
        )
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_BANK_SOURCE_UNAVAILABLE",
                "message": "Verified topic facts and previous-paper source records could not be loaded.",
            }
        })
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()

    def persist_question(question) -> None:
        scoped_connection = connection_factory()
        try:
            PostgresGeneratedQuestionRepository(scoped_connection).save(question)
        finally:
            close_scoped = getattr(scoped_connection, "close", None)
            if callable(close_scoped):
                close_scoped()

    try:
        generator = TopicPracticeAlternativeGenerator(
            provider=question_provider,
            verifier=answer_verifier,
            persist_question=persist_question,
            max_source_facts=300,
        )
        generated = generator.generate(
            subject_id=payload.subject_id,
            requested_count=payload.question_count,
            topics=topics,
            one_liners=one_liners,
            previous_questions=previous_questions,
            existing_generated_questions=existing_generated,
        )
    except Exception:
        # Provider internals, model prompts, credentials and returned source data
        # must not be copied into a learner-facing error response.
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "QUESTION_GENERATION_FAILED",
                "message": "New MCQs could not be generated and verified. No test settings were saved; retry after checking server-side generation diagnostics.",
            }
        })

    if generated.accepted_count < 1:
        return _json_response(HTTPStatus.CONFLICT, {
            "error": {
                "code": "NO_VERIFIED_ALTERNATIVE_MCQS",
                "message": "No new MCQ passed source-answer verification, four-option validation, topic mapping and duplicate checks. The app will not fill the test with fabricated questions.",
            }
        })

    context_provider = request.app.state.preparation_context_provider
    readiness_provider = getattr(context_provider, "get_question_bank_readiness", None)
    request_repository = request.app.state.preparation_test_request_repository
    if not callable(readiness_provider) or request_repository is None:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "SUBJECT_PRACTICE_NOT_CONFIGURED",
                "message": "Subject-scoped question selection or test-request storage is not configured.",
            }
        })
    try:
        readiness = readiness_provider(subject_id=payload.subject_id)
        eligible_count = readiness.get("eligible_question_count")
        if isinstance(eligible_count, bool) or not isinstance(eligible_count, int) or eligible_count < 1:
            raise ValueError("eligible question count is empty or invalid")
    except Exception:
        return _json_response(HTTPStatus.CONFLICT, {
            "error": {
                "code": "NO_ELIGIBLE_SUBJECT_QUESTIONS",
                "message": "The selected subject has no eligible verified four-option MCQs after generation. Check topic mappings and answer verification.",
            }
        })

    effective_count = min(payload.question_count, eligible_count)
    request_id = uuid4().hex
    title = f"{payload.subject_id} practice test"
    specification = TestSpecification(
        test_id=f"topic-{request_id}",
        title=title,
        question_count=effective_count,
        duration_seconds=payload.duration_seconds,
        scoring=ScoringPolicy(
            correct_marks=1.0,
            incorrect_marks=-0.25,
            unattempted_marks=0.0,
        ),
    )
    try:
        domain_request = PreparationTestRequest(
            learner_id=authenticated_learner_id,
            specification=specification,
            mode=PersonalizedPreparationMode.MIXED,
            subject_id=payload.subject_id,
        )
        request_repository.save_active(request_id, domain_request)
    except Exception:
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_REQUEST_STORE_UNAVAILABLE",
                "message": "Generated MCQs were saved, but test settings could not be saved. Retry creating the test.",
            }
        })

    response_payload = TopicPracticeGenerationResponse.model_validate({
        "learner_id": authenticated_learner_id,
        "subject_id": payload.subject_id,
        "request_id": request_id,
        "requested_question_count": payload.question_count,
        "generated_alternative_count": generated.accepted_count,
        "eligible_question_count": eligible_count,
        "effective_question_count": effective_count,
        "duration_seconds": payload.duration_seconds,
        "one_liner_source_count": generated.one_liner_source_count,
        "previous_paper_source_count": generated.previous_paper_source_count,
        "warnings": list(generated.warnings),
        "message": "New four-option alternatives passed answer verification and were mapped to the selected subject. The test engine will use eligible questions from this subject only.",
    }).model_dump(mode="json")
    return _json_response(HTTPStatus.CREATED, response_payload)


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

    # PostgreSQL-backed context marks the actual verified-pool size. Preserve
    # injected/non-database context-provider contracts; only enforce this
    # capacity check when that explicit metadata is supplied.
    available_question_count = context.get("available_question_count")
    if (
        isinstance(available_question_count, int)
        and not isinstance(available_question_count, bool)
        and available_question_count < context["question_count"]
    ):
        return _json_response(HTTPStatus.SERVICE_UNAVAILABLE, {
            "error": {
                "code": "PREPARATION_CONTEXT_UNAVAILABLE",
                "message": "Verified question and learner context is not ready.",
            }
        })

    adapter = PreparationGuidanceHTTPAdapter(service)
    adapted = adapter.handle(
        method=request.method,
        target=target,
        authenticated_learner_id=authenticated_learner_id,
        request_context=dict(context),
    )
    return _from_adapter(adapted)


__all__ = ["get_preparation_guidance", "router"]
