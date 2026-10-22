# AI-COMP Phase Registry — Single Source of Truth

**Registry policy:** This file is the canonical index for phase identity, current status, evidence and next actions. Update the registry whenever a phase starts, changes status, is merged, or is validated. Other roadmaps may explain design details, but must link here and must not redefine status independently.

**Last verified:** 2026-10-22  
**Repository:** `snchat78-svg/AI-COMP`

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
| 6.54 | Topic-wise previous-paper API filtering, counts and integrity | IMPLEMENTED_CI_PENDING | [PR #40](https://github.com/snchat78-svg/AI-COMP/pull/40), head `0a8931dbddf673e32a86662f1f3569f113955a1e`; `docs/PHASE_6_54_TOPIC_PREVIOUS_PAPER_API.md` | Backend + Flutter/API tests and release APK CI must pass; then merge and record merge SHA. Real historic data remains separately gated by source availability |
| 6.55 | One-liner content depth and editorial workflow | PLANNED | `docs/PHASE_6_53_TOPICWISE_QUESTION_BANK_ROADMAP.md` | Add/review actual content from traceable sources; editor workflows must not auto-verify AI output |
| 6.56 | Full mobile exam → subject → topic study navigation | PLANNED | `docs/PHASE_6_53_TOPICWISE_QUESTION_BANK_ROADMAP.md`; reuse current `QuestionBankScreen` | Add exam-profile selection, filters/search, independent counts/loading/paging states and widget tests without replacing existing session flows |
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
