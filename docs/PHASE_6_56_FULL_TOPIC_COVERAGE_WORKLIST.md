# Phase 6.56 — full-catalogue One-Liner coverage worklist

**Status:** implementation on current-main branch `phase-6-56-full-topic-coverage-mainline`; PR #109 exact-head CI pending.  
**Parent phase:** Phase 6.56 remains IN_PROGRESS. Phase 6.57 is not started.  
**Canonical status:** [PHASE_REGISTRY.md](PHASE_REGISTRY.md)  
**Permanent coverage rule:** [QUESTION_BANK_CONTENT_COVERAGE.md](QUESTION_BANK_CONTENT_COVERAGE.md)

## Why this increment exists

The starter catalogue contains 340 concepts across 14 broad subjects. A simple count of Q&A can hide omissions: a topic might have several definitions but no key dates, identities, places, classifications, comparisons, causes/effects, formulas, rules, exceptions, data, diagrams or common-confusion checks. PR #107 already adds topic-scoped duplicate protection and batch audit. This increment adds primary coverage-dimension tags and an explicit no-skip review worklist.

## Thirteen assessment dimensions

DEFINITION, IDENTITY, DATE_TIME, PLACE_LOCATION, CLASSIFICATION_LIST, COMPARISON_RELATIONSHIP, CAUSE_EFFECT_SEQUENCE, FORMULA_UNIT_METHOD, RULE_EXCEPTION, DATA_STATISTIC, MAP_DIAGRAM_TABLE, COMMON_CONFUSION and FACTUAL_DETAIL.

These are reviewer lenses, not a requirement that all 13 apply to every concept. The reviewer must explicitly state when a lens genuinely does not apply.

## Full catalogue matrix

`QUESTION_BANK_EXAMINABLE_POINT_MATRIX.csv` contains 340 × 13 = **4,420 assessment rows**. Every row begins `NOT_ASSESSED`. Fields include concept identity, dimension, status, source locator, accepted One-Liner IDs, reviewer identity and review note.

Valid reviewer outcomes:
- `APPLICABLE_COVERED`: cite authoritative evidence and accepted Q&A IDs that cover the point.
- `APPLICABLE_GAP`: record the examinable point that still needs coverage.
- `NOT_APPLICABLE_WITH_REASON`: record an explicit rationale and supporting syllabus/source locator.

The matrix was created from the Git coverage ledger, not from a production database query. It does not create questions or claim any topic is covered.

## Code behavior

- Gemini structured output must return exactly one allowlisted primary coverage dimension.
- The application validates the category again before persistence.
- The tag is stored beside the existing source-evidence locator; no new table or migration is added.
- The protected authoring API returns the tag per saved candidate and a count breakdown for actually saved items only.
- Legacy/manual records without a tag read as `UNCLASSIFIED`.
- Existing duplicate and batch audit checks remain in place.
- Every generated Q&A stays `NEEDS_REVIEW`; AI cannot approve its own work. Learner reads remain VERIFIED-only.

## Required authoring sequence

1. Reconcile every catalogue concept to the exact official syllabus of a selected exam. Add missing syllabus concepts before inventory attestation.
2. Work through every applicable topic/dimension row; do not silently skip any.
3. Use an authoritative checked source excerpt and exact section/page/heading locator for each batch.
4. Draft multiple distinct concise question → answer pairs for the source-supported examinable points; omit anything unsupported.
5. Run existing same-concept/language exact and near-duplicate checks.
6. Submit every draft as NEEDS_REVIEW, then require a separate independent human review.
7. Update matrix rows with evidence and accepted One-Liner IDs. Assess completion only after the applicable checklist and independent reviews pass.

## Explicit limits and blocked gates

This does not bulk-create 1,700 unverified Q&As from model memory. Existing generation remains concept-by-concept and source-excerpt-grounded; it does not fetch arbitrary URLs. Official syllabus bytes/version/hash and reuse rights, complete reviewed inventory and mappings, controlled live migrations/secrets and genuine mobile E2E remain open. Phase 2.2 remains BLOCKED; Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED; Phase 6.58 remains BLOCKED. No TLS/robots/proxy/DNS/access-control bypass and no email/phone contact is performed.
