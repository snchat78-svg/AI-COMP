# Phase 6.39 — End-to-End Adaptive Preparation Loop Verification

## Goal

Verify the whole persisted learner feedback loop against PostgreSQL without creating another analytics service, question composer, request repository, session store, or migration.

## Verified workflow

The integration test in tests/test_postgres_preparation_sessions.py exercises one learner through this sequence:

1. Save verified, accepted fixture questions and create a baseline practice request.
2. Create, start, answer, and submit a persisted test with known incorrect answers.
3. Read Phase 6.37 analytics and confirm the weak-topic and previous-mistake signals came from the saved result.
4. Call POST /api/v1/learners/{learner_id}/preparation-recommendations.
5. Confirm the recommendation is ADAPTIVE, focuses on the persisted weak concept, includes revision-question evidence, and is now the active saved request.
6. Create a second session through the ordinary preparation-sessions endpoint; confirm it uses the recommended request.
7. Submit the second session and confirm the result appears in persisted analytics, with completed-test and question-outcome counts incremented.
8. Confirm a different authenticated learner cannot use the first learner's recommendation endpoint.

## Existing components reused

- CompletedTestAnalyticsProvider and existing learning-history/question-learning repositories.
- AdaptivePracticeRecommendationPlanner from Phase 6.38.
- PostgresPreparationContextProvider and QuestionIntelligenceService for eligible verified questions.
- PersonalizedPreparationService / the existing adaptive composition workflow.
- Existing persisted request/session/result repositories and completed-test recorder.

## Data and safety checks

- The test uses uniquely named, verified fixture questions and cleans up all learner-scoped test data in a finally block.
- Results and analytics are checked through API responses and direct row counts, proving that reading analytics does not fabricate new attempts and that a new submission is persisted.
- Learner isolation is asserted at the API boundary.
- No client-supplied scores or learning history are used; the recommendation is based on saved outcomes.
- No database migration or production behavior change is required for this verification phase.

## Limits

A passing CI integration test proves this specific PostgreSQL-backed loop and fixture contract. It does not establish production deployment, broad official-exam coverage, complete source/OCR accuracy, or improved learning outcomes. Flutter/client integration remains a separate end-to-end target.
