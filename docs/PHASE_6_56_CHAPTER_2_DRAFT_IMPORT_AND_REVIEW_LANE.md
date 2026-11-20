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
