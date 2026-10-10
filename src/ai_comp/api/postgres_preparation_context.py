from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any, Protocol

from fastapi import Request

from ai_comp.analysis.adaptive_study_strategy_history import AdaptiveStudyStrategyHistoryService
from ai_comp.analysis.learning_history import LearningHistoryService
from ai_comp.analysis.question_learning import QuestionLearningHistoryService
from ai_comp.api.dependencies import PreparationContextUnavailable
from ai_comp.database.postgres_adaptive_study_strategy_audit import (
    PostgresAdaptiveStudyStrategyAuditRepository,
)
from ai_comp.database.postgres_generated_question import PostgresGeneratedQuestionRepository
from ai_comp.database.postgres_learning_history import PostgresLearningHistoryRepository
from ai_comp.database.postgres_question_learning import PostgresQuestionLearningHistoryRepository
from ai_comp.database.postgres_preparation_test_request import PostgresPreparationTestRequestRepository
from ai_comp.domain.preparation_request import PreparationTestRequest
from ai_comp.domain.adaptive_study_strategy_audit import AdaptiveStudyStrategyAudit
from ai_comp.domain.material_generation import GeneratedMCQ
from ai_comp.domain.personalized_preparation import PersonalizedPreparationMode
from ai_comp.domain.question_intelligence import (
    DifficultyLevel,
    QuestionIntelligenceInput,
    RankedQuestionCandidate,
)
from ai_comp.domain.test_engine import TestSpecification
from ai_comp.material.intelligence import QuestionIntelligenceService


ConnectionFactory = Callable[[], Any]




class ConnectionScopedPreparationTestRequestRepository:
    """Repository facade which opens and closes a PostgreSQL connection per call."""

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def _run(self, operation: str, *args: Any, **kwargs: Any) -> Any:
        connection = self._connection_factory()
        try:
            repository = PostgresPreparationTestRequestRepository(connection)
            return getattr(repository, operation)(*args, **kwargs)
        finally:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

    def save_active(self, request_id: str, request: PreparationTestRequest):
        return self._run("save_active", request_id, request)

    def get_active_for_learner(self, learner_id: str):
        return self._run("get_active_for_learner", learner_id)

    def get_for_learner(self, learner_id: str, request_id: str):
        return self._run("get_for_learner", learner_id, request_id)

    def list_for_learner(
        self,
        learner_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
        status=None,
    ):
        return self._run(
            "list_for_learner", learner_id, limit=limit, offset=offset, status=status
        )

    def activate_for_learner(self, learner_id: str, request_id: str):
        return self._run("activate_for_learner", learner_id, request_id)

    def cancel_for_learner(self, learner_id: str, request_id: str):
        return self._run("cancel_for_learner", learner_id, request_id)


class PostgresStoredPreparationTestRequestProvider:
    """Reads durable active settings instead of trusting client-supplied context."""

    def __init__(self, repository: ConnectionScopedPreparationTestRequestRepository) -> None:
        self._repository = repository

    def load_request(self, learner_id: str, *, request: Request) -> PreparationTestRequest:
        record = self._repository.get_active_for_learner(learner_id)
        if record is None:
            raise PreparationContextUnavailable("learner has not saved a preparation request")
        if record.request.learner_id != learner_id or record.status.value != "ACTIVE":
            raise PreparationContextUnavailable("stored preparation request is outside learner scope")
        return record.request

class PreparationTestRequestProvider(Protocol):
    """Resolve a current test request from trusted server-side application state."""

    def load_request(
        self,
        learner_id: str,
        *,
        request: Request,
    ) -> PreparationTestRequest: ...


class ConnectionScopedAdaptiveStudyStrategyAuditRepository:
    """Open a short-lived connection for each audit repository operation.

    PreparationGuidanceAPIService can safely outlive individual HTTP requests
    without holding a closed or process-global PostgreSQL connection.
    """

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def _run(self, operation: str, *args: Any, **kwargs: Any) -> Any:
        connection = self._connection_factory()
        try:
            repository = PostgresAdaptiveStudyStrategyAuditRepository(connection)
            return getattr(repository, operation)(*args, **kwargs)
        finally:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

    def get_audit(self, audit_id: str) -> AdaptiveStudyStrategyAudit | None:
        return self._run("get_audit", audit_id)

    def save_audit(self, audit: AdaptiveStudyStrategyAudit) -> AdaptiveStudyStrategyAudit:
        return self._run("save_audit", audit)

    def list_for_learner(
        self,
        learner_id: str,
        *,
        limit: int = 50,
    ) -> tuple[AdaptiveStudyStrategyAudit, ...]:
        return self._run("list_for_learner", learner_id, limit=limit)


