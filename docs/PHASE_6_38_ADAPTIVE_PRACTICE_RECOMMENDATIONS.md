# Phase 6.38 — Adaptive Practice Recommendations

## Scope and reuse

This phase connects persisted Phase 6.37 analytics to the existing preparation-request and adaptive session flow. It does not add a second analytics store, question composer, learning-history pipeline, or database migration.

- Phase 6.37 CompletedTestAnalyticsProvider remains the source for saved test performance, weak topics, repeated-concept alerts, and revision candidates.
- The new planner ranks focus concepts from those persisted signals: weak topics first, then repeated concepts, then concepts attached to prior mistakes. Declining trends are retained as explicit reasons.
- PostgresPreparationContextProvider counts the same accepted, answer-verified, non-duplicate, supported-difficulty questions that session composition is allowed to use.
- The existing PersonalizedPreparationService / Phase 6.14 adaptive composition still chooses the actual questions, including retention-due questions, mistake questions, remediation, advancement, concept coverage, and ranking.
- PostgresPreparationTestRequestRepository saves the derived request as active only after analytics and eligible-pool checks succeed.

## API

POST /api/v1/learners/{learner_id}/preparation-recommendations

Body fields are optional; defaults are question_count=20, duration_seconds=1800, correct_marks=1.0, incorrect_marks=-0.25, unattempted_marks=0, and max_concepts=8. Bounds match the current preparation-request/test contracts. Unknown fields are rejected.

On success the response includes the saved active preparation request plus:
- focus_concept_ids and focus_reasons
- revision_question_ids that overlap selected focus concepts
- test-history summary counts
- requested, eligible-in-configured-pool, and effective question counts
- question_count_adjusted when fewer questions are eligible than requested

The following normal workflow creates a session from the saved recommendation:
1. POST /api/v1/learners/{learner_id}/preparation-recommendations
2. POST /api/v1/learners/{learner_id}/preparation-sessions
3. Start/answer/submit through the existing session endpoints
4. Read saved results and analytics through Phase 6.35–6.37 endpoints

## Safety and correctness

- Authentication and learner-scope checks occur before reading analytics or counting questions.
- Analytics must identify the authenticated learner; arbitrary client-supplied scores/history are not accepted.
- Only concepts with recorded need signals are selected. If no weak, repeated, declining, or prior-mistake signal exists, the endpoint returns 409 NO_ADAPTIVE_PRACTICE_SIGNAL.
- If there are no eligible questions, the endpoint returns 409 NO_ELIGIBLE_ADAPTIVE_QUESTIONS. In both conflict cases the previous active preparation request is not superseded.
- When the configured eligible pool has fewer questions than requested, the persisted request uses the available unique count and transparently reports the adjustment.
- Pool availability is bounded by question_pool_limit; it is not represented as a count of every question that might exist outside the configured pool.
- Session creation independently reloads persisted learner history and repeats eligibility checks. The recommendation response does not reveal answer keys or assert unverified exam appearances.
- No migration is introduced.

## Tests

Unit/API tests cover deterministic focus ordering and reasons, previous-mistake retention, no-signal behavior, count capping, no-write failure paths, provider fail-closed behavior, and learner-scope isolation.
