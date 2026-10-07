# Phase 6.7 — Test Engine

Phase 6.7 converts Phase 6.6 ranked accepted questions into a real test-session
contract.

```
RankedQuestionCandidate
        ↓
Accepted GeneratedMCQ
        ↓
TestSpecification
        ↓
TestSession
        ↓
Start / Timer
        ↓
Answer + Navigation + Review
        ↓
Submit / Auto-expire
        ↓
TestResult
```

## Implemented capabilities

- Selects the highest-ranked candidates from Phase 6.6.
- Optionally shuffles the selected question order with a deterministic seed.
- Rejects rejected/non-accepted generated questions.
- Starts an explicit timed session with a deadline.
- Supports current question, next, previous, and direct question navigation.
- Supports mark-for-review toggle.
- Validates answer options against the actual MCQ options.
- Allows changing an answer before final submission.
- Applies configurable positive marks and negative marking.
- Correct, incorrect, unattempted counts are reconciled in the final result.
- Calculates raw score, max score, percentage, and attempted-question accuracy.
- Negative marking is preserved in percentage; a negative score is not silently clamped.
- Automatically converts an active session to EXPIRED when its deadline is reached.
- Submission is idempotent.
- Finished sessions cannot accept further answers.
- Uses an injectable clock for deterministic tests.

## Scoring safety

The engine scores against the stored `GeneratedMCQ.correct_option_key`; it never asks
an AI model to decide whether a submitted answer is correct.

The engine accepts only `GeneratedMCQ(status=ACCEPTED)`, so rejected/uncertain generated
content cannot silently enter a test.

Historical-exam provenance is not created or changed by the test engine. Previous-exam
questions remain governed by the verified historical pipeline.

## Current boundary

This phase keeps the repository contract provider-neutral and uses an in-memory session
repository for deterministic development/testing. Durable PostgreSQL test-session/result
storage and user-level analytics are subsequent layers.

Option shuffling is intentionally not enabled in this phase because it requires storing
an explicit option permutation; question-order randomization is supported safely.
