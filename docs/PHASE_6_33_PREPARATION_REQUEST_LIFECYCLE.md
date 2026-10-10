# Phase 6.33 — Preparation Request History and Lifecycle

## Goal

Complete the persisted Phase 6.32 request lifecycle: learners can inspect prior settings, reactivate a superseded request, and cancel an active or historical request. No migration is required; the phase uses migration 0015 and its existing status/index contract.

## API

- `GET /api/v1/learners/{learner_id}/preparation-requests?limit=50&offset=0&status=ACTIVE` lists requests owned by the authenticated learner. `limit` is 1–100, `offset` is 0–100000, and `status` is optional (`ACTIVE`, `SUPERSEDED`, or `CANCELLED`). Responses include `items` and bounded pagination metadata.
- `POST /api/v1/learners/{learner_id}/preparation-requests/{request_id}/activate` reactivates a superseded request, atomically superseding the current active request.
- `POST /api/v1/learners/{learner_id}/preparation-requests/{request_id}/cancel` cancels a request. Repeating cancellation is idempotent.
- Existing POST-create and GET-active endpoints continue to work unchanged.

## State rules

- At most one request per learner is `ACTIVE` (database partial unique index).
- `ACTIVE → SUPERSEDED` occurs when another request is created or a previous request is activated.
- `ACTIVE → CANCELLED` and `SUPERSEDED → CANCELLED` are allowed.
- `SUPERSEDED → ACTIVE` is allowed through the explicit activate endpoint.
- `CANCELLED` is terminal; activation returns HTTP 409. A learner must create a new request rather than reviving cancelled settings.
- Missing request IDs return 404, invalid history filters return 400, learner-scope mismatches return 403, and repository failures use generic 503 responses.
- Lifecycle mutations and request creation share the same PostgreSQL table lock and transaction boundary, preventing two concurrent lifecycle writers from leaving multiple active requests. The repository filters every read/mutation by both authenticated learner ID and request ID.

## Validation

Unit-level FastAPI tests cover learner scope, history query validation, pagination, filtering, activation, idempotent cancellation, and the terminal cancelled state. PostgreSQL integration coverage verifies persisted status transitions against the real repository and migration 0015.
