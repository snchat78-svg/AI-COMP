# Phase 6.27 — Personalized Strategy Feedback Loop

## Goal

Use Phase 6.26's immutable adaptive-strategy history in the next preparation guidance. The new service emits a strategy-change finding only for a repeated decline pattern; it does not mutate schedules, learner history, previous audit snapshots, or question selection.

## Evidence gate

A scope must satisfy every condition below before a change-approach finding is emitted:

- At least 3 distinct assessment sessions and at least 3 recorded decisions.
- At least 2 declining decisions, with declines outnumbering improvements.
- Mean linked accuracy change of -5 percentage points or worse.
- The latest recorded action for the scope is `REINFORCE_WEAK_AREA`.

Scopes that do not qualify are not turned into a strategy-change prompt. The report counts those scopes as not actionable. These defaults are configurable through `AdaptiveStudyStrategyFeedbackPolicy`.

## Preparation-guidance integration

`PreparationGuidanceService.build_guidance` accepts an optional learner-scoped `strategy_history_report`. If a qualifying finding exists, guidance includes one ranked `REVISIT_STUDY_APPROACH` action and references its concept/question scope. Existing planning, ranking, accepted-question constraints, exclusions, progress signals, and retention logic remain canonical and unchanged. Omitting the report preserves existing behavior.

## Interpretation and safety

The text explicitly asks learners to consider a different study method and compare similar tests. It does not say the previous strategy caused the score change or that mastery was gained/lost. Strategy feedback is a read-only observation, not an automated schedule mutation or a causal estimate.

## Validation

Tests cover the evidence gate, mixed/improving patterns, configurable-policy validation, time validation, learner scoping, and integration into ranked preparation guidance without changing the planned question set.
