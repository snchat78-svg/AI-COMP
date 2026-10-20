# AI-COMP Master Roadmap — Operational Checkpoint

**Checkpoint date:** 20 October 2026  
**Repository:** [snchat78-svg/AI-COMP](https://github.com/snchat78-svg/AI-COMP)  
**Main snapshot reviewed:** [c75f273](https://github.com/snchat78-svg/AI-COMP/commit/c75f273a91277b8a29586802c4276ad077b8c885)

## Executive status

AI-COMP has a substantial backend and Flutter-client foundation, and the recent source-research work is merged. It is **not yet proven end-to-end as a complete exam-intelligence platform**. The current critical path is to restore and verify allowed connectivity to official exam sources, persist real paper candidates, process them, run official answer-key reconciliation, and confirm the learner's verified question pool is populated.

Do not repeat the already implemented registry, downloader, OCR, verification, test-session, or adaptive-learning foundations. Extend them only where the current evidence shows a gap.

## Recent work reviewed

| Area | Repository evidence | Assessment |
|---|---|---|
| Phase 2.2 — Durable official-source discovery | Merged PR #15; later discovery hardening and source-health changes are also on main | Code and tests exist. Operational discovery is still blocked until official-source connectivity is proven and candidates persist. |
| Phase 2.3 — Durable paper processing | Merged PR #16; bounded downloader, SHA-256 deduplication, private Supabase Storage, Hindi/English OCR, extraction CLI and scheduled/manual workflow | Implemented in code. Real documents still must flow through it. |
| Phase 2.4 — Official answer-key verification/history ingestion | Merged PR #17; migration 0018_phase2_4_official_answer_key_pairs.sql, conservative paper/key matching, provenance and history ingestion | Implemented in code. Live migration state and actual appearance counts are not confirmed by the repository alone. |
| Phase 2.5 — Source reachability diagnostics | PRs #25–#29 merged; bounded DNS/TCP/TLS probes, fixed-host Render diagnostic endpoint, and improved GitHub Actions result logging | Diagnostic endpoint deployed; it does not itself restore network access or discover papers. Inspect the source-specific TCP/TLS result table before calling the blocker fixed. |
| Phase 2.5.1 — Official RSSB legacy archive fallback | PR #31 merged; registers `RSSB_LEGACY_OFFICIAL` as a separate official source under existing robots/host/TLS policies | Live TCP passes but TLS fails due unsafe legacy renegotiation requirement; no candidates were persisted. Not operationally resolved. |
| Phase 2.5.2 — Registry-aware health polling | PR #32 merged; Render health workflow waits until the current report includes `RSSB_LEGACY_OFFICIAL` | Fixes stale old-deployment success; does not prove any site is reachable. |
| Phase 2.5.3 — Operational connectivity gate | PR #33 merged; main CI and Docker build passed. Health job requires TCP + certificate-validated TLS on at least one official source | Live health correctly fails: no registered official source currently passes both checks. This is a real external source-access blocker, not a code-test failure. |

| Phase 6.47 — APK default API URL | Merged PR #10 | Client defaults to the HTTPS Render API URL, editable by the user. This does not by itself prove login or database access works on a real device. |
| Phase 6.51 — Eligible-pool test selection | Merged PR #14 | A test is capped to available unique eligible questions; an empty verified pool correctly remains an explicit error rather than creating fake or duplicate history. |
| Phase 6.52 — Verified historical question pool | In progress on PR `phase-6-52-verified-history-question-pool`; distinct official-history repository, matched official answer-key gates, source provenance in session snapshots, readiness API and mobile status | Fixes the code gap where `exam_appearances` history was not queried by timed practice. Live candidate ingestion is still blocked, so a nonzero real pool remains unproven until official HTTPS access returns. |

## Master Roadmap coverage

| Master phase | Current implementation assessment | What is still unproven or incomplete |
|---|---|---|
| **1. Source & exam registry** | Registry, conducting-body/exam/source/category foundations and Rajasthan seeds exist. | Completeness of live official archives and real source coverage. Do not recreate the registry. |
| **2. Paper research engine** | Controlled discovery, safe fetching, file hashing, private object storage, OCR/extraction and scheduled/manual workflows exist. Phase 2.5 diagnostics and strict operational health gate are merged. | Latest Render report confirms: current RSSB and RPSC TCP connections fail; the official legacy RSSB host passes TCP but fails verified TLS with `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`. Research run 39408528273 persisted zero candidates. Do not weaken TLS or bypass robots/terms/host policy. The unresolved external blocker is an approved official HTTPS endpoint reachable from the research runtime. |
| **3. Structured question DB & answer verification** | Structured extraction, answer-key records, provenance, migration 0018 and conservative reconciliation exist. | Confirm migration 0018 was applied to the intended Supabase database, then verify real extracted-question and answer-key counts. Live migration state is not inferable from merged code. |
| **4. Matching & exam history** | Exact/normalized/semantic/concept matching, master identity and official appearance ingestion exist. Phase 6.52 loads only explicit matched-paper / verified-key historical items and deduplicates exact stems in the learner pool. | Live evidence rows must exist and be checked. The source/key provenance is displayed for historical questions when they reach a test; no complete question-wise history browser is claimed. |
| **5. User material analysis** | Backend foundations for material matching and generated-question storage are present in the audited codebase. | A complete photo/PDF upload → OCR/text → concept extraction → generation → test flow, and its upload UI in the mobile app, are not yet proven end-to-end. |
| **6. Test engine** | Persistent sessions, timed session flow, answer/navigation/resume/submit, unique eligible-pool capping and separate historical/generated source selection are implemented. The mobile dashboard can read and display readiness counts. | Verify the current live pool endpoint and complete a real test only after the pool returns eligible records. Do not use duplicates or unverified items to meet a requested count. |
| **7. Results & analytics** | Persistent results, answer review, explanations and weak-topic analytics foundations exist. | Validate against real learner sessions and the live database/API. |
| **8. Personalized preparation** | Adaptive recommendations, learning history/feedback and mobile dashboard/auth/session flows exist. | Verify live Firebase sign-in and API-side UID binding on a device; previous Firebase Admin credential configuration had a reported deployment issue and its live resolution must be tested. |
| **9. Continuous research** | Scheduled/manual source discovery, processing and verification workflows exist. | Scheduled jobs do not equal continuous successful ingestion. Prove the full chain from source access → candidates → extracted questions/key entries → verified history → eligible practice pool. |

## Mobile app: what the available APK lets you inspect

The Flutter client includes Firebase email/password sign-in and verification, password reset, preparation dashboard, adaptive/mixed practice setup, timed questions, answer saving/navigation/review markers, persistent-session resume, and submitted-result/answer review flows.

The APK is a **release-mode test build signed with a debug key**, not a production/store-signed application. It is intended to let you inspect the current client UI and test the API flow. It does not mean that every Master Roadmap feature is already present in the app, that the live learner pool has questions, or that production distribution is ready.

The last validated mobile build (Phase 6.51, 16 October) passed dependency resolution, flutter analyze, Flutter tests, APK build, artifact verification and upload. A fresh build is also run as part of this checkpoint change. Comparison of the 45 commits from the Phase 6.51 merge to the reviewed main snapshot showed no changes under apps/mobile/**; the later changes were in research/backend/docs/workflows.

## Live operational facts and boundaries

- Render's latest confirmed live deployment is commit `ca433d76855a293512d84e803e348b8699e9dc4b` for https://ai-comp-api.onrender.com.
- The merged health workflow [run 39409525917](https://github.com/snchat78-svg/AI-COMP/actions/runs/39409525917) retrieved the current three-source table and then correctly failed because none of the official hosts completed both TCP and certificate-validated TLS.
- Official research run [39408528273](https://github.com/snchat78-svg/AI-COMP/actions/runs/39408528273) persisted zero candidates. Green paper-processing/verification jobs with zero selected rows do not establish a populated question bank.
- Phase 6.52 adds the missing code path from verified `exam_appearances` to the practice pool, but it is still pending CI/merge in this checkpoint branch. The real count depends on the live readiness endpoint plus existing source-backed DB records.
- Migration 0018's current live state and secret configuration must still be checked through existing workflow/database evidence. Never put secrets in chat or source control.
- Do not put database URLs, passwords, Firebase service-account JSON or Supabase service-role keys in source control or chat.

## Exact next sequence — resume here, without repeating completed phases

1. Merge Phase 6.52 only after CI passes. This closes the practice-pool integration gap; it does not generate or backfill historical source records.
2. Confirm the deployed `/api/v1/learners/{learner_id}/question-bank/readiness` endpoint responds and reports the actual eligible, verified-history and generated-question counts.
3. Restore one approved official HTTPS path from the research runtime. The current-source timeout and legacy TLS failure must be fixed by a supported endpoint or authorized network/hosting change—not by weakening certificate verification, enabling unsafe legacy renegotiation, or bypassing robots/terms.
4. Run `official-source-research` and stop if it fails or persists zero candidates.
5. Run `official-paper-processing`; validate download/dedup/storage/extraction counters.
6. Run `official-answer-key-verification`; inspect review states, matched pairs, resolved answer records and real source-linked exam appearances.
7. Refresh the mobile dashboard and confirm the readiness counts increase. Start and submit a timed test only when the eligible count is nonzero; check historical provenance on questions pulled from exam history.

**Resume checkpoint:** Phase 6.52 pool integration → approved official TCP + certificate-validated TLS → nonzero persisted discovery → extraction/OCR → official answer-key reconciliation → source-backed exam history → readiness endpoint and mobile test. Never treat an empty-queue green job as end-to-end completion. Do not restart Phase 1 or reimplement Phases 2.2–2.4.
