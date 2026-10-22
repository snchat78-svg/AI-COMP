# Phase 6.54 — Topic-wise Previous-Paper API

**Phase status:** IN_PROGRESS until this code is merged and current backend + Flutter CI pass.  
**Canonical status ledger:** [Phase Registry](PHASE_REGISTRY.md)  
**Related implementation:** existing `GET /api/v1/learners/{learner_id}/question-bank/previous-papers` route and `PostgresVerifiedHistoryQuestionRepository`. This phase extends them; it does not create a second historical-question store or endpoint.

## Scope

The authenticated previous-paper API now supports these query parameters:

| Parameter | Required | Meaning |
|---|---|---|
| `concept_id` | yes | Canonical topic/subtopic concept ID |
| `subject_id` | no | Restrict to the selected subject |
| `exam_id` | no | Exact exam identity |
| `exam_year` | no | Appearance year, 1900–2200 |
| `exam_shift` | no | Case-insensitive shift match |
| `source_domain` | no | Official question-paper source hostname only, without URL scheme/path |
| `limit` | no | Page size, 1–100 |
| `offset` | no | Offset, 0–100000 |

Example:

```http
GET /api/v1/learners/learner-1/question-bank/previous-papers?concept_id=catalog.rajasthan_geography_rivers_and_drainage_luni_river&subject_id=Rajasthan%20Geography&exam_year=2024&exam_shift=MORNING&source_domain=rssb.rajasthan.gov.in&limit=20&offset=0
```

The API response includes `pagination.total_count` and `pagination.has_more`. `total_count` is the number of distinct eligible canonical question identities after the requested filters; it is not the number of websites that copied a question. Each item keeps `verified_appearance_count`, paper source URL and matched official answer-key URL.

## Trust and identity rules

- Reuse the Phase 2.2–2.4 source/appearance/answer-resolution tables and Phase 6.52 historical read model.
- Include a historical question only if the paper source and official answer key are verified, the paper/key pair is matched, the resolved answer agrees with the source answer, there are exactly four options, and the official HTTPS origin checks pass.
- Apply exam/year/shift filters after the eligible appearance set's canonical repeat count is calculated. Filtering to one exam must not falsely reduce a known question's verified appearance count to one.
- Preserve canonical question identity while keeping real exam appearances distinct in the source record.
- Bound pagination and reject malformed filter values before database access.
- Learner identity and scope is checked before the query. Content-admin credentials are not accepted as learner identity.

## Tests

- Repository SQL uses the existing official paper + matched official answer-key gates.
- Exact count and pagination are returned even when an offset is past the final row.
- Exam, year, shift, subject, concept and source-domain filters are parameterized.
- Repeat-count calculation occurs before appearance-specific filters.
- API tests cover answer/paper provenance, count metadata, invalid filters and learner-scope rejection.

## Not claimed complete

This API returns only records that actually exist and pass the trust gate. It does not populate missing official paper records, guarantee live RSSB/RPSC connectivity, or claim complete nationwide/exam-specific topic coverage. Those remain explicit data and deployment gates in [the full roadmap](PHASE_6_53_TOPICWISE_QUESTION_BANK_ROADMAP.md).

## Close-out checklist

1. Backend pytest and Flutter analyze/widget/release-APK CI pass on the PR head.
2. Required reviewers and merge policy pass.
3. Update [Phase Registry](PHASE_REGISTRY.md) with PR number, merge SHA, CI run outcomes and any outstanding live-data gates.
4. Mark complete only after all phase-specific checks are true; otherwise leave the exact pending gate.
