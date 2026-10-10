# Phase 6.29 — HTTP Transport Adapter

## Endpoint contract

`GET /api/v1/learners/{learner_id}/preparation-guidance?history_limit=50`

The framework-neutral `PreparationGuidanceHTTPAdapter` wraps the Phase 6.28 application service and returns a JSON HTTP response. It supports a GET-only read route, JSON errors, no-store caching and `nosniff`.

## Authentication and learner isolation

The host authenticates the caller and passes the verified learner identity through `authenticated_learner_id`. The adapter rejects missing identity (401) and requested/authorized learner mismatches (403). Never derive this argument from the URL, query string or client-controlled body. This class is a transport adapter, not an authentication provider.

## Preparation context

The caller supplies existing preparation context via `request_context`: test ID/title, question count/duration, learner learning history, question history, ranked candidates and generated questions. Optional canonical settings may also be supplied. Missing context returns 400 rather than inventing or silently loading data.

Only `history_limit` is accepted, at most once, in the range 1–500. Unknown routes return 404, other methods 405, invalid IDs/queries/context 400. Unexpected internal errors return a generic 500 without exception details.

## Deployment boundary

No FastAPI/Starlette/ASGI runtime currently exists in the repository. This phase supplies a tested framework-neutral HTTP adapter that a future server can mount. It does not claim a public/deployed URL, nor does it implement authentication, request-context persistence/loading, or frontend integration.

## Validation

Tests cover successful JSON delivery, headers, route and method matching, auth and learner-scope checks, query/context validation, and safe handling of internal errors.
