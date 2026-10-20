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
| Phase 2.5.1 — Official legacy RSSB archive fallback | In progress on PR `phase-2-5-1-official-rssb-legacy-fallback`; adds `RSSB_LEGACY_OFFICIAL` with constrained paths and robot-respecting navigation tests | Pending CI/merge and a live health/discovery result. It is an official-host fallback, not a claim that network access is restored or any questions have been ingested. |
| Phase 6.47 — APK default API URL | Merged PR #10 | Client defaults to the HTTPS Render API URL, editable by the user. This does not by itself prove login or database access works on a real device. |
| Phase 6.51 — Eligible-pool test selection | Merged PR #14 | A test is capped to available unique eligible questions; an empty verified pool correctly remains an explicit error rather than creating fake or duplicate history. |

## Master Roadmap coverage

| Master phase | Current implementation assessment | What is still unproven or incomplete |
|---|---|---|
| **1. Source & exam registry** | Registry, conducting-body/exam/source/category foundations and Rajasthan seeds exist. | Completeness of live official archives and real source coverage. Do not recreate the registry. |
| **2. Paper research engine** | Controlled discovery, safe fetching, file hashing, private object storage, OCR/extraction and scheduled/manual workflows exist. Phase 2.5 added connectivity diagnostics. | Recent research runs documented RSSB and RPSC IPv4 TCP timeouts, RPSC IPv6 network failure, and zero persisted candidates. A controlled fallback to the official legacy RSSB host is in progress; only a successful live TCP/TLS and discovery result can close the blocker. Do not bypass robots, terms, host checks or TLS. |
| **3. Structured question DB & answer verification** | Structured extraction, answer-key records, provenance, migration 0018 and conservative reconciliation exist. | Confirm migration 0018 was applied to the intended Supabase database, then verify real extracted-question and answer-key counts. Live migration state is not inferable from merged code. |
| **4. Matching & exam history** | Existing exact/normalized/semantic/concept matching, embeddings/concept identity and appearance/history data foundations are present; official appearance ingestion is connected to Phase 2.4. | Validate against actual sourced records. Website duplicates must never be counted as separate exam appearances. A complete question-wise history UI is not yet proven by the mobile workflow. |
| **5. User material analysis** | Backend foundations for material matching and generated-question storage are present in the audited codebase. | A complete photo/PDF upload → OCR/text → concept extraction → generation → test flow, and its upload UI in the mobile app, are not yet proven end-to-end. |
| **6. Test engine** | Persistent sessions, timed session flow, navigation/answer saving, resume/submit and unique eligible-pool capping exist in backend/client. | Real test completion must be validated after the verified question pool is populated. No duplicate/fabricated questions should be used to satisfy a requested count. |
| **7. Results & analytics** | Persistent results, answer review, explanations and weak-topic analytics foundations exist. | Validate against real learner sessions and the live database/API. |
| **8. Personalized preparation** | Adaptive recommendations, learning history/feedback and mobile dashboard/auth/session flows exist. | Verify live Firebase sign-in and API-side UID binding on a device; previous Firebase Admin credential configuration had a reported deployment issue and its live resolution must be tested. |
| **9. Continuous research** | Scheduled/manual source discovery, processing and verification workflows exist. | Scheduled jobs do not equal continuous successful ingestion. Prove the full chain from source access → candidates → extracted questions/key entries → verified history → eligible practice pool. |

## Mobile app: what the available APK lets you inspect

The Flutter client includes Firebase email/password sign-in and verification, password reset, preparation dashboard, adaptive/mixed practice setup, timed questions, answer saving/navigation/review markers, persistent-session resume, and submitted-result/answer review flows.

The APK is a **release-mode test build signed with a debug key**, not a production/store-signed application. It is intended to let you inspect the current client UI and test the API flow. It does not mean that every Master Roadmap feature is already present in the app, that the live learner pool has questions, or that production distribution is ready.

The last validated mobile build (Phase 6.51, 16 October) passed dependency resolution, flutter analyze, Flutter tests, APK build, artifact verification and upload. A fresh build is also run as part of this checkpoint change. Comparison of the 45 commits from the Phase 6.51 merge to the reviewed main snapshot showed no changes under apps/mobile/**; the later changes were in research/backend/docs/workflows.

## Live operational facts and boundaries

- Render's latest observed deployment is live at commit c75f273 for https://ai-comp-api.onrender.com.
- Render logs show two GET /diagnostics/official-source-health requests returned HTTP 200 on 20 October. That proves the diagnostic endpoint answered; it **does not** prove the RSSB/RPSC source hosts passed TCP/TLS or that any paper was downloaded.
- Recent repository evidence documents official-source research failures and zero candidate persistence. No end-to-end populated question bank should be claimed.
- Whether migration 0018 has been applied, whether the required GitHub/Supabase secrets are configured correctly, and the current verified pool count require live workflow/database evidence.
- Do not put database URLs, passwords, Firebase service-account JSON or Supabase service-role keys in source control or chat.

## Exact next sequence — resume here, without repeating completed phases

1. **Close the current Phase 2.5 operational blocker:** inspect the latest render-official-source-health workflow's per-source DNS/IPv4/IPv6 TCP and certificate-validated TLS table. A green HTTP request to the diagnostic endpoint is not enough.
2. If source connections fail, fix the actual permitted runtime/egress problem or use an approved research runner that can reach the registered official hosts. Do not weaken TLS, bypass robots/terms, allow cross-host redirects, or silently substitute an unapproved secondary website.
3. Check/apply migration 0018_phase2_4_official_answer_key_pairs.sql through the existing manual-only Apply database migrations workflow with its explicit APPLY confirmation and AI_COMP_DATABASE_URL secret. Do not invent or run an alternate migration path.
4. Run official-source-research; stop and diagnose if it fails or persists zero candidates.
5. Run official-paper-processing with AI_COMP_DATABASE_URL, SUPABASE_URL, and server-only SUPABASE_SERVICE_ROLE_KEY; check fetched, deduplicated, stored and extracted counts.
6. Run official-answer-key-verification; review ambiguous exam/year/shift or paper/key pairings instead of guessing. Confirm actual source-linked historical appearance rows.
7. Test the existing eligible question selector and mobile practice session using the real verified pool. Only after this chain works should the next matching/history gaps be expanded.

**Resume checkpoint:** Phase 2.5 operational closure (including validation of the `RSSB_LEGACY_OFFICIAL` fallback) → migration 0018 confirmation → discovery → processing → answer-key verification/history → verified learner-pool/device test. Do not restart Phase 1, reimplement the Phase 2.2–2.4 pipeline, or skip directly to broader exam coverage while the current source-data chain is empty.
