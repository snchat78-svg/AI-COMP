# Phase 6.8 — Learning Recommendations and Weak-Topic Next-Test Selection

Phase 6.8 now extends the post-test analytics from diagnosis into an actionable
learning loop:

```
TestResult + TestSession
        ↓
Question Outcome
        ↓
Concept / Topic Performance
        ↓
Weak Topic Priority
        ↓
Learning Recommendation
        ↓
Weak-Topic Focused Next-Test Selection
        ↓
Phase 6.6 Ranked Candidates
        ↓
Phase 6.7 Test Engine
```

## Fixed validation issues

Two correctness gaps from the first 6.8 implementation are closed:

1. Weak-topic priority now gives unattempted questions a meaningful urgency
   contribution and remains capped at 1.0.
2. Learning analysis requires both the session and the result to be in a finished
   state: SUBMITTED or EXPIRED.

## Learning recommendations

Recommendations are deterministic and provider-neutral.

- Weak topics are already ordered by priority from the test-analysis layer.
- Up to three weak topics are surfaced by default.
- Accuracy below 0.25 recommends EASY remediation questions.
- Other weak topics recommend MEDIUM remediation questions.
- Recommendation generation does not call an AI provider and does not alter
  historical-exam data.

## Weak-topic next-test selection

The selector consumes Phase 6.6 `RankedQuestionCandidate` records and accepted
`GeneratedMCQ` records.

- The next test reserves up to 75% of its questions for weak-topic remediation.
- Weak topics are represented round-robin so a single topic does not monopolize
  the focused portion.
- A question whose difficulty matches the recommendation is preferred.
- Fresh questions from the current analysis are preferred before recently used
  questions; reuse remains possible when the pool is small.
- Remaining slots are filled using the existing Phase 6.6 selection score,
  importance, and deterministic rank/id tie-breakers.
- The selector only accepts `GeneratedQuestionStatus.ACCEPTED`.
- It returns a new deterministic ranking contract that Phase 6.7
  `TestEngine.create_session()` can consume directly.

## Boundaries

This is a decision layer over existing verified/generated data. It does not:

- create new historical exam appearances,
- mark AI-generated questions as previous-exam questions,
- ask an AI model to re-score a user's submitted answers,
- replace the Phase 6.6 intelligence formula,
- replace the Phase 6.7 test-engine scoring/session state.

Durable cross-test user learning history and long-term personalization remain a later
layer.
