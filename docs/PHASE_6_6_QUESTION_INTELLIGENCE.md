# Phase 6.6 — Difficulty + Importance Intelligence

Phase 6.6 scores **accepted generated questions** for downstream test selection.

```
Accepted Generated Questions
        ↓
Intelligence Evidence
        ↓
Difficulty Assessment
        +
Exam Importance
        +
Novelty
        +
Coverage
        ↓
Selection Score
        ↓
Ranked Question Candidates
        ↓
Phase 6.7 Test Engine
```

## Safety boundaries

- Only `GeneratedMCQ(status=ACCEPTED)` enters this stage.
- Historical frequency uses only verified appearance counts supplied by the verified
  exam-matching/history layers.
- Historical frequency is capped at ten appearances; it is evidence, not proof that a
  topic is universally important.
- Difficulty is independent from historical frequency. A frequently repeated question
  is not automatically easy or hard.
- An explicit difficulty signal can be supplied by a future AI classifier; the current
  implementation also supports deterministic EASY/MEDIUM/HARD defaults.
- Novelty and coverage are explicit inputs and are never guessed from unrelated data.
- Scores are bounded to 0..1.
- Ranking is deterministic: selection score, importance score, then question ID.
- This phase does not create exam appearances, alter master-question identity, or
  convert generated questions into historical questions.

## Importance formula

`importance = 0.40*fact_importance + 0.30*bounded_verified_frequency +
0.15*fact_confidence + 0.15*concept_confidence`

Verified appearance frequency is normalized as `min(count, 10) / 10`.

## Selection formula

`selection = 0.55*importance + 0.25*novelty + 0.20*coverage`

The resulting `RankedQuestionCandidate` is the contract that the next Test Engine
phase can consume without coupling the engine to Gemini or another AI provider.
