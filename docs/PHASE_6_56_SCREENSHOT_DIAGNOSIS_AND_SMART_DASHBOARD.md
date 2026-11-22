# Phase 6.56 continuation — screenshot diagnosis and Smart Dashboard

**Date:** 22 November 2026  
**Status:** Investigation confirmed; implementation tracked in GitHub issue #124. No verification or APK readiness is claimed by this record.

## Screenshot diagnosis

The user APK screenshot shows Rajasthan History with 34/34 child topics, 7 parent groups, 0 verified and 368 review-pending. This matches the intended publication boundary, not a reason to bulk-approve records.

The 368 Chapter-2 candidates are:
- कालीबंगा: 311
- आहड़-बनास संस्कृति: 20
- गणेश्वर-जोधपुरा संस्कृति: 18
- बैराठ / विराटनगर: 9
- मत्स्य जनपद: 10

They are AI-authored study-note candidates, not established previous-year questions. They remain `NEEDS_REVIEW`. The learner verified route returns only independently approved records; the separate pending lane/local APK fallback displays drafts with a clear review-pending label. A topic catalogue entry is not proof of complete content coverage.

## Current content checkpoint

PR #123 merged into main at `a3900af50fd5eb8dc13b8db335fc86c911bfe071`. KAL-001–KAL-180 have Hindi-first prose, synchronized across canonical notes, migration 0030 and the offline APK asset, with 60/60 parity for the latest batch. All remain `NEEDS_REVIEW`. Next bounded language batch: KAL-181–KAL-240.

## Work order — issue #124

1. Reconcile verified and pending counts across API, database migration and local fallback; preserve status separation.
2. Exercise the independent reviewer path against exact source bytes/locations, answer correctness, source authority, Hindi clarity, duplicate risk and syllabus applicability. No self-approval or bulk status update.
3. Redesign the Question Bank and home dashboard with an attractive Hindi-first hierarchy, accurate topic progress, distinct verified/draft/PYQ/practice lanes and useful next actions. Preserve auth/email verification, existing tests and previous-paper flows.
4. Continue KAL-181–KAL-240 only with exact notes ↔ SQL ↔ APK asset parity, source locators and regression tests.
5. Run backend tests, Flutter analyze/widget tests, release APK build and artifact verification on the exact merged main head.

## Acceptance boundaries

- Do not mark any AI-authored question `VERIFIED` or PYQ without an independent source review and audit record.
- Do not infer complete syllabus coverage from the 34-topic catalogue or a raw question count.
- Do not mark Phase 6.56 complete or start Phase 6.57 until official syllabus/source identity, live migration and authentic-data mobile E2E gates are proven.
- A merged PR is not proof of a post-merge APK artifact. Record the exact main workflow and artifact ID/hash before saying a new APK is ready.


## 2026-11-22 — User-approved no-reinstall content sync requirement

The user approved a content-first update model so newly published questions/content reach the installed APK without repeated APK downloads. Add this as a required Phase 6.56 product requirement (implementation/acceptance still pending):

- **Cloud content source:** published question-bank content, answers, explanations, topic catalogue and practice sets are served by authenticated/versioned API endpoints; the APK is not the source of truth for future content.
- **Automatic sync:** on app launch/resume and when the learner opens a relevant subject/topic, check a lightweight content revision/manifest; fetch only changed records (delta sync), not the entire bank.
- **Background refresh:** refresh published content in the background when network/connectivity and platform lifecycle permit; show last-sync state and retry safely. Do not promise instant push delivery while the app is closed; use polling/next-open sync unless a separately configured push channel is added.
- **Offline-first:** persist downloaded content in the local database/cache; previously synced questions remain usable offline. Queue safe learner progress locally and reconcile idempotently when online.
- **Publication safety:** only server-published content is synced as published. NEEDS_REVIEW drafts remain clearly labelled and are never silently promoted to VERIFIED or PYQ. Keep source/evidence, language, topic IDs, content revision and status with each record.
- **Compatibility:** content schema/API changes must remain backward-compatible with supported APK versions; if a mandatory app-code change is needed, clearly indicate that a Play Store/APK update is required. Content updates alone must not require reinstall.
- **Verification:** test first install, existing APK upgrade path, delta update, duplicate/idempotent sync, offline read, reconnect/retry, auth expiry, empty update and rollback/corrupt payload handling. Record backend + Flutter CI and exact main-branch APK artifact after merged app-code changes.

This requirement is accepted by the user but is NOT implemented or verified merely by this roadmap entry. Phase 6.56 stays IN_PROGRESS; 6.57 stays PLANNED; 6.58 stays BLOCKED. Preserve current review/PYQ boundaries.


## 2026-11-22 — Automatic content sync implementation slice 1 (manifest API)

**Status: IN_PROGRESS — design scoped; code and tests pending in branch `phase-6-56-content-manifest-api`.**

- Reuse the existing Firebase-authenticated learner API and configured `question_bank_connection_factory`; do not add another authentication system or database connection lifecycle.
- Add read-only endpoint `GET /api/v1/learners/{learner_id}/question-bank/content-manifest`.
- The manifest will provide a deterministic revision derived from the canonical `concepts` catalogue and the **VERIFIED-only** `question_bank_one_liners` publication set, plus aggregate concept/verified/pending counts. Pending drafts are represented only as a count and are never included in the published-content revision or silently promoted.
- No migration is intended for this first slice: derive the manifest from existing `concepts` and `question_bank_one_liners` data and existing `updated_at`/`content_hash` fields.
- Add regression coverage for authenticated access, learner-scope rejection, fail-closed unconfigured DB, deterministic revision, revision changes when catalogue/published question content changes, and exclusion of NEEDS_REVIEW/DRAFT rows from published revision.
- This slice is only the server-side revision contract. The next dependent slice adds a typed Flutter client reader, persisted local revision, delta retrieval and offline-safe sync. Do not claim the installed APK auto-updates until those client parts and real API/device E2E are accepted.
- Phase 6.56 remains IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. Preserve all prior content verification and APK release gates.
