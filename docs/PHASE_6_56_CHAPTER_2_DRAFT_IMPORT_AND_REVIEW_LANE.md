# Phase 6.56 — Chapter 2 Q&A draft import and learner review lane

**Date:** 20 November 2026  
**State:** Code and CI validation in progress; production database activation not yet verified.

## 1. Problem observed in APK

The Rajasthan History screen loaded the subject catalogue (34 child topics and 7 parent topic groups in the user screenshot) but showed 0 verified One-Liners. This was technically consistent with the old learner API, which returned only `verification_status='VERIFIED'`. The 368 AI-authored Chapter-2 Q&A entries were stored in the Git Markdown source file but were not seeded into the live PostgreSQL question-bank table.

## 2. Chapter 2 source of record

The single parent book chapter remains **राजस्थान के प्राचीन सभ्यता स्थल** with five child sites/concepts:

| Child | Draft range | Draft count | Canonical concept ID |
|---|---|---:|---|
| कालीबंगा | KAL-001–KAL-311 | 311 | `catalog.rajasthan_history_ancient_history_kalibangan` |
| आहड़-बनास संस्कृति | AHB-001–AHB-020 | 20 | `catalog.rajasthan_history_ancient_history_ahar_banas_culture` |
| गणेश्वर-जोधपुरा संस्कृति | GJ-001–GJ-018 | 18 | `catalog.rajasthan_history_ancient_history_ganeshwar_jodhpura_culture` |
| बैराठ / विराटनगर | BRT-001–BRT-009 | 9 | `catalog.rajasthan_history_ancient_history_bairat` |
| मत्स्य जनपद | MTS-001–MTS-010 | 10 | `catalog.rajasthan_history_ancient_history_matsya_janapada` |
| **Total** | | **368** | |

These are AI-authored study-note candidates, not claimed PYQs. All require independent review.

## 3. Database import

Migration `0030_import_chapter_2_hindi_draft_one_liners.sql` inserts the 368 Q&A rows into `question_bank_one_liners`.

- Stable import IDs preserve the source draft reference, e.g. `ch2_KAL-001`.
- Language is `hi`; existing concept IDs are preserved.
- `verification_status` is always `NEEDS_REVIEW`; `reviewed_at` is NULL.
- Each row carries the source URL and a human-readable source locator.
- `content_hash` follows the repository's established normalized question + literal backslash-n + normalized answer algorithm.
- `ON CONFLICT DO NOTHING` makes a controlled re-run safe.
- This migration is committed code, not proof that the live database has been updated.

## 4. API visibility contract

The verified learner route remains unchanged in meaning:
`GET /api/v1/learners/{learner_id}/question-bank/one-liners` returns only `VERIFIED`.

A separate authenticated route was added:
`GET /api/v1/learners/{learner_id}/question-bank/pending-one-liners`

It returns only `DRAFT/NEEDS_REVIEW` entries, with the explicit status in each item. Topic catalogue responses now include separate `verified_one_liner_count` and `pending_one_liner_count` values.

## 5. APK display

In the One-Liner tab, the learner sees both categories with separate status chips:

- **सत्यापित प्रश्न** — only independently approved records.
- **AI मसौदा — समीक्षा बाकी** — visible for study/reading, but not represented as verified and not used as official PYQ.

Pending answers show source locators as “जाँच बाकी”. The “पिछले वर्षों के प्रश्न” tab continues to show only questions matched to verified official papers and official answer keys.

## 6. Review and publishing

All 368 imported rows remain `NEEDS_REVIEW`. Publication to `VERIFIED` requires a separate reviewer credential, exact source check, Q/A confirmation, Hindi quality and topic mapping checks, duplicate checks, review note and append-only audit entry. Authoring credentials cannot self-verify.

## 7. Remaining acceptance gates

1. Backend repository and pending-route tests pass.
2. Flutter analyze, all widget/client tests and release APK build pass on the exact PR head.
3. Merge PR and confirm API deployment.
4. Identify the real PostgreSQL target without exposing secrets.
5. Run controlled migrations 0029 and 0030 through the repository's manual database-migration workflow with the intended `AI_COMP_DATABASE_URL`.
6. Query counts by concept: pending 311/20/18/9/10 (total 368) and verified count unchanged until review.
7. Sign in to the APK and verify pending questions display under the right five child topics in Hindi; verify Previous Year lane remains separate.
8. Complete independent reviewer workflow before moving any row to `VERIFIED`.

