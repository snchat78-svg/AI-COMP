# Phase 6.30 — FastAPI Runtime and Dependency Wiring

## Goal

Mount the existing Phase 6.29 framework-neutral HTTP adapter on a real FastAPI route while preserving the Phase 6.28 JSON response contract and learner-scoping rules.

## Route

GET /api/v1/learners/{learner_id}/preparation-guidance?history_limit=50

The route passes its authenticated learner identity and trusted server-loaded context to PreparationGuidanceHTTPAdapter. It does not reimplement preparation selection, strategy feedback, history aggregation, or JSON serialization.

## Host-supplied dependencies

create_app accepts three explicit dependencies:

- preparation_guidance_api_service: the existing PreparationGuidanceAPIService.
- learner_identity_provider: a trusted callable that resolves the authenticated learner from the host's authentication/session layer.
- preparation_context_provider: an implementation that loads a learner-scoped preparation context from trusted server-side state.

No authentication mechanism exists in the current repository, so this phase does not invent a JWT, cookie, or header-based authentication scheme. An unconfigured app fails closed with 401; a missing service or context provider returns 503. The context provider must not infer identity from client-controlled inputs. Invalid provider output is not treated as a successful response, and exception details are not returned to clients.

## Runtime setup

Install the optional runtime and persistence dependencies:

    python -m pip install -e ".[server,postgres]"

The module exposes an ASGI application as ai_comp.api.app:app, and the create_app factory supports host-specific dependency injection. The default importable app is intentionally not usable for authenticated preparation until a trusted host supplies authentication and context dependencies.

A host integration should construct its configured application with existing application services, its real authentication resolver, and a context provider that loads the required test/session settings, learning history, question history, ranked candidates, and generated questions. No sample learner data or fake test questions are supplied by production code.

## Security and failure mapping

- 400: malformed learner ID, invalid/duplicate query parameters, invalid history_limit.
- 401: missing or invalid authentication.
- 403: URL learner differs from the authenticated learner.
- 404/405: unknown route or unsupported method (FastAPI routing).
- 503: server dependencies or preparation context are not configured/available.
- 500: unexpected context-provider error; internal exception details are hidden.
- API responses use JSON, Cache-Control: no-store, and X-Content-Type-Options: nosniff.

## Validation

Route tests cover successful adapter integration, authentication and learner isolation, query validation before context loading, fail-closed default configuration, missing dependencies/context, generic internal errors, and method handling. The full existing pytest suite remains part of CI.
