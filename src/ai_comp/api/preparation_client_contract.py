from __future__ import annotations

"""Stable response models used by OpenAPI and adaptive-preparation clients."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class APIErrorDetail(ContractModel):
    code: str
    message: str


class APIErrorResponse(ContractModel):
    error: APIErrorDetail


class ScoringContract(ContractModel):
    correct_marks: float
    incorrect_marks: float
    unattempted_marks: float


class PreparationTestRequestResponse(ContractModel):
    request_id: str
    learner_id: str
    status: Literal["ACTIVE", "SUPERSEDED", "CANCELLED"]
    test_id: str
    title: str
    question_count: int = Field(ge=1)
    duration_seconds: int = Field(ge=1)
    scoring: ScoringContract
    mode: Literal["ADAPTIVE", "REVISION", "WEAK_TOPICS", "MIXED"]
    concept_ids: list[str]
    exclude_question_ids: list[str]
    shuffle_questions: bool
    shuffle_seed: int | None
    exam_id: str | None
    subject_id: str | None
    created_at: datetime
    updated_at: datetime


class AdaptiveRecommendationDetails(ContractModel):
    strategy: Literal["WEAK_TOPICS_THEN_REPEATED_CONCEPTS_THEN_PREVIOUS_MISTAKES"]
    source: Literal["PERSISTED_LEARNER_TEST_HISTORY"]
    focus_concept_ids: list[str]
    focus_reasons: dict[str, list[str]]
    revision_question_ids: list[str]
    completed_test_count: int = Field(ge=0)
    weak_topic_count: int = Field(ge=0)
    repeated_concept_count: int = Field(ge=0)
    requested_question_count: int = Field(ge=1)
    eligible_question_count_in_configured_pool: int = Field(ge=0)
    effective_question_count: int = Field(ge=1)
    question_count_adjusted: bool
    availability_scope: Literal["configured_accepted_question_pool"]


class AdaptivePreparationRecommendationResponse(PreparationTestRequestResponse):
    recommendation: AdaptiveRecommendationDetails


class TestResultResponse(ContractModel):
    test_id: str
    session_id: str
    status: Literal["SUBMITTED", "EXPIRED"]
    total_questions: int = Field(ge=1)
    attempted_questions: int = Field(ge=0)
    correct_answers: int = Field(ge=0)
    incorrect_answers: int = Field(ge=0)
    unattempted_questions: int = Field(ge=0)
    raw_score: float
    max_score: float
    percentage: float = Field(ge=0, le=100)
    accuracy: float = Field(ge=0, le=1)
    timed_out: bool


class PreparationTestSessionResponse(ContractModel):
    session_id: str
    test_id: str
    status: Literal["CREATED", "IN_PROGRESS", "SUBMITTED", "EXPIRED", "CANCELLED"]
    question_count: int = Field(ge=1)
    question_ids: list[str]
    current_question_number: int = Field(ge=1)
    answered_question_count: int = Field(ge=0)
    review_question_count: int = Field(ge=0)
    review_question_ids: list[str]
    started_at: float | None
    deadline_at: float | None
    submitted_at: float | None
    result: TestResultResponse | None
    remaining_seconds: float | None = None
    preparation_request_id: str | None = None
    mode: Literal["ADAPTIVE", "REVISION", "WEAK_TOPICS", "MIXED"] | None = None
    focus_concept_ids: list[str] = Field(default_factory=list)
    revision_question_ids: list[str] = Field(default_factory=list)


class QuestionOptionResponse(ContractModel):
    key: str
    text: str


class CurrentQuestionResponse(ContractModel):
    session_id: str
    question_number: int = Field(ge=1)
    question_count: int = Field(ge=1)
    question_id: str
    stem: str
    options: list[QuestionOptionResponse]
    selected_option_key: str | None = None
    review_marked: bool
    remaining_seconds: float = Field(ge=0)


class SubmittedTestResponse(ContractModel):
    session: PreparationTestSessionResponse
    result: TestResultResponse


class PaginationResponse(ContractModel):
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    returned: int = Field(ge=0)
    has_more: bool


class PreparationSessionHistoryItem(ContractModel):
    session_id: str
    preparation_request_id: str
    test_id: str
    title: str
    mode: Literal["ADAPTIVE", "REVISION", "WEAK_TOPICS", "MIXED"]
    status: Literal["CREATED", "IN_PROGRESS", "SUBMITTED", "EXPIRED", "CANCELLED"]
    question_count: int = Field(ge=1)
    answered_question_count: int = Field(ge=0)
    review_question_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    started_at: float | None
    submitted_at: float | None
    result: TestResultResponse | None


class PreparationSessionHistoryResponse(ContractModel):
    items: list[PreparationSessionHistoryItem]
    pagination: PaginationResponse


class PreparationResultsSummaryResponse(ContractModel):
    learner_id: str
    total_session_count: int = Field(ge=0)
    completed_test_count: int = Field(ge=0)
    average_percentage: float = Field(ge=0, le=100)
    best_percentage: float = Field(ge=0, le=100)
    total_questions: int = Field(ge=0)
    attempted_questions: int = Field(ge=0)
    correct_answers: int = Field(ge=0)
    incorrect_answers: int = Field(ge=0)
    unattempted_questions: int = Field(ge=0)


class CompletedTestAnalyticsResponse(ContractModel):
    schema_version: Literal["1.0"]
    learner_id: str
    generated_at: datetime
    summary: dict[str, Any]
    topic_performance: list[dict[str, Any]]
    weak_topics: list[dict[str, Any]]
    revision_candidates: list[dict[str, Any]]
    repeated_concept_alerts: list[dict[str, Any]]
    limits: dict[str, Any]


class AnswerReviewQuestionResponse(ContractModel):
    question_number: int = Field(ge=1)
    question_id: str
    stem: str
    options: list[QuestionOptionResponse]
    selected_option_key: str | None
    selected_option_text: str | None
    correct_option_key: str
    correct_option_text: str | None
    outcome: Literal["CORRECT", "INCORRECT", "UNATTEMPTED"]
    explanation: str
    fact_ids: list[str]
    concept_ids: list[str]
    difficulty: str
    answer_verification: str
    answer_verification_evidence: list[str]
    review_marked: bool
    answered_at_seconds: float | None


class AnswerReviewSummaryResponse(ContractModel):
    total_questions: int = Field(ge=1)
    correct_answers: int = Field(ge=0)
    incorrect_answers: int = Field(ge=0)
    unattempted_questions: int = Field(ge=0)


class AnswerReviewResponse(ContractModel):
    session_id: str
    test_id: str
    status: Literal["SUBMITTED", "EXPIRED"]
    title: str
    submitted_at: float | None
    result: TestResultResponse
    summary: AnswerReviewSummaryResponse
    questions: list[AnswerReviewQuestionResponse]


COMMON_API_ERROR_RESPONSES = {
    400: {"model": APIErrorResponse, "description": "Invalid path or query parameters."},
    401: {"model": APIErrorResponse, "description": "Authentication is required."},
    403: {"model": APIErrorResponse, "description": "Authenticated learner scope does not match."},
    404: {"model": APIErrorResponse, "description": "Resource was not found for this learner."},
    409: {"model": APIErrorResponse, "description": "The requested action conflicts with current state."},
    500: {"model": APIErrorResponse, "description": "The request could not be completed."},
    503: {"model": APIErrorResponse, "description": "A required service or storage provider is unavailable."},
}


__all__ = [
    "APIErrorDetail",
    "APIErrorResponse",
    "AdaptiveRecommendationDetails",
    "AdaptivePreparationRecommendationResponse",
    "AnswerReviewResponse",
    "COMMON_API_ERROR_RESPONSES",
    "CompletedTestAnalyticsResponse",
    "CurrentQuestionResponse",
    "PreparationResultsSummaryResponse",
    "PreparationSessionHistoryResponse",
    "PreparationTestRequestResponse",
    "PreparationTestSessionResponse",
    "SubmittedTestResponse",
]
