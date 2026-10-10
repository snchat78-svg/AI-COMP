from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request

from ai_comp.api.dependencies import (
    LearnerIdentityProvider,
    PreparationContextProvider,
)
from ai_comp.api.preparation_guidance_routes import router
from ai_comp.application.preparation_guidance_api import PreparationGuidanceAPIService


def create_app(
    *,
    preparation_guidance_api_service: PreparationGuidanceAPIService | Any | None = None,
    learner_identity_provider: LearnerIdentityProvider | None = None,
    preparation_context_provider: PreparationContextProvider | None = None,
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

    @app.middleware("http")
    async def api_security_headers(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response

    app.include_router(router)
    return app


# Importable ASGI application. Without host-injected authentication and context,
# protected endpoints reject requests instead of accepting an untrusted identity.
app = create_app()


__all__ = ["app", "create_app"]
