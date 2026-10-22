# AI-COMP Phase Registry — Single Source of Truth

**Registry policy:** This file is the canonical index for phase identity, current status, evidence and next actions. Update the registry whenever a phase starts, changes status, is merged, or is validated. Other roadmaps may explain design details, but must link here and must not redefine status independently.

**Last verified:** 2026-10-22  
**Repository:** `snchat78-svg/AI-COMP`
**Persistent content coverage ledger:** [QUESTION_BANK_CONTENT_COVERAGE.md](QUESTION_BANK_CONTENT_COVERAGE.md) + [QUESTION_BANK_CONTENT_COVERAGE.csv](QUESTION_BANK_CONTENT_COVERAGE.csv)  
**Restart checkpoint:** [PROJECT_CONTINUITY_CHECKPOINT.md](PROJECT_CONTINUITY_CHECKPOINT.md)  

**Cross-chat start gate:** Read this registry before every phase and follow [PHASE_CONTINUITY_STANDARD.md](PHASE_CONTINUITY_STANDARD.md). Verify `main` head and latest exact-SHA CI before changing code; do not repeat phases already completed here.

**Continuity setup evidence (2026-10-22):**
- Last verified application/documentation baseline before the phase-policy addition: `99d18efdef202f661ccd444f921641f44e7ceb7e`, [CI run 39756305750](https://github.com/snchat78-svg/AI-COMP/actions/runs/39756305750) — success.
- Added the reusable phase policy in `docs/PHASE_CONTINUITY_STANDARD.md` at commit `1fc42e631ec3601c72e0b174243e9b5cfde4283d`; its CI run 39758153317 was in progress at the last state check. Re-check latest CI before the next code phase.
- From the phase ledger, the next planned implementation item is **Phase 6.56**. Phase 6.55 still has live migration/reviewer/data gates, and Phase 6.58 remains blocked on approved official-source connectivity. Do not claim those operational gates complete from code CI alone.

## Status rules

- **PLANNED** — scoped, but implementation has not started.
- **IN_PROGRESS** — implementation/validation is being worked on; do not repeat the phase from scratch.
- **IMPLEMENTED_CI_PENDING** — code is in a PR; required CI is not all green yet.
- **MERGED_CODE_DATA_PENDING** — code was merged and relevant CI passed, but live data, secrets, migrations, or deployment acceptance are outstanding.
- **COMPLETED** — acceptance criteria are met, changes are merged, required tests are green, and any phase-specific data/deployment checks are complete.
- **BLOCKED** — a documented external dependency prevents completion.

Never mark a phase **COMPLETED** based only on file creation, a green local check, or a merged PR. Record what is and is not proven. Reuse existing components and extend a phase instead of creating a new duplicate implementation.

## Phase ledger

| Phase ID | Short name | Status | Evidence / work location | Remaining gate / next action |
|---|---|---|---|---|
| 6.39 | PostgreSQL learning feedback loop | MERGED (historical README record) | README phase history | No reimplementation; change only for a documented defect |
| 6.40 | Client-facing OpenAPI contracts | MERGED (historical README record) | README phase history | Extend existing contracts |
| 6.41 | Flutter adaptive-preparation foundation | MERGED (historical README record) | README phase history and `apps/mobile/` | Preserve login, timed session, resume and results flows |
| 6.42 | Android build and APK CI | MERGED (historical README record) | README phase history / Flutter Actions | Keep build artifact check green |
| 6.44 | Firebase email/password auth | MERGED (historical README record) | README phase history | Preserve email verification and password reset |
| 6.45 | Firebase API authentication/runtime | MERGED (historical README record) | README phase history | Secrets stay server-side |
| 6.46 | Free-tier hosting readiness | MERGED (historical README record) | `docs/PHASE_6_46_FREE_HOSTING_READINESS.md` | Actual deployment must be separately verified |
| 6.52 | Verified historical-question read model | MERGED | `docs/PHASE_6_52_VERIFIED_HISTORICAL_QUESTION_POOL.md`; main checkpoint listed in README | Reuse history gates, source-separated pool and readiness APIs |
| 6.53 | Topic catalogue, one-liners, separate past-paper view and subject practice generation | MERGED_CODE_DATA_PENDING | PR #36 merged; follow-up PR #39 merged as squash commit `916fac8f9876b46443573af772bb0e505032aad0`; migrations `0019_phase6_53_topic_one_liners.sql` and `0020_phase6_53_starter_topic_catalogue.sql`; Flutter screen `apps/mobile/lib/screens/question_bank_screen.dart` | Apply migrations through the controlled workflow; configure server secrets; populate/review source-backed one-liners and verify real previous-paper data. Starter catalogue is scaffolding, not official syllabus-completeness proof |
| 6.54 | Topic-wise previous-paper API filtering, counts and integrity | COMPLETED | [PR #40](https://github.com/snchat78-svg/AI-COMP/pull/40) squash-merged as `16f75e3c76e9c830235c39a4dc806710c116bed0`; `docs/PHASE_6_54_TOPIC_PREVIOUS_PAPER_API.md` | Backend pytest + API container passed (workflow run `39742750806`); Flutter analysis, mobile tests, release APK build, artifact verification and upload passed (run `39742750869`; artifact `12409383681`). Live historic-data readiness remains separately gated under Phase 6.58 |
| 6.55 | Source-backed One-Liner Q&A and independent review | MERGED_CODE_DATA_PENDING | [PR #41](https://github.com/snchat78-svg/AI-COMP/pull/41) squash-merged as `abfdfbfa8c8b732012c04a247e443032c93f6d01`; `docs/PHASE_6_55_ONE_LINER_SOURCE_REVIEW.md`; migrations `0021_phase6_55_one_liner_review_workflow.sql` and `0022_phase6_55_seed_one_liner_candidates.sql`; independent review API + audit tests | Backend pytest: 502 passed, 14 warnings; API container build passed (run `39755404955`). Flutter analyze, mobile tests, release APK build, artifact check and upload passed (run `39755200693`, artifact `12414704506`, SHA-256 `87d6bb73ea1794798bc6fde6c17f48fad08d8c0a40f1350e50977ee288161e14`; duplicate run `39755404990` also passed). Live migrations not applied; all 10 Q&A remain `NEEDS_REVIEW` until source/syllabus review; configure distinct author/reviewer secrets and reviewer ID before production use |
| 6.56 | Mobile Question Bank navigation, topic search and paged study states | IN_PROGRESS | [PR #42](https://github.com/snchat78-svg/AI-COMP/pull/42) merged as `d138d65d758efbde5c04126688566d499063da40`; `docs/PHASE_6_56_MOBILE_QUESTION_BANK_NAVIGATION.md`; `apps/mobile/lib/screens/question_bank_screen.dart`; `apps/mobile/test/question_bank_screen_test.dart`; content ledger `docs/QUESTION_BANK_CONTENT_COVERAGE.csv` and restart checkpoint `docs/PROJECT_CONTINUITY_CHECKPOINT.md` | Backend tests + API container passed on current PR head `c70313064c341b3f517c045a2dc63969b2c58341` (run `39758826307`). Flutter analyze, widget/client tests, release APK build, artifact verification and upload all passed on the same PR head (run `39758826247`; artifact `12416808828`, SHA-256 `10bf4f17bf3ada321c2ce3efab1a99d442f3cc311c34d9a031656f27fcaa1f55`). **Phase remains IN_PROGRESS:** next implement exam-profile selection and sourced official-notification/syllabus → concept mapping without inventing applicability. Full syllabus coverage and 5 independently verified Q&A per applicable subtopic remain outstanding |
| 6.57 | Topic coverage, learner mastery and revision | PLANNED | `docs/PHASE_6_53_TOPICWISE_QUESTION_BANK_ROADMAP.md` | Reuse existing learner-session/results/analytics; browsing alone must not count as mastery |
| 6.58 | Real-data end-to-end proof | BLOCKED on external/live-data gates | Roadmap's official-source connectivity checkpoint and verification gates | Confirm approved official HTTPS/TLS access, apply migrations, configure secrets, ingest paper + matched key and run mobile end-to-end test |

## Anti-duplication checklist (required before every new phase)

1. Read this registry first and select the next **PLANNED** phase; if an item already exists, extend it instead of starting a duplicate.
2. Search existing source files, migrations, API paths, models and tests before adding new ones.
3. State the exact gap this phase closes, in/out of scope, and testable exit criteria in its PR.
4. Add/update tests alongside code. Do not invent fixtures that present unsupported facts as verified.
5. After implementation, record PR number, changed files, test/CI results, merge commit, data/deployment gates and next action here.
6. Update the roadmap and README link only after the registry row is consistent; never claim real content/data complete before verification.

## Append-only change log

| Date (UTC) | Phase | Event | Evidence |
|---|---|---|---|
| 2026-10-22 | 6.53 | PR #36 merged; follow-up PR #39 merged after backend and Flutter CI passed on its PR head. | Main merge commit `916fac8f9876b46443573af772bb0e505032aad0` |
| 2026-10-22 | 6.54 | Opened implementation PR with exam/year/shift/source-domain filters, exact filtered canonical-question counts, bounded pagination, mobile filter/count contracts and regression tests. | [PR #40](https://github.com/snchat78-svg/AI-COMP/pull/40), head `0a8931dbddf673e32a86662f1f3569f113955a1e` |
| 2026-10-22 | 6.54 | PR #40 squash-merged after current-head backend and Flutter/APK CI passed; added exact merge evidence and kept real-data caveats under Phase 6.58. | Merge SHA `16f75e3c76e9c830235c39a4dc806710c116bed0`; runs `39742750806`, `39742750869`; APK artifact `12409383681` |
| 2026-10-22 | 6.55 | PR #41 squash-merged after backend tests/container and Flutter analyze/client/APK CI passed. Added separate reviewer authorization, audited decisions, idempotent pending seed candidates and explicit live-data gates. | Merge SHA `abfdfbfa8c8b732012c04a247e443032c93f6d01`; [PR #41](https://github.com/snchat78-svg/AI-COMP/pull/41); backend run `39755404955` (502 passed); Flutter run `39755200693`; APK artifact `12414704506` (SHA-256 `87d6bb73ea1794798bc6fde6c17f48fad08d8c0a40f1350e50977ee288161e14`) |
| 2026-10-22 | 6.56 | Started mobile topic navigation/search work and persisted the full-topic content requirement, per-concept ledger and first-read continuity checkpoint. | Branch `feature/phase-6-56-topic-navigation-coverage`; contract `docs/PHASE_6_56_MOBILE_QUESTION_BANK_NAVIGATION.md`; ledger contains 340 concept rows/14 subjects, 10 pending seed candidates across 6 concepts (Git only; live DB not queried) |
| 2026-10-22 | 6.56 | Merged topic search, bounded topic loading, independent paged One-Liner/Previous-Year states, coverage ledger and continuity docs; phase remains open for exam-profile/syllabus mapping. | Merge SHA `d138d65d758efbde5c04126688566d499063da40`; PR #42; backend run `39758826307`; Flutter run `39758826247`; APK artifact `12416808828` (SHA-256 `10bf4f17bf3ada321c2ce3efab1a99d442f3cc311c34d9a031656f27fcaa1f55`) |
