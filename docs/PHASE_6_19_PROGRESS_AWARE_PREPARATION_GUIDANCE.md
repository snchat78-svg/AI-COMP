# Phase 6.19 — Progress-Aware Preparation Guidance

## Goal

Combine the Phase 6.18 learner-progress report with the established Phase 6.11 personalized preparation plan. Return a single learner-scoped response containing the next test plan and a ranked set of explainable study actions.

## Flow

Phase 6.9 learner history + Phase 6.10 question-level history
plus Phase 6.13 adaptive-difficulty/retention signals
then Phase 6.18 LearningProgressService
and Phase 6.11 PersonalizedPreparationService
then Phase 6.19 PreparationGuidanceService
then PreparationGuidance (progress report + next test + ranked actions)

## Action rules

- Previous mistakes selected by the existing preparation planner produce a revision action ranked by stored mistake priority.
- Focus concepts selected by the existing planner produce a weak-topic practice action using stored topic/recommendation priority.
- Selected questions whose spaced-review schedules are due produce a retention action.
- A declining overall test trend adds a caution to reinforce and review errors before advancing difficulty. An improving/stable trend encourages consistent, comparable practice.
- When there are too few completed tests for a trend, guidance asks for more evidence rather than guessing.
- Actions are sorted deterministically by descending priority and stable action-kind tie-breaker.

## Invariants

- Question selection remains owned by Phase 6.11 and still consumes accepted generated questions and Phase 6.6 ranked candidates.
- Progress and adaptive signals are read-only calculations over existing histories.
- Learner identity is checked across supplied histories and all returned contracts.
- No score is recalculated, no historical exam appearance is created, and no separate mutable learner state or database migration is introduced.
- Trend guidance is descriptive; different test difficulty or question composition can affect aggregate scores.

## Validation

Tests cover declining-trend integration, weak-topic/mistake/retention guidance, insufficient-data handling, deterministic action ordering, learner isolation and explicit question exclusions.
