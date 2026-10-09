# Phase 6.17 — Adaptive Learning Feedback Loop

## Goal

Connect the completed-test feedback contract from Phase 6.16 to the adaptive composition/session services from Phases 6.14–6.15. The loop uses freshly updated learner histories to create the next personalized test.

## Flow

CompletedTestFeedback
then validate learner/session/result identity
then analyze current adaptive profile
then pass updated long-term and question histories to AdaptiveTestSessionService
then return AdaptiveLearningLoopResult with the previous result summary, weak concepts represented in the profile, adaptive decisions and next created session.

## Guarantees

- Delegates all history persistence to Phase 6.16 and existing history repositories; this phase does not duplicate or rewrite history.
- Delegates question composition and session creation to the Phase 6.14/6.15 services.
- Only a finished SUBMITTED/EXPIRED feedback snapshot can start the follow-up flow.
- Rejects mismatched learner IDs and result/session IDs.
- The next session remains CREATED; the timer only starts after an explicit start call.
- Candidate acceptance, exclusions, uniqueness, and available-pool checks remain enforced by the existing composition service.
- No database migration is introduced.

## Boundary

This orchestration expects the caller to pass the result of Phase 6.16 processing, not arbitrary client-submitted score/history data. Authentication/authorization of learner ownership remains the caller/API responsibility, as TestSession does not persist owner identity.

## Tests

- End-to-end completed feedback to next adaptive session.
- Previous score and learner identity preserved.
- Next session timer remains stopped.
- Reject wrong learner and unfinished feedback snapshots.
