# Phase 6.56 continuation — One-Liner coverage-dimension tags

**Status:** implementation branch `phase-6-56-coverage-dimension-tags`; PR and exact-head CI pending.  
**Parent phase:** Phase 6.56 remains **IN_PROGRESS**. This increment does not start Phase 6.57.  
**Prior accepted slice:** PR #105 merged; tested head `e7957a81573093f77a6d7f97b82d3b3e98239971`, CI run [41025914983](https://github.com/snchat78-svg/AI-COMP/actions/runs/41025914983), 620 tests and API container build passed.

## Gap

The previous generator reported candidate totals but did not classify which kind of examinable knowledge point each Q&A addresses. Counts alone can hide missing dimensions within a broad topic. This increment adds a reviewer aid to make coverage gaps more visible.

## Change

Each Gemini-proposed candidate must contain exactly one supported `coverage_dimension`:

- `DEFINITION`
- `IDENTITY`
- `DATE_TIME`
- `PLACE_LOCATION`
- `CLASSIFICATION_LIST`
- `COMPARISON_RELATIONSHIP`
- `CAUSE_EFFECT_SEQUENCE`
- `FORMULA_UNIT_METHOD`
- `RULE_EXCEPTION`
- `DATA_STATISTIC`
- `MAP_DIAGRAM_TABLE`
- `COMMON_CONFUSION`
- `FACTUAL_DETAIL`

The provider response schema constrains the value to this allowlist. The application validates it again and persists the tag in the already-existing `source_evidence` text as a `coverage_dimension=...` prefix. This avoids a database migration and keeps old/manual records readable; untagged legacy records report as `UNCLASSIFIED`.

The protected admin generation response exposes:
- the saved candidate's coverage dimension;
- a count breakdown by dimension for the saved batch;
- the pre-existing saved, duplicate and rejected counts.

Counts are calculated from candidates that were actually saved. Duplicates/rejections are not counted as covered.

## Safety and interpretation

- A tag identifies the primary type of fact asked in one Q&A; it does not claim that the whole dimension, subtopic or syllabus is complete.
- Multiple independent facts in one dimension may still be missing. The source and topic must be checked for omissions, not merely for the presence of a category.
- This tag is model-proposed metadata. It remains attached to `NEEDS_REVIEW` candidates and must be corrected by the independent reviewer when it is wrong.
- It is not a fact-check, official-source certification, syllabus applicability decision, importance proof, question frequency, or coverage completion status.
- No new learner-facing access is granted. Verified-only learner reads and the separate Old Papers lane remain unchanged.
- No arbitrary URL fetch, source access bypass, TLS weakening, external mirror, new credential, or migration is introduced.

## Validation

Regression tests cover a valid tagged candidate, persistence/read-back from source evidence, saved-batch dimension counts, rejection of an unsupported category and Gemini schema parsing of a dimension tag. The full backend and API-container checks on the exact PR head are still required; green CI will validate code only, not factual review or live official-source access.

## Remaining parent-phase gates

Official source bytes/hash and reuse rights, an independently reviewed full syllabus inventory, every concept's applicability decision, reviewed factual candidates, live data/admin configuration, and authentic mobile end-to-end acceptance are still outstanding. Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED.
