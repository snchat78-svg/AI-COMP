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
