# Phase 6.37 — Completed-Test Analytics and Weak-Topic Priorities

## API

- GET /api/v1/learners/{learner_id}/preparation-results/analytics returns authenticated learner analytics from persisted completed-test history and question outcomes.
- summary reports completed tests, question counts, average/latest test percentage, aggregate accuracy, weak-topic count, revision-candidate count, and repeated-concept alert count.
- topic_performance includes each concept's historical and recent accuracy, performance band, trend, consecutive weak-test streak, priority score, and a rule-based next action.
- weak_topics surfaces concepts classified as WEAK by the existing learning-history service. revision_candidates comes from question-mistake history, and repeated_concept_alerts flags concepts repeatedly underperforming across tests.

## Data and behavior

- Uses LearningHistoryService and QuestionLearningHistoryService over the existing PostgreSQL repositories; no second result store or client-provided scores are introduced.
- Accuracies are available as fractions (0–1) and readable percentages (0–100). Test percentages are averaged per completed test, not weighted by question count.
- Revision candidates and repeated-concept alerts are each capped at 50 in the response; summary counts reflect the full stored histories.
- The report is read-only and calculated from saved outcomes. It does not claim causal learning gains, invent topic labels, or modify adaptive test selection.
- Learner identity is checked before analytics are loaded. Missing provider configuration and storage/analytics failures fail closed with safe 503 responses.

## Validation

PostgreSQL integration coverage verifies analytics built from a submitted test, separates one strong and one weak concept, confirms a revision candidate is returned from the recorded mistake, and rejects cross-learner access.
