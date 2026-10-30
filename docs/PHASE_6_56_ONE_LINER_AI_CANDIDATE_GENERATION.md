# Phase 6.56 — AI-assisted, source-grounded One-Liner candidates

**Status:** merged in PR [#104](https://github.com/snchat78-svg/AI-COMP/pull/104) at `43e5209f70e729e7f68af9e4931e9ed529d08e0f`; this is the source-grounded candidate-generation foundation.  
**Parent phase:** Phase 6.56 remains **IN_PROGRESS**. This does not start Phase 6.57.  
**Canonical state:** [PHASE_REGISTRY.md](PHASE_REGISTRY.md)  
**Content coverage policy:** [QUESTION_BANK_CONTENT_COVERAGE.md](QUESTION_BANK_CONTENT_COVERAGE.md)  
**Product contract:** [QUESTION_BANK_PRODUCT_CONTRACT.md](QUESTION_BANK_PRODUCT_CONTRACT.md)

## Goal

Add an AI-assisted authoring path that turns a bounded, human-supplied source excerpt into concise, subject/topic/subtopic-linked One-Liner Q&A candidates. Reuse the existing `concepts` taxonomy, `question_bank_one_liners` table, duplicate hash, author endpoint, reviewer endpoint, audit trail and learner read endpoint.

This is a content-authoring pipeline, not a new One-Liner table or a replacement for the official Old Papers ingestion pipeline.

## Implemented scope

- `OneLinerCandidateGenerationService` accepts an existing canonical `concept_id`, a source HTTPS URL, source locator, exact source excerpt, requested language and a bounded count.
- Gemini returns structured question, direct answer, exact supporting quote, exact answer quote and an importance score. The model is instructed to use only the supplied excerpt, ignore embedded instructions, omit unsupported facts and return fewer rather than guess.
- The application independently checks both quotes against the submitted excerpt. The answer quote must be contained in the full evidence quote. It rejects malformed responses, low-priority candidates (default score below 0.60), duplicates and source excerpts above 120,000 characters.
- Candidate priority uses the existing `importance_score` field (0–1) and the existing question-bank reader already orders items by that field. This is an editorial study-priority estimate, **not** a claim about past-paper frequency, exam probability or confirmed syllabus applicability.
- Candidate persistence uses the existing repository and canonical content hash. New candidates are always saved as `NEEDS_REVIEW`; this generator cannot promote content to `VERIFIED`.
- The existing learner endpoint continues to return verified One-Liners only. Pending drafts remain hidden from learners until an independent reviewer uses the existing separate review credential and creates the required audit record.
- The new admin route is `POST /api/v1/admin/question-bank/one-liners/generate-candidates`. It requires the existing server-side `AI_COMP_CONTENT_ADMIN_TOKEN` header and `GEMINI_API_KEY` server secret. It is not called by the learner APK and neither credential belongs in client configuration.

## Request contract

Example payload (use a source excerpt that an authorized editor has actually opened and checked):

```json
{
  "concept_id": "catalog.rajasthan_geography_rivers_and_drainage_luni_river",
  "source_url": "https://example.gov.in/official-reference",
  "source_locator": "Document title, page 4, heading: Rivers",
  "source_text": "Exact bounded text copied from the reviewed source ...",
  "language_code": "hi",
  "requested_count": 20
}
```

The generator does not fetch arbitrary URLs. This avoids turning the authoring endpoint into a server-side request proxy and keeps the actual source acquisition separate. The HTTPS URL and excerpt are stored as evidence for the independent reviewer to reopen and verify. An HTTPS URL alone is not proof of official authority.

## Quality and publication gates

1. The canonical concept must already exist. Do not silently invent a topic or apply one exam's syllabus to every exam.
2. Every accepted question must be a direct Q → A, not a bare fact or an MCQ. Exact evidence text must support the proposed answer.
3. Priority scores order candidate review; they do not certify truth, frequency or syllabus fit.
4. No model-generated item can verify itself. All newly generated candidates remain `NEEDS_REVIEW`.
5. Only an independent reviewer can set `VERIFIED`, with source evidence, a review note, reviewer identity, source-check time and append-only review audit.
6. Only independently verified items appear in the learner One-Liner view. Previous Year Papers remain a separate lane and are never created from this generator.
7. Full syllabus completeness is not claimed from a question count. Continue to use the per-concept coverage ledger and the full examinable-point checklist.

## Operational prerequisites and limitations

- The API host must already have `GEMINI_API_KEY`, `AI_COMP_CONTENT_ADMIN_TOKEN`, and the independent review configuration. Never store these in Git or the APK.
- The request source excerpt must be sourced and checked by the authorized content operator. No official source has been fetched by this AI generation route.
- Phase 2.2 official-source connectivity remains independently BLOCKED. When an approved official document fetch path is restored, a subsequent integration can pass the validated source text and page/section locator into this generator without bypassing robots, TLS, provenance or review.
- This code slice does not query the live database, bulk-generate a complete syllabus bank, apply migrations, or prove that any new candidate is visible in the app.

## Acceptance evidence

PR #104 is merged on main. It adds deterministic tests for source-quote grounding, answer-quote containment, importance ordering/threshold, malformed provider output, local/database deduplication, HTTPS validation, excerpt/count bounds, Gemini response parsing and admin endpoint access/configuration failures. This checkpoint records the merge, not a claim that live Gemini credentials, database migrations or learner-visible verified data were exercised.

## Next action

The deterministic format gate is merged in PR #105. PR [#107](https://github.com/snchat78-svg/AI-COMP/pull/107) is now merged as `0f8da54ca22ec5e76857587e92df2a9913b92521`; [PHASE_6_56_TOPIC_BATCH_AUDIT.md](PHASE_6_56_TOPIC_BATCH_AUDIT.md) records the same-topic near-duplicate guard and separate generation/review audit counts. Next, continue examinable-point coverage planning and reviewer-facing gap reporting. Connect official-source content only after the existing source/provenance gates permit it. Keep Phase 6.56 IN_PROGRESS until the real exam profile, complete source-backed syllabus inventory, all concept applicability reviews, live migrations/secrets and genuine mobile E2E acceptance are complete.
