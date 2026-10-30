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


## Merged increment — topic duplicate guard and batch audit (PR #107)

PR [#107](https://github.com/snchat78-svg/AI-COMP/pull/107) merged as `0f8da54ca22ec5e76857587e92df2a9913b92521`. Tested implementation head `49feab1ce05ec712415b208c141d74fdab0d3b7d`; backend [run #730](https://github.com/snchat78-svg/AI-COMP/actions/runs/41061934522) passed full pytest and API container build; Flutter [run #144](https://github.com/snchat78-svg/AI-COMP/actions/runs/41061934507) passed analysis, mobile tests, release APK build, verification and upload (artifact `12980571357`, SHA-256 `acf231349a7735a485748463bf5eb571a4587cb2a470a58449a644959cb042a8`).

The service now scans prior same-concept/language Q&A across review states, uses deterministic Unicode-aware question/answer similarity triage and same-batch filtering, and returns separate generated/rejected/duplicate/pending-review/verified batch counts. Database exact-hash uniqueness remains the final race-safe duplicate guard. Scan failures or more than 5,000 existing topic records fail closed. Generated items remain `NEEDS_REVIEW`; generated `verified_count` is zero. This is not semantic truth validation or full examinable-point coverage.

## Next quality increment

Next bounded work should add reviewer-facing coverage dimensions (distinct examinable points, not just question counts), safe duplicate/near-duplicate handling across a topic, and a batch audit report that shows generated, rejected, duplicate, pending-review and verified counts separately. Do not bulk-generate from unreviewed or unofficial source text.
