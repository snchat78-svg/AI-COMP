# Phase 6.28 — Preparation Guidance API Application Boundary

## Goal

Expose the Phase 6.19/6.27 preparation guidance through a stable application-level response contract that a future HTTP controller or mobile client can consume.

## Flow

Learner request inputs + existing learning/question histories
then `AdaptiveStudyStrategyHistoryService.build_report(learner_id)`
then existing `PreparationGuidanceService.build_guidance(..., strategy_history_report=...)`
then `PreparationGuidanceAPIResponse`
then `to_payload()` for a JSON-compatible response body.

## API-facing contract

- Response envelope includes `schema_version=1.0`, learner ID, a shared timezone-aware generation timestamp, guidance, immutable strategy history, and strategy feedback.
- All dataclasses are serialized recursively; enums use stable string values and dates/times use ISO-8601.
- Unknown objects or non-string mapping keys raise `TypeError` rather than being silently converted to strings.
- A single fixed timestamp is used for history, feedback, guidance, and response consistency.
- History retrieval continues through the existing learner-scoped service, including its bounded limit and cross-learner checks.
- Question planning stays within the canonical Phase 6.11/6.19 preparation service; API integration adds no duplicate selection engine.

## Scope and limitation

This repository has no HTTP server/router or FastAPI dependency today. Therefore this phase adds the API application/use-case boundary and a transport-neutral payload contract, not a deployed URL route, authentication middleware, or frontend screen. Those should be added only with the intended HTTP/mobile transport architecture rather than introducing an unrequested framework here.

## Validation

Tests verify JSON serialization, fixed-clock consistency, empty history, question exclusions, learner scoping, and delivery of qualifying Phase 6.27 feedback in the same response.
