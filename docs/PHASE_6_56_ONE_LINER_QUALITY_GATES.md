# Phase 6.56 continuation — deterministic One-Liner format gate

**Status:** MERGED in PR [#105](https://github.com/snchat78-svg/AI-COMP/pull/105) at `b68043fbc6b18616bbe75a31abd3b63977addc5a`; this is a scoped increment inside Phase 6.56, not a new numbered phase.
**Tested head:** `e7957a81573093f77a6d7f97b82d3b3e98239971`. **CI:** [run #721](https://github.com/snchat78-svg/AI-COMP/actions/runs/41025914983) — 620 passed, 14 warnings; API container build passed.
**Base main:** `43e5209f70e729e7f68af9e4931e9ed529d08e0f` (PR #104 merge).
**Canonical status:** [Phase Registry](PHASE_REGISTRY.md)
**Generation foundation:** [AI-assisted One-Liner candidate generation](PHASE_6_56_ONE_LINER_AI_CANDIDATE_GENERATION.md)

## Why this increment is needed

PR #104 added a per-concept, bounded-excerpt Gemini authoring route. It verifies exact evidence quotes, deduplicates candidates and stores every result as `NEEDS_REVIEW`. A remaining format gap was that an overly long question, a multi-question string or a paragraph-like answer could pass the evidence gate and still be called a One-Liner.

## Deterministic candidate-format contract

Before persistence, every draft must satisfy all of the following:

1. Exactly one question, ending in one `?` or `？`.
2. Question and direct answer each contain at most 240 characters.
3. Neither field contains a line break.
4. The answer contains no question mark and is not identical to the question after whitespace/case normalization.
5. Existing exact-source-evidence, answer-evidence containment, importance threshold and duplicate checks still pass.

Malformed candidates are rejected with a non-sensitive warning and counted in `rejected_count`. This is deliberately a format gate, not a semantic truth detector. It cannot prove that a translated/condensed answer is factually correct or that the source is authoritative.

## Gemini instruction update

The provider is asked to return one short question and one short direct answer, each within 240 characters, without compound questions or explanatory paragraphs. The application repeats these rules deterministically; prompt instructions alone are not treated as enforcement.

## Security and publication invariants

- Source excerpts remain bounded operator-supplied input; the generation route does not fetch arbitrary URLs.
- The generator never approves its own output. All persisted candidates remain `NEEDS_REVIEW`.
- Only an independent reviewer can approve a candidate after reopening the exact source and confirming source authority, concept/syllabus fit, answer accuracy, currency and evidence.
- One-Liners remain separate from the Old Papers lane. No paper is synthesized from generated Q&A, and no question history/frequency is inferred.
- No source-access restriction is bypassed. Normal TLS, source terms, robots rules and review controls remain unchanged.

## Regression coverage

Added deterministic tests reject:
- two questions combined in one item;
- a multi-line answer;
- an answer over 240 characters;
- a multi-line question.

A Hindi Q&A example confirms that the format gate accepts an ordinary single-question/direct-answer pair without changing its language. All accepted candidates still assert `NEEDS_REVIEW`.

## Remaining Phase 6.56 gates

This increment does not complete Phase 6.56. The official exam profile and official syllabus bytes/version/hash are still unverified; the complete unit/topic/subtopic inventory and every applicability mapping still need independent review; live migrations/admin-review secrets and real-data mobile E2E remain unproven. Phase 6.57 remains PLANNED and must not start before all parent-phase gates pass.


## Current next increment — topic duplicate guard and generation batch audit

The scoped Phase 6.56 work is on branch `phase-6-56-topic-batch-audit`. It adds a bounded scan of the existing concept/language Q&A before generation, Unicode-aware Q+A similarity triage, in-batch similarity checks, and explicit generated/rejected/duplicate/pending-review/verified counts. The final exact content-hash uniqueness rule remains in PostgreSQL. Any scan failure or more than 5,000 existing topic records blocks generation rather than silently skipping duplicate checks. Await exact-head CI and review; do not describe this as merged or live until those gates pass.

## Current quality controls — 2026-10-31

- PR #107 is merged and already provides topic/language-scoped near-duplicate checks plus separate generation/review batch audit counts.
- PR #108 carries forward the reviewer-facing 13-dimension tags onto current main and adds the full 340-concept × 13-dimension worklist (4,420 assessment rows).
- Every matrix row begins `NOT_ASSESSED`. A reviewer must explicitly record `APPLICABLE_COVERED`, `APPLICABLE_GAP`, or `NOT_APPLICABLE_WITH_REASON`, with source/syllabus evidence.
- A tag count or matrix row is not proof of fact accuracy, syllabus applicability, or full topic completeness.
- The authoring endpoint remains concept-by-concept and requires a checked, bounded source excerpt. It does not fetch arbitrary URLs or create source-free factual content.
- Every generated candidate remains `NEEDS_REVIEW`; existing independent review and VERIFIED-only learner read gates remain unchanged.

## Next content-authoring sequence

Reconcile the full catalogue to the exact official syllabus for a selected exam. Then process applicable topic/dimension gaps in bounded batches from checked authoritative sources, attach exact page/heading/section locators, deduplicate, submit as `NEEDS_REVIEW`, and complete independent review. Never replace inaccessible evidence with model memory or declare a topic complete based on a fixed question count.
