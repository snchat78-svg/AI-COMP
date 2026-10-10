from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request

from ai_comp.api.dependencies import (
    LearnerIdentityProvider,
    PreparationContextProvider,
)
from ai_comp.api.preparation_guidance_routes import router
from ai_comp.api.postgres_preparation_context import (
    ConnectionScopedPreparationTestRequestRepository,
    PostgresPreparationContextProvider,
    PostgresStoredPreparationTestRequestProvider,
)
from ai_comp.application.preparation_guidance_api import PreparationGuidanceAPIService


def create_app(
    *,
    preparation_guidance_api_service: PreparationGuidanceAPIService | Any | None = None,
    learner_identity_provider: LearnerIdentityProvider | None = None,
    preparation_context_provider: PreparationContextProvider | None = None,
    preparation_test_request_repository: Any | None = None,
    preparation_test_session_repository_factory: Any | None = None,
    completed_test_learning_recorder: Any | None = None,
    completed_test_analytics_provider: Any | None = None,
) -> FastAPI:
    """Create a FastAPI app with explicitly injected trusted host dependencies.

    The defaults intentionally fail closed: no authentication provider means
    protected endpoints return 401, and missing application/context wiring returns
    503. This factory does not invent an authentication scheme or learner data.
    """
    app = FastAPI(
        title="AI Competitive Exam Intelligence API",
        version="0.1.0",
        description="HTTP runtime for the AI-COMP application contracts.",
    )
    app.state.preparation_guidance_api_service = preparation_guidance_api_service
    app.state.learner_identity_provider = learner_identity_provider
    app.state.preparation_context_provider = preparation_context_provider
    app.state.preparation_test_request_repository = preparation_test_request_repository
    app.state.preparation_test_session_repository_factory = preparation_test_session_repository_factory
    app.state.completed_test_learning_recorder = completed_test_learning_recorder
    app.state.completed_test_analytics_provider = completed_test_analytics_provider

    @app.middleware("http")
    async def api_security_headers(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response

    app.include_router(router)
    return app


def create_postgres_app(
    *,
    dsn: str,
    learner_identity_provider: LearnerIdentityProvider,
    preparation_test_request_provider: Any | None = None,
    question_pool_limit: int = 5000,
) -> FastAPI:
    """Compose a database-backed API with short-lived PostgreSQL connections.

    A real authentication provider and a trusted test-request provider are required.
    The provider must resolve the learner's current TestSpecification from server-side
    state; this function deliberately does not fabricate a test or learner identity.
    """
    if not isinstance(dsn, str) or not dsn.strip():
        raise ValueError("PostgreSQL DSN is required")

    from ai_comp.analysis.adaptive_study_strategy_history import (
        AdaptiveStudyStrategyHistoryService,
    )
    from ai_comp.api.postgres_preparation_context import (
        ConnectionScopedAdaptiveStudyStrategyAuditRepository,
        PostgresPreparationContextProvider,
    )
    from ai_comp.database.connection import connect_postgres
    from ai_comp.application.completed_test_session_learning import CompletedTestSessionLearningRecorder
    from ai_comp.application.completed_test_analytics import CompletedTestAnalyticsProvider
    from ai_comp.database.postgres_preparation_session import PostgresPreparationTestSessionRepository

    connection_factory = lambda: connect_postgres(dsn)
    audit_repository = ConnectionScopedAdaptiveStudyStrategyAuditRepository(
        connection_factory
    )
    request_repository = ConnectionScopedPreparationTestRequestRepository(
        connection_factory
    )

    def session_repository_factory(
        learner_id: str,
        *,
        preparation_request_id: str | None = None,
        specification=None,
        questions=(),
        new_session_id: str | None = None,
    ):
        return PostgresPreparationTestSessionRepository(
            connection_factory,
            learner_id=learner_id,
            preparation_request_id=preparation_request_id,
            specification=specification,
            questions=questions,
            new_session_id=new_session_id,
        )
    service = PreparationGuidanceAPIService(
        strategy_history_service=AdaptiveStudyStrategyHistoryService(audit_repository)
    )
    request_provider = preparation_test_request_provider or (
        PostgresStoredPreparationTestRequestProvider(request_repository)
    )
    context_provider = PostgresPreparationContextProvider(
        connection_factory,
        request_provider,
        question_pool_limit=question_pool_limit,
    )
    return create_app(
        preparation_guidance_api_service=service,
        learner_identity_provider=learner_identity_provider,
        preparation_context_provider=context_provider,
        preparation_test_request_repository=request_repository,
        preparation_test_session_repository_factory=session_repository_factory,
        completed_test_learning_recorder=CompletedTestSessionLearningRecorder(connection_factory),
        completed_test_analytics_provider=CompletedTestAnalyticsProvider(connection_factory),
    )


# Importable ASGI application. Without host-injected authentication and context,
# protected endpoints reject requests instead of accepting an untrusted identity.
app = create_app()


__all__ = ["app", "create_app", "create_postgres_app"]