## 8. Phase control

Phase 6.56 remains `IN_PROGRESS` until its official syllabus/source gates, live import and acceptance checks are closed. Phase 6.57 stays `PLANNED`; Phase 6.58 stays `BLOCKED`. Do not start the next book chapter before Chapter 2 scope and source/review checks are complete.


## 2026-11-20 — Offline Chapter 2 draft fallback

- Added `apps/mobile/assets/question_bank/rajasthan_history_chapter_2_drafts.json`, generated from the exact 368 rows in database migration 0030/source-of-record. Counts: KAL 311, AHB 20, GJ 18, BRT 9, MTS 10. All carry `NEEDS_REVIEW` and Hindi language code.
- Registered the JSON asset in Flutter `pubspec.yaml`; added `LocalQuestionBankDrafts` with a cached loader, concept-specific queries, total count 368 and five stable per-concept counts.
- The mobile One-Liner screen now loads the server pending lane and the bundled local copy, merges by stable `one_liner_id`, prefers the server representation for duplicates, and fills any missing rows from the APK asset. Sorting by stable source ID gives consistent pagination.
- When the server returns zero rows or the pending endpoint is temporarily unavailable, the local copy still displays with the exact **AI मसौदा — समीक्षा बाकी** label and an explanatory local-copy banner. It never becomes VERIFIED and is never shown as a PYQ.
- Subject, parent chapter and child-topic pending counts use the greater of the live API count and the known bundled local count, so the screenshot's zero pending indicator is corrected even before migration 0030 is live.
- Added tests for 368 asset records, all five group counts, unique IDs, NEEDS_REVIEW-only status, and the screen rendering KAL-001 when the server pending endpoint returns 503. Flutter CI must pass before this offline increment is merged.
- Migration 0030 is still required to synchronize draft content to PostgreSQL and make it available across devices. The bundled fallback guarantees this APK can show the 368 Chapter 2 drafts without waiting for that DB write.
- Phase 6.56 remains `IN_PROGRESS`; 6.57 `PLANNED`; 6.58 `BLOCKED`.


## 2026-11-22 — हिंदी-प्रथम प्रश्न batch 1 और अनिवार्य APK gate

- Chapter-2 के पूरे 368 Hindi Q&A पर lexical audit ने प्रारम्भ में 292 प्रश्नों और 254 उत्तरों में Latin-script terms पाए। यह heuristic scan था; proper names, technical terms और fixed site identifiers को अलग-अलग संभालना आवश्यक था।
- KAL-001–KAL-060 का Hindi-first rewrite पूरा हुआ। अब इन 60 प्रश्नों/उत्तर pairs के prose में KLB fixed identifiers (KLB-I, KLB-II, KLB-1 आदि) को छोड़कर कोई Latin-script word नहीं है। स्रोत-आधारित अर्थ, तिथियाँ, माप और evidence columns सुरक्षित रखे गए। 368 में से 252 प्रश्नों और 211 उत्तरों में अभी भी अन्य Latin-script terms हैं; शेष batches लंबित हैं।
- Audit report: `docs/reviews/CHAPTER_2_HINDI_LANGUAGE_AUDIT_2026-11-22.md`. Regression tests first 60 Hindi rows, site-code preservation और Phase-file-to-APK CI triggers को enforce करते हैं।
- Updated `.github/workflows/flutter-mobile.yml`: Phase 6.56 docs, study notes, coverage ledger और DB migrations के push/PR changes भी Flutter release workflow चलाते हैं। Real Firebase config अब distributable APK artifact के लिए required है; analyze, tests, release build, verify और upload सभी gates हैं।
- कोई draft VERIFIED/PYQ नहीं किया गया। सभी 368 question drafts review-pending रहते हैं।
- Next bounded content batch: KAL-061–KAL-120 Hindi-first rewrite. Phase 6.56 remains IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED.
- **APK rule:** every merged content/phase/database increment must have a matching successful main-branch Flutter release run and a verified `ai-comp-mobile-android-apk` artifact. A PR-only build does not replace this main-head artifact check.
