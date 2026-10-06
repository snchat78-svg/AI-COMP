# Phase 5.1 — Master Question Identity

## Purpose

Phase 5.1 converts independently extracted observed questions into a canonical **MasterQuestion** identity.

An observed question remains separate from the master. The master is an equivalence class used by the future question bank, test generator and analytics layers.

## Master identity rule

An observed question may join an existing master only through a historical-equivalent relationship:

- EXACT
- REPHRASED

These relationships are persisted as master memberships:

- CANONICAL
- EXACT
- REPHRASED

The following relationships never create master identity equivalence:

- SAME_CONCEPT
- RELATED_TOPIC
- NO_MATCH

This preserves the distinction between same question and same concept/topic.

## Safe assignment policy

`MasterQuestionService` applies these rules:

1. An already-assigned question is not reassigned.
2. EXACT is stronger than REPHRASED.
3. REPHRASED requires the configured minimum confidence.
4. When multiple REPHRASED masters compete, the leading confidence must exceed the runner-up by the configured margin.
5. Two competing EXACT masters are always ambiguous.
6. A retired or merged master is not used for automatic assignment.
7. When no safe existing master is available, a new master is created using the observed question as its canonical member.
8. Ambiguity is returned explicitly instead of guessing.

Default policy:

- minimum REPHRASED confidence: 0.90
- minimum confidence margin: 0.05

## Persistence integrity

`database/migrations/0005_phase5_master_questions.sql` creates:

- `master_questions`
- `master_question_options`
- `master_question_memberships`

Database rules ensure:

- one observed question belongs to at most one master;
- one canonical question is owned by at most one master;
- master status is valid;
- MERGED masters point to another master;
- a master cannot point to itself;
- membership relationship is limited to CANONICAL/EXACT/REPHRASED.

## Canonical presentation

The first newly-created master uses the current observed question as its canonical presentation.

Phase 5.1 does not automatically promote a later secondary or rephrased source into the canonical presentation. Source authority promotion is a separate later step.

## Boundary

This phase does not yet:

- merge two existing master records;
- repair wrongly assigned questions;
- generate AI questions;
- select practice questions;
- calculate user performance;
- claim that the master appeared in all government examinations.

## Phase 5.3 — Batch Master Assignment

`MasterQuestionBatchService` accepts a complete extracted question set plus explicit `QuestionMatch` records.

The batch flow:

1. preserves already-assigned questions;
2. builds deterministic EXACT-equivalence components;
3. groups a new exact component under one master;
4. reuses an existing safe master when external evidence supports it;
5. applies the REPHRASED confidence and margin policy;
6. returns AMBIGUOUS instead of guessing when competing masters remain;
7. never uses SAME_CONCEPT or RELATED_TOPIC for master identity.

The batch API is deterministic with respect to question metadata and does not depend on the caller's input order.

## Phase 5.4 — Verified Ingestion Orchestration

`VerifiedIngestionOrchestrator` is the application-level lifecycle boundary:

`NormalizedDocument → QuestionExtraction → QuestionPersistence → AnswerKeyPersistence → AnswerResolution → MatchPersistence → MasterAssignment → VerifiedHistory`

Important safety rules:

- extracted questions are persisted even when historical verification is insufficient;
- answer-key mappings are deterministic and never invented;
- matching is persisted independently of historical appearance creation;
- only `VerificationStatus.VERIFIED` can create historical `ExamAppearance` records;
- unresolved/invalid answer keys remain visible as unresolved rather than becoming guessed answers;
- `SAME_CONCEPT` and `RELATED_TOPIC` never become historical-equivalent master identity;
- appearance identity is deterministic from exam/year/shift/question number, so copied source pages cannot create additional exam occurrences;
- master assignment determines whether the current appearance is canonical/exact/rephrased relative to the master.

This keeps source evidence, extraction, matching, master identity and exam history as separate auditable layers.

## Next step

Add the durable ingestion transaction/outbox boundary and batch document lifecycle so a fetched paper can be processed exactly once, retried safely, and resumed after partial failure.
