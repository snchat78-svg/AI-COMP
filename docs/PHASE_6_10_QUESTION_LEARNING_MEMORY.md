# Phase 6.10 — Question-Level Learning Memory, Revision and Repeated-Concept Intelligence

Phase 6.10 completes the question-level part of Master Roadmap Phase 8
(Personalized AI Preparation) on top of the durable Phase 6.9 learner history.

Flow:

```
Phase 6.7 TestResult + Phase 6.8 TestAnalysis
        ↓
Question-level learner outcome
        ↓
Durable question history
        ↓
Previous Mistakes
        ↓
Revision Candidates
        ↓
Repeated Concept Alerts
        ↓
Personalized Question Recommendations
        ↓
Revision / Next Test
        ↓
Phase 6.7 Test Engine
```

## Question-level durable memory

Each completed-test question outcome is persisted separately from the aggregate
test/topic history.

Stored evidence includes learner/session/test identity, question ID, concept IDs,
difficulty, selected option, correct option, outcome and completion time.

The outcome identity is deterministic over learner + session + question. Replaying
the same completed analysis is idempotent; conflicting data is rejected.

## Previous mistakes

A question becomes a revision candidate only after an actual learner INCORRECT outcome.
Correct and unattempted outcomes do not create a false "mistake".

Revision priority is deterministic and uses:

- mistake rate,
- consecutive mistake streak,
- repeated mistake count.

A question can remain a revision candidate after the learner later answers it
correctly; this preserves the fact that it was previously a mistake and allows a
targeted revision history.

## Repeated concept alerts

A concept alert is emitted only when:

- the concept appeared in at least two distinct tests,
- weak performance occurred in at least two tests,
- concept accuracy is below 75%.

Copied/generated question identity is not changed by this analysis; it only consumes
learner outcomes already tied to question/concept IDs.

## Personalized recommendation

The recommendation service consumes Phase 6.6 ranked candidates and Phase 6.10 learner
history.

- Personalized tests reserve up to 40% of slots for previous mistakes.
- Revision-only tests can dedicate all requested slots to prior mistakes.
- Repeated weak concepts receive priority for remaining slots.
- Phase 6.6 selection score remains the final quality signal/tie-break source.
- Candidates must be ACCEPTED generated questions.
- Current question IDs can be explicitly excluded, so a "next test" does not
  accidentally repeat the just-finished test.

No historical exam provenance is modified. No AI model is used to decide whether the
learner was right or wrong; Phase 6.7/6.8 remains the source of truth.
