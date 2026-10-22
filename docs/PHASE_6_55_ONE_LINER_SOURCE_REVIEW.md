# Phase 6.55 — Source-backed One-Liner Q&A and Independent Review

**Status:** IN_PROGRESS; implementation is on `feature/phase-6-55-one-liner-source-review`.  
**Canonical status:** [Phase Registry](PHASE_REGISTRY.md).  
**Previous phase:** Phase 6.54 is merged and its backend + Flutter CI passed. Merge SHA: `16f75e3c76e9c830235c39a4dc806710c116bed0`.

## Goal and boundaries

Fill the existing `question_bank_one_liners` store with concise, topic-mapped direct Q&A that have traceable supporting evidence. Add an independent review path so a submitter cannot mark their own new content `VERIFIED` merely by adding an HTTPS URL.

This phase reuses migration `0019_phase6_53_topic_one_liners.sql`, the canonical `concepts` IDs, `PostgresTopicQuestionBankRepository`, the existing learner read endpoint and the protected admin authoring endpoint. It does not create a second content store, does not use generated MCQs as historic questions, and does not claim the entire 340-topic starter catalogue is covered.

## Current implementation in this branch

- Migration `0021_phase6_55_one_liner_review_workflow.sql` adds reviewer metadata and append-only `question_bank_one_liner_reviews` audit events. Legacy `VERIFIED` rows without independent reviewer identity are demoted to `NEEDS_REVIEW` for re-review.
- Migration `0022_phase6_55_seed_one_liner_candidates.sql` idempotently seeds 10 Hindi Q&A records with evidence URLs and concept IDs. **Every seeded record is `NEEDS_REVIEW`; none is learner-visible as verified by this migration.**
- The existing author endpoint (`POST /api/v1/admin/question-bank/one-liners`) accepts only `DRAFT` or `NEEDS_REVIEW`. Supplying `VERIFIED` is rejected.
- The separate review endpoint is `POST /api/v1/admin/question-bank/one-liners/{one_liner_id}/review`. Decisions are `VERIFIED`, `REJECTED`, or `NEEDS_REVIEW`; a non-empty reviewer note is required. Review events record reviewer identity, decision, note and source-check timestamp.
- A `VERIFIED` decision requires an absolute HTTPS source URL and non-empty evidence. The database additionally requires `reviewed_at`, `reviewed_by`, and `source_checked_at` for verified rows.
- A verified item cannot be silently downgraded to `NEEDS_REVIEW`; an independent reviewer can explicitly reject it with a reason, which removes it from the verified learner list and adds an audit event. The author may then resubmit the same canonical Q&A with corrected source/evidence; the existing rejected duplicate is reset to `NEEDS_REVIEW` and old review events remain in the audit table.

## Server configuration

Keep these values in the API host's secret/configuration store, never in the repository or mobile app:

- `AI_COMP_CONTENT_ADMIN_TOKEN` — authoring credential, sent using `X-AI-COMP-Content-Admin-Token`.
- `AI_COMP_CONTENT_REVIEW_TOKEN` — a separate reviewer credential, sent using `X-AI-COMP-Content-Review-Token`.
- `AI_COMP_CONTENT_REVIEWER_ID` — stable server-side reviewer identifier recorded in the audit log.

Missing configuration fails closed. Do not reuse the author token as the review token. Do not send these secrets to learners or include them in APK/client configuration.

## Editorial checklist

Before a candidate can become `VERIFIED`, the reviewer should:

1. Open the exact cited page or document and confirm it is accessible over HTTPS, authoritative for the fact, and relevant to the selected exam/topic.
2. Confirm that the source supports both the question's premise and the direct answer. Store a concise source locator (page/section/table) and paraphrased evidence; do not paste a large copyrighted passage.
3. Check that the topic ID is the most specific existing canonical concept, the Hindi wording is unambiguous, the answer is direct, and the record is not a duplicate.
4. Check whether the fact is volatile. Office holders, budgets, rankings, current rules and counts that change over time need an explicit as-of date and refresh/review policy.
5. Record a reviewer note and select `VERIFIED`, `REJECTED`, or `NEEDS_REVIEW`. A model-generated suggestion is never evidence of correctness and does not qualify as human review.

The API enforces separate credentials and audit fields. Source quality, exact factual support, syllabus applicability and language quality still require a human reviewer; HTTPS alone does not prove authority.

## Starter candidate set

The seed contains 10 candidates:

- **Rajasthan Geography (5):** the Luni desert river system; direction/endpoint of the Luni; Thar Desert in northwestern Rajasthan; the Aravalli/rain-shadow relationship described by the source; Banas and Chambal drainage of eastern and southeastern Rajasthan.
- **Protected areas (2):** district attribution for Keoladeo National Park and Ranthambore National Park, based on the currently published Rajasthan Forest Department table.
- **Rajasthan Art & Culture (3):** UNESCO inscription year for Kalbelia folk songs/dances; instruments named in UNESCO's description; comparison of the dance's swirling movements to a serpent.

These are a practical starting sample—not a complete topic bank. They remain pending until a qualified reviewer checks the source and syllabus fit.

## Source ledger used for the pending seed

All source URLs and evidence notes are stored on each seed row, not inferred from this document alone.

- [Rajasthan at a Glance — Rajasthan State Biodiversity Board / Environment Department](https://environment.rajasthan.gov.in/content/environment/en/rsbb/about-rajasthan/rajasthan-at-a-glance.html). Relevant sections cover the Thar Desert, the Aravalli and southwest monsoon relationship, the Luni and tributaries, and Banas/Chambal drainage. Page displayed an update date of 18 August 2026 when checked.
- [National Parks and Sanctuaries in Rajasthan — Forest Department, Government of Rajasthan](https://forest.rajasthan.gov.in/content/raj/forest/en/aboutus/forest-statistics/general-introduction1/national-parks-and-sanctuaries-in-rajasthan.html). The national parks table lists Keoladeo–Bharatpur and Ranthambore–Sawai Madhopur. Page displayed an update date of 18 October 2026 when checked.
- [Kalbelia folk songs and dances of Rajasthan — UNESCO Intangible Cultural Heritage](https://ich.unesco.org/en/RL/kalbelia-folk-songs-and-dances-of-rajasthan-00340?lang=en). Supports the entry's 2010 inscription and the details about performers and instruments. The review should open the linked official record when accessible and record the check in the review audit.

## Validation and completion gates

- Tests must ensure candidate IDs are unique, concept IDs exist in the starter catalogue, source URLs are HTTPS, evidence exists, and stored content hashes match the normalized Q&A pair.
- API tests must show that the author route cannot self-verify; the review route fails closed without its separate server secret/identity; the audit row is committed with a valid review; missing sources and unknown IDs are rejected; an already verified row cannot be overwritten.
- Backend tests and API image build, Flutter analyze/tests and release APK build/artifact verification must pass on the PR head.
- Apply migrations only through the approved migration workflow after reviewing the actual target database. Migrations authored in GitHub are not proof that a live database has run them.
- Do not mark Phase 6.55 complete until CI is green, the code is merged, and the seed's live-data status is stated accurately. The content count remains zero for verified candidates until they pass review. Phase 6.58 remains the separate real-data end-to-end gate.
