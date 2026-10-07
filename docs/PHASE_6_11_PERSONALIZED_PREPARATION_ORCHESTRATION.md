# Phase 6.11 — Personalized Preparation Orchestration

Phase 6.11 completes the orchestration layer for Master Roadmap Phase 8 by composing
the existing learning signals instead of replacing them.

Flow:

Phase 6.9 long-term topic history
+
Phase 6.10 question-level mistakes
+
Phase 6.8 current weak-topic signals
+
Phase 6.6 ranked candidates
+
Phase 6.7 Test Engine
=
PersonalizedPreparationService

Policy:

1. Adaptive mode gives up to 40% of the requested test to previous mistakes when
   eligible ranked candidates exist.
2. The remaining capacity gives up to 75% of its slots to long-term or current weak
   concepts.
3. Remaining slots use Phase 6.6 selection score, importance, novelty and deterministic
   tie-breakers.
4. The just-completed test questions are excluded automatically when current analysis
   is supplied.
5. Explicit question exclusions are also honored.

Modes:

- ADAPTIVE: combines mistakes and weak concepts automatically.
- REVISION: prioritizes previous mistakes for the requested number of questions.
- WEAK_TOPICS: focuses on weak concepts and falls back to general ranking when needed.
- MIXED: explicitly combines revision-first and weak-topic selection.

Adaptive difficulty:

The highest-priority learning recommendation determines the plan difficulty. Very low
recent or long-term accuracy recommends EASY remediation; other weak recommendations
recommend MEDIUM. Difficulty is a preference during focused selection and never overrides
the accepted-question contract or Phase 6.6 candidate ranking.

Integration:

PersonalizedPreparationPlan returns a real TestSpecification plus ranked candidates.
The caller can pass those objects directly to Phase 6.7 TestEngine.create_session().
The orchestrator itself does not score answers, modify exam history, change verification,
or call an AI provider.

Safety:

Only ACCEPTED generated questions are selected. Histories are strictly learner-scoped.
Current-test questions cannot silently leak into the next test. No historical provenance
is created or modified by personalization.