class PostgresPreparationContextProvider:
    """Build preparation context from learner-scoped PostgreSQL records.

    Question test settings come from a trusted host-provided request source.
    Accepted, answer-verified generated questions and learner history are loaded
    from PostgreSQL; ranking is delegated to the canonical QuestionIntelligenceService.
    """

    def __init__(
        self,
        connection_factory: ConnectionFactory,
        test_request_provider: PreparationTestRequestProvider,
        *,
        question_pool_limit: int = 5000,
        intelligence_service: QuestionIntelligenceService | None = None,
    ) -> None:
        if (
            isinstance(question_pool_limit, bool)
            or not isinstance(question_pool_limit, int)
            or not 1 <= question_pool_limit <= 10000
        ):
            raise ValueError("question_pool_limit must be between 1 and 10000")
        self._connection_factory = connection_factory
        self._test_request_provider = test_request_provider
        self.question_pool_limit = question_pool_limit
        self._intelligence_service = intelligence_service or QuestionIntelligenceService()

    def load_context(
        self,
        learner_id: str,
        *,
        request: Request,
    ) -> dict[str, Any]:
        if not learner_id.strip():
            raise ValueError("learner_id is required")

        test_request = self._test_request_provider.load_request(
            learner_id,
            request=request,
        )
        if not isinstance(test_request, PreparationTestRequest):
            raise PreparationContextUnavailable(
                "trusted test request provider returned no valid test request"
            )
        if test_request.learner_id != learner_id:
            raise PreparationContextUnavailable(
                "test request does not belong to the authenticated learner"
            )

        connection = self._connection_factory()
        try:
            with connection.transaction():
                learning_history = LearningHistoryService(
                    PostgresLearningHistoryRepository(connection)
                ).history(learner_id)
                question_history = QuestionLearningHistoryService(
                    PostgresQuestionLearningHistoryRepository(connection)
                ).history(learner_id)
                stored_questions = PostgresGeneratedQuestionRepository(
                    connection
                ).list_accepted(
                    limit=self.question_pool_limit,
                    concept_ids=test_request.concept_ids,
                )
        finally:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

        questions, candidates = self._rank_accepted_questions(
            stored_questions,
            target_concept_ids=test_request.concept_ids,
        )
        if len(candidates) < test_request.specification.question_count:
            raise PreparationContextUnavailable(
                "the accepted verified question pool is smaller than the requested test"
            )

        specification = test_request.specification
        return {
            "test_id": specification.test_id,
            "title": specification.title,
            "question_count": specification.question_count,
            "duration_seconds": specification.duration_seconds,
            "history": learning_history,
            "question_history": question_history,
            "candidates": candidates,
            "questions": questions,
            "mode": test_request.mode,
            "scoring": specification.scoring,
            "shuffle_questions": specification.shuffle_questions,
            "shuffle_seed": specification.shuffle_seed,
            "exclude_question_ids": test_request.exclude_question_ids,
            "as_of": test_request.as_of,
        }

    def _rank_accepted_questions(
        self,
        stored_questions: Sequence[GeneratedMCQ],
        *,
        target_concept_ids: tuple[str, ...],
    ) -> tuple[tuple[GeneratedMCQ, ...], tuple[RankedQuestionCandidate, ...]]:
        scoreable: list[GeneratedMCQ] = []
        evidence_by_question: dict[str, QuestionIntelligenceInput] = {}
        target_ids = set(target_concept_ids)

        for question in stored_questions:
            if question.status.value != "ACCEPTED":
                continue
            if question.answer_verification.value != "VERIFIED":
                continue
            if question.duplicate_of_master_question_id is not None:
                continue
            try:
                difficulty = DifficultyLevel(question.difficulty.strip().upper())
            except ValueError:
                # Unsupported stored difficulty metadata cannot enter a test.
                continue

            matched_concepts = target_ids.intersection(question.concept_ids)
            coverage = (
                len(matched_concepts) / len(target_ids)
                if target_ids
                else 0.0
            )
            scoreable.append(question)
            evidence_by_question[question.generated_question_id] = QuestionIntelligenceInput(
                generated_question_id=question.generated_question_id,
                requested_difficulty=difficulty,
                # Stored question importance is real evidence. Confidence and
                # verified historical appearances are not inferred where absent.
                fact_importance_scores=(question.importance_score,),
                verified_appearance_count=0,
                novelty_score=1.0,
                coverage_score=coverage,
            )

        if not scoreable:
            return (), ()
        candidates = self._intelligence_service.rank(
            scoreable,
            evidence_by_question,
        )
        return tuple(scoreable), candidates


__all__ = [
    "ConnectionScopedAdaptiveStudyStrategyAuditRepository",
    "PreparationTestRequest",
    "PreparationTestRequestProvider",
    "PostgresPreparationContextProvider",
]
