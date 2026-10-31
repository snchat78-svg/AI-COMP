# AI-COMP Project Continuity Checkpoint

**This file is the first-read checkpoint for every new AI-COMP chat/session.** Do not restart from conversation memory alone. Check the repository state in GitHub because it is the shared durable record.

**Last updated:** 2026-10-31 (main `0f8da54ca22ec5e76857587e92df2a9913b92521`; PR #107 is merged. Current continuation: branch `phase-6-56-full-topic-coverage-worklist` / PR #108, exact-head CI pending. Phase 6.56 continues; Phase 6.57 has not started.)  
**Repository:** https://github.com/snchat78-svg/AI-COMP  
**Canonical state ledger:** [docs/PHASE_REGISTRY.md](PHASE_REGISTRY.md)  
**Permanent full-topic content goal:** [docs/QUESTION_BANK_CONTENT_COVERAGE.md](QUESTION_BANK_CONTENT_COVERAGE.md)  
**Per-concept inventory:** [docs/QUESTION_BANK_CONTENT_COVERAGE.csv](QUESTION_BANK_CONTENT_COVERAGE.csv)  
**Roadmap:** [docs/PHASE_6_53_TOPICWISE_QUESTION_BANK_ROADMAP.md](PHASE_6_53_TOPICWISE_QUESTION_BANK_ROADMAP.md)

## Always-follow restart steps

1. Read this file and PHASE_REGISTRY.md first.
2. Read QUESTION_BANK_CONTENT_COVERAGE.md and the CSV ledger before planning Question Bank content.
3. Confirm current main/PR status and CI in GitHub; do not rely on old chat details if the code has changed.
4. Select the next PLANNED phase or resume an IN_PROGRESS phase. Never repeat merged phases unless fixing a specific defect.
5. Update this checkpoint and Phase Registry in the same PR as meaningful work; include exact branch, PR, merge SHA, test evidence, uncompleted gates and the next task.
6. Do not claim content complete from catalogue rows, code, generated text, or Git seed files. Only source-backed, independent-reviewed VERIFIED records count.

## Current phase state

- **Phase 6.54:** COMPLETED. PR #40 merge SHA 16f75e3c76e9c830235c39a4dc806710c116bed0. Backend tests/container and Flutter analysis/client/release APK workflows passed.
- **Phase 6.55:** MERGED_CODE_DATA_PENDING. PR #41 merge SHA abfdfbfa8c8b732012c04a247e443032c93f6d01. The repository contains independent one-liner review code and 10 Hindi candidates (all NEEDS_REVIEW), but migrations have not been confirmed applied to the live database and reviewer credentials remain a server configuration gate.
- **Phase 6.56:** IN_PROGRESS. Navigation/search/paging PR #42 merged at `d138d65d758efbde5c04126688566d499063da40`; exam-profile mapping PR #43 merged at `a3eeb95ef9557e56c0bad3005a8850d4b1013ba6` (backend run `39899673677`: 512 passed/14 warnings + container; Flutter/APK run `39899673666` passed). Protected author/reviewer + append-only audit PR #44 merged `44a1da0ef6c5afd79e81e7367ea57fac15dbfc7c` (run `39904691212`: 517 passed/14 warnings + API container). Structured UNIT/TOPIC/SUBTOPIC inventory PR #45 merged `9694e01c11528157b8a1107fcf78c4c3a1e01ef9` (run `39906458179`: 527 passed/14 warnings + container). Secure official-source fetch/evidence PR #46 merged `ea59fc9e4712b3b646c707e2abf6f30f3690975c`; tested head `c0e293d58c70a3621f5bf6d51741384838c24549` passed [run 39907825229](https://github.com/snchat78-svg/AI-COMP/actions/runs/39907825229): 538 passed/14 warnings; API container build passed. The source-fetch endpoint validates official-host HTTPS/redirects, size/time and PDF structure; computes SHA-256 from actual bytes and stores immutable evidence. No official exam profile is seeded; the candidate RSSB PDF has not been retrieved here. Remaining gates are controlled application of migrations, actual source fetch from approved API-host networking, independent notification/version/content review, complete topic/subtopic inventory, concept reconciliation and independent scope reviews, then real-data/mobile E2E. Phase 6.57 must not start early; Phase 6.55 live reviewer-secret/data gates and Phase 6.58 are still open.
- **Phase 6.57:** PLANNED — topic coverage, learner mastery and revision.
- **Phase 6.58:** BLOCKED on approved official-source connectivity, live database migration/secrets, real official-paper + matched answer-key records, and live end-to-end proof.

## Phase chronology audit (24 October 2026)

The canonical registry now includes the previously omitted merged milestones **6.43** and **6.47–6.51** from PRs #5, #10–#14, and separates the Phase 6.44 verified-email/English-UI work from the Phase 6.43 Firebase client-auth foundation. These are historical merged phases, not new work to repeat. Continue from the active/incomplete status in `docs/PHASE_REGISTRY.md`; do not infer that a later number means its prerequisites have passed.

## Cross-lane restart guard: Phase 2.2 is implemented, not a new start

The Phase Registry now records the older paper-research lane alongside the current Phase 6.56 work. This prevents a new chat from confusing a blocked live gate with an unimplemented phase.

- **Phase 2.2 — Durable official-source discovery:** implementation and tests were merged previously (PR #15). Registry synchronization, controlled discovery, robots/host restrictions, deterministic candidate IDs, PostgreSQL persistence and the scheduled/manual workflow already exist. The current blocker is **operational source reachability**, not missing Phase 2.2 code. Incremental PR [#52](https://github.com/snchat78-svg/AI-COMP/pull/52) is merged at `5baf6601c7addbecdf849fbcbaa16e966f6b386f`; exact tested head passed [workflow 40066852069](https://github.com/snchat78-svg/AI-COMP/actions/runs/40066852069): 545 tests passed (14 warnings) and API container build passed. The change skips retries for permanent TLS errors and preserves bounded transient retries; it cannot restore blocked outbound access. The post-merge official-source-research [run #14](https://github.com/snchat78-svg/AI-COMP/actions/runs/40066959494) then failed closed: all three official sources were blocked/failed and **0 candidates** persisted. Phase 2.2 therefore remains **BLOCKED**, not completed.
- **Phase 2.3 — Paper processing/extraction:** implemented and merged (PR #16). Reuse the existing bounded downloader, SHA-256 identity, private storage and Hindi/English extraction. Do not build another downloader.
- **Phase 2.4 — Answer-key verification/history:** implemented and merged (PR #17). Reuse the existing conservative pairing/provenance gates; do not rebuild answer-key matching.
- **Phase 2.5–2.5.3:** source diagnostics and the registry-aware/fail-closed health gates are already merged (PRs #25–#33). The gate correctly fails while all official sources fail TCP or certificate-validated TLS.
- **Phase 2.5.1:** the legacy RSSB fallback is registered, but it remains operationally blocked by `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`. Keep TLS verification on; do not enable unsafe renegotiation or bypass robots/terms.
- **Known repeat risk:** PR #48 was closed as superseded because its stale branch repeated Phase 6.56 source-fetch implementation already merged in PR #46. PR #49 was based cleanly on current main and added only isolated regression tests. Check current main before creating every new branch/PR.

### Exact next action for the Phase 2 pipeline

1. Restore access to at least one **verified official** host from the relevant runtime using DNS + TCP + certificate-validated TLS, and confirm current `robots.txt` and allowed-path rules.
2. Run the existing `official-source-research` workflow. Require a registered source to complete discovery and persist a **nonzero** number of real paper candidates. A diagnostic response or a green zero-row downstream workflow is not completion.
3. Only after candidates exist, run the existing Phase 2.3 processing workflow, then Phase 2.4 official answer-key verification. Check fetched/extracted/paired/appearance/eligible-pool counts at every boundary.
4. If all current official hosts remain unreachable, record the run as blocked and make no duplicate downloader, retry workflow or unofficial-source implementation to disguise the blocker. Do not advance past the unsatisfied dependency.

**Phase selection:** Phase 2.2 should not be “started from scratch” again. It is **BLOCKED at live acceptance**. The current mainline development phase remains **6.56 IN_PROGRESS**; Phase 6.57 remains **PLANNED**, and Phase 6.58 remains **BLOCKED** until its source, migration and real-data E2E gates pass. These lanes share the official-source dependency, so the same blocker should be fixed once and evidenced in both records—not reimplemented in separate chats.

## Separate draft lane: Phase 7.1 / 7.2 YouTube Study Notes

These two phases exist as **draft branches only**, not as features merged into current `main`:

- [PR #19 / Phase 7.1](https://github.com/snchat78-svg/AI-COMP/pull/19) is a documentation-only architecture freeze. It was tested at old head `19d76655405266338a4a5e077a2a09ab29ccfd1c` by workflow [38916367924](https://github.com/snchat78-svg/AI-COMP/actions/runs/38916367924), but its base is older than current main. It still needs review/rebase against current architecture.
- [PR #20 / Phase 7.2](https://github.com/snchat78-svg/AI-COMP/pull/20) is a draft contract/URL-validation implementation, stacked on the unmerged PR #19 branch. Its old-head workflow [38916533266](https://github.com/snchat78-svg/AI-COMP/actions/runs/38916533266) passed at the time, but it is not validated against current main and cannot merge ahead of its prerequisite.
- Do **not** recreate the URL parser/contracts or treat these PRs as completed. Do not merge or continue this later-numbered lane until Phase 7.1 is reviewed and the mainline ordering is explicitly confirmed. If resumed, rebase/port once on current main and rerun full CI. No YouTube provider, transcript ingestion or database writes are part of PR #20.
- The draft Phase 7.1 architecture also sketches **7.3 transcript acquisition, 7.4 notes builder, 7.5 persistence/API, 7.6 visual evidence/OCR, 7.7 Flutter integration, 7.8 PDF/E2E hardening, and optional 7.9 local/open model adapter**. The Registry records them as provisional planned dependencies only; no implementation for 7.3–7.9 is accepted in current main. Do not start them until the architecture is reviewed and the prior phase accepted.

The current accepted mainline remains **Phase 6.56 IN_PROGRESS** with Phase 6.57 PLANNED and Phase 6.58 BLOCKED. Phase 2.2 is a shared external dependency blocker across the research/data-ingestion areas. The registry is the source of truth; PRs on old or stacked branches are not completed phases.

## Latest live source/data pipeline evidence (24 October 2026)

- Official-source research [run #15](https://github.com/snchat78-svg/AI-COMP/actions/runs/40067718339) failed closed again after the Phase 2.2 retry hardening was merged. All three official sources were blocked/failed and **0 paper candidates** persisted. DNS resolves, but current RSSB TCP times out, legacy RSSB certificate-validated TLS fails with `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`, and RPSC TCP is unavailable. Do not weaken TLS or create a duplicate discovery implementation.
- Paper processing [run #10](https://github.com/snchat78-svg/AI-COMP/actions/runs/40073489696) was green but reports `processed=0`, `question_candidates=0`, `failed=0`. This is an empty queue, not successful ingestion.
- Official answer-key verification [run #8](https://github.com/snchat78-svg/AI-COMP/actions/runs/40077069998) was green but reports `selected_candidates=0`, `pairs_matched=0`, `extracted_questions_seen=0`, `failed=0`. This is also an empty queue, not verified history.
- [PR #55](https://github.com/snchat78-svg/AI-COMP/pull/55) merged at `8fca0805d64df3eebc5dc8f2a1ac6db0222f4619`; exact tested head passed [workflow 40077507849](https://github.com/snchat78-svg/AI-COMP/actions/runs/40077507849): 548 tests, 14 warnings, API container build passed. It restored missing Phase 6.43 and 6.47–6.51 rows and recorded the latest empty-queue evidence.
- The safe manual workflow added by PR [#54](https://github.com/snchat78-svg/AI-COMP/pull/54) has passing code CI, but a live `REGISTER_AND_FETCH` run is still required. Open [register-and-fetch-official-syllabus](https://github.com/snchat78-svg/AI-COMP/actions/workflows/register-and-fetch-official-syllabus.yml) only after migrations 0024–0026 and the protected `official-source-review` GitHub environment have been configured. Author/reviewer secrets must match Render's server-side values, remain distinct, and never be placed in Git or chat. Use the existing unverified candidate metadata and review the audit/result; the workflow must not mark the source VERIFIED by itself.

**Do not start Phase 6.57 or Phase 2.3 data processing yet.** The next work is still live acceptance within Phase 6.56 / the Phase 2.2 shared source-access gate: retrieve and store actual official PDF bytes on the approved API host, independently inspect the document/version/all pages, complete the reviewed syllabus inventory and mappings, apply required migrations through the controlled workflow, then complete real-data/mobile E2E. Do not treat a successful workflow with zero records as phase completion.

## Full One-Liner coverage requirement

The target is full examinable-point coverage for every applicable subject/topic/subtopic in every supported exam profile—not just meeting a fixed question count. The current catalogue has 340 concept rows across 14 broad subject categories; that is scaffolding, not a complete official syllabus. Final learner-facing One-Liners must be written in question + concise direct answer (Q → A) format, not as bare fact statements. Analyse each topic against its official syllabus and authoritative sources, build a topic-specific checklist of testable knowledge points, draft questions to cover every applicable point, remove duplicates, and track missing points. Five distinct source-backed independently verified Q&As per applicable subtopic is only a minimum floor, not proof of completeness; broad/high-weight topics may require many more. All factual drafts must have source URL and evidence locator and remain NEEDS_REVIEW until an independent reviewer signs them off. No model-generated answer may self-certify as verified. See QUESTION_BANK_CONTENT_COVERAGE.md for the completion checklist and rules.

The CSV ledger currently shows candidate seeds in Git only: 10 pending Q&A across 6 concept IDs; the other 334 catalogue concepts have no candidate in that seed migration. Live database counts have not been queried and are labelled NOT_QUERIED_LIVE_DB.

## Current Phase 6.56 continuation (updated 2026-10-24)

Phase 6.56 remains **IN_PROGRESS**. Do not start Phase 6.57 until the official source, complete reviewed inventory, all concept mappings, controlled live migrations and real-data/mobile E2E gates pass.

- PR #44 (protected syllabus author/reviewer workflow) is merged at `44a1da0ef6c5afd79e81e7367ea57fac15dbfc7c`; tested head passed 517 tests and API-container build (run `39904691212`).
- PR #45 (hierarchical UNIT/TOPIC/SUBTOPIC inventory) is merged at `9694e01c11528157b8a1107fcf78c4c3a1e01ef9`; tested head passed 527 tests and API-container build (run `39906458179`).
- PR #46 (server-side official PDF fetch and immutable SHA-256 evidence) is merged at `ea59fc9e4712b3b646c707e2abf6f30f3690975c`; tested head passed 538 tests and API-container build (run `39907825229`).
- PR [#49](https://github.com/snchat78-svg/AI-COMP/pull/49), branch `phase-6-56-source-fetch-tests-clean`, adds six isolated source-fetch security regression tests on top of current `main`. PR #49 was squash-merged as `a5b4aafed39dee8831b3b2eef2a17832157d77f9`. The final tested head `0bb1e06c50c9525c1520fe501b0afc1407a04f71` passed **544 tests, 14 warnings, and API container build** in [workflow 40061803084](https://github.com/snchat78-svg/AI-COMP/actions/runs/40061803084). PR #48 was closed as superseded because its stale branch history repeated already-merged implementation/migration changes.
- The latest scheduled official-source discovery run [39908982194](https://github.com/snchat78-svg/AI-COMP/actions/runs/39908982194) failed operationally and persisted **zero paper candidates**. Logs show TCP timeouts for the current RSSB host, a legacy TLS renegotiation failure for the legacy RSSB host, and network-unreachable/timeout results for RPSC. Do not weaken TLS or bypass source policy.
- No real RSSB official PDF bytes, version, content digest, complete syllabus inventory or verified exam profile has been confirmed. The source-fetch endpoint is implemented, but it still must be used from an approved deployed API host with outbound network access; the fetched PDF must be independently inspected against the official notification/version.
- Remaining work: controlled migration/secrets gate; successful retrieval of the DB-registered official PDF and review of exact bytes/version/pages; independently reviewed inventory of every unit/topic/subtopic; reconcile missing catalogue concepts and independently review every applicability mapping; then prove real-data/mobile E2E. Phase 6.55 live reviewer-secret/data gates also remain open; Phase 6.58 remains externally blocked.

## Exact next actions at checkpoint creation

1. PR #43 remains the merged exam-profile/syllabus-mapping foundation. Tested head 6841d953be73608e1f0fd59bddfa2f674b639141 passed backend run [39899673677](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673677) (512 passed, 14 warnings + API container) and Flutter/APK run [39899673666](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673666).
2. PR [#44](https://github.com/snchat78-svg/AI-COMP/pull/44) was squash-merged at 44a1da0ef6c5afd79e81e7367ea57fac15dbfc7c. Tested head 4189742e9981f8f0d288e1260bd79b0a3b4d4918 passed workflow [39904691212](https://github.com/snchat78-svg/AI-COMP/actions/runs/39904691212): 517 passed, 14 warnings; API container build passed.
3. Continue within Phase 6.56 with PR [#45](https://github.com/snchat78-svg/AI-COMP/pull/45) was squash-merged at 9694e01c11528157b8a1107fcf78c4c3a1e01ef9. Tested head 7b746257cbf06bc6c9d2a5f96a907ab637834adf passed workflow [39906458179](https://github.com/snchat78-svg/AI-COMP/actions/runs/39906458179): 527 passed, 14 warnings; API container build passed. Migration 0025 adds hierarchical unit/topic/subtopic rows, independent review and a DB guard on inventory completeness.
4. Official RSSB source remains unverified. Secondary transcription [TopKaro CET Graduation Level 2026](https://topkaro.com/rssb/cet-graduation/syllabus) describes Advertisement 09/2026 (1 July 2026) and 14 units, but candidate official PDF https://rssb.rajasthan.gov.in/storage/advertisement_item/1782966142.pdf could not be retrieved in the current runtime. Do not treat the secondary page as official bytes, verified syllabus content or SHA-256 evidence. No real profile is seeded.
5. Next within Phase 6.56: use the already-merged protected source-fetch endpoint from an approved deployed API host with outbound DNS/network; inspect the exact stored official PDF bytes and notification/version; then complete the independently reviewed syllabus inventory and mappings, apply migrations through the controlled workflow, and run real-data/mobile E2E. Do not start Phase 6.57 while any acceptance gate is open.
## Known live-data/security gates

Do not include credentials in Git or chat. Content authoring uses server-side AI_COMP_CONTENT_ADMIN_TOKEN; independent content review requires a different AI_COMP_CONTENT_REVIEW_TOKEN and AI_COMP_CONTENT_REVIEWER_ID. Migration 0021 may demote legacy VERIFIED records without reviewer metadata to NEEDS_REVIEW; review this consequence before applying it. Official-source TLS must not be weakened to bypass the current Phase 6.58 blocker.


## PR #46 merged — next live source verification gate (Phase 6.56 — IN_PROGRESS)

- PR: https://github.com/snchat78-svg/AI-COMP/pull/46; branch `phase-6-56-official-source-fetch`.
- Migration 0026 stores exact fetched PDF bytes and immutable metadata/audit. Reviewer-only fetch uses a DB-owned source URL, strict official-host allowlist, normal TLS verification, redirect revalidation, no environment proxies, time/size limits, PDF validation and server SHA-256. Source review refuses VERIFIED without a matching latest successful server fetch for the same registered URL; latest failed fetch blocks verification.
- Exact-head CI passed: 538 tests, 14 warnings; API container build succeeded (run `39907825229`). PR #46 is merged.
- Actual RSSB PDF is still inaccessible from this research runtime; no official PDF/digest is claimed verified. Use the merged endpoint on an approved API host, inspect the stored exact bytes and official document/version, complete the reviewed syllabus inventory and mapping, then run controlled migration and real mobile E2E. Phase 6.57 stays PLANNED.


## PR #49 — isolated source-fetch security regression tests (2026-10-24)

- PR: https://github.com/snchat78-svg/AI-COMP/pull/49; branch `phase-6-56-source-fetch-tests-clean`.
- PR #49 was squash-merged as `a5b4aafed39dee8831b3b2eef2a17832157d77f9`; final tested head `0bb1e06c50c9525c1520fe501b0afc1407a04f71` passed 544 tests with 14 warnings and the API container build in [workflow 40061803084](https://github.com/snchat78-svg/AI-COMP/actions/runs/40061803084).
- Six additional tests cover deceptive/unsafe URLs, digest and metadata derived from exact PDF bytes, HTML masquerading as PDF, unapproved redirects, size limits and redirect-host validation. Only synthetic PDF fixtures were used; no official syllabus was marked verified.
- PR #48 is closed as superseded because its stale branch compared already-merged implementation history again. PR #49 is based directly on current main and carries only the incremental tests plus this continuity update.
- Next: continue the live source/migration/inventory gates above; do not restart the completed security-test slice. Phase 6.56 remains IN_PROGRESS.

## Latest live-gate evidence (25 October 2026)

- Current main: `dd676617d5c4ac0feb123a309b6ba4984aec531d`.
- Official-source research [run #16](https://github.com/snchat78-svg/AI-COMP/actions/runs/40167821936) failed closed. `RSSB_OFFICIAL` TCP timed out; `RSSB_LEGACY_OFFICIAL` TLS negotiation failed with `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`; `RPSC_OFFICIAL` TCP timed out/network was unreachable. **0 paper candidates persisted.**
- Paper-processing [run #11](https://github.com/snchat78-svg/AI-COMP/actions/runs/40173279948) was job-successful but produced **0 question candidates**.
- Answer-key verification [run #9](https://github.com/snchat78-svg/AI-COMP/actions/runs/40176782796) was job-successful but selected **0 candidates** and matched **0 paper/key pairs**.
- Interpret the latter two as successful no-op/empty-queue runs, not completed processing or verified exam data. Do not advance Phase 2.3, Phase 6.57 or Phase 6.58.
- **Next single operational gate within Phase 6.56:** confirm migrations 0024–0026 have been applied through the controlled migration workflow; configure the protected GitHub Actions environment `official-source-review` with `AI_COMP_SYLLABUS_ADMIN_TOKEN` and `AI_COMP_SYLLABUS_REVIEW_TOKEN` matching the deployed Render service, plus distinct server-side author/reviewer IDs. Never send tokens in chat or commit them. Then manually dispatch the existing `register-and-fetch-official-syllabus` workflow with `REGISTER_AND_FETCH` and a unique `syllabus_id`. Keep the candidate unverified until a human inspects the exact stored PDF, notification/version and all pages. Do not implement another downloader or weaken TLS.

## Phase 6.56 manual official-source fetch workflow — operator runbook

- PR [#54](https://github.com/snchat78-svg/AI-COMP/pull/54) merged at `1b3d1e7534f6bf0802caf396020bca0762c1769f`; tested head `23ae408ccb321b258bd88482b7ad65850984f666` passed [workflow 40073840875](https://github.com/snchat78-svg/AI-COMP/actions/runs/40073840875): 548 tests passed, 14 warnings, API container build passed. This is still Phase 6.56, not Phase 6.57.
- Workflow: `.github/workflows/register-and-fetch-official-syllabus.yml`. It defaults to `DO_NOT_RUN`; an operator must select `REGISTER_AND_FETCH`. It registers only a REVIEW_PENDING candidate through the existing protected endpoint, then calls the already-merged `fetch-source` endpoint using the server-registered URL. It uses an allowlist, normal TLS validation, rejects API redirects, and never prints credentials or raw API response bodies.
- Before manually running it: use the existing `.github/workflows/database-migrations.yml` to apply unapplied migrations 0024–0026 to the verified target DB (secret `AI_COMP_DATABASE_URL`), only after confirming that DB target. Do not create or edit an alternate migration path.
- Create GitHub Actions environment `official-source-review` and add secrets `AI_COMP_SYLLABUS_ADMIN_TOKEN` and `AI_COMP_SYLLABUS_REVIEW_TOKEN`; these must match the Render service's values exactly and be different from one another and from the Phase 6.55 content tokens. On Render, ensure server-side `AI_COMP_SYLLABUS_AUTHOR_ID` and `AI_COMP_SYLLABUS_REVIEWER_ID` are configured and distinct. Never put values in Git/chat/mobile config.
- Run manually from Actions only when the prerequisites are verified: choose workflow `register-and-fetch-official-syllabus`, confirm `REGISTER_AND_FETCH`, supply a unique `syllabus_id`, and retain candidate title/version/notification as unverified until the exact PDF is reviewed. The workflow cannot mark VERIFIED.
- After a successful fetch, independently inspect the stored PDF bytes, notification/issuer/version/date and all pages, inventory every official unit/topic/subtopic, reconcile missing concepts, review every mapping, and complete real mobile E2E. If the fetch fails, keep the candidate pending and inspect the audit before retrying. Phase 6.56 remains IN_PROGRESS and Phase 6.57 remains PLANNED.

## Migration checkpoint update — 25 October 2026

The supplied successful migration run #3 checked out commit `22d0fcb3a5972b241550b5d64de37207dcc651a2`. That exact commit contained only migrations `0001`–`0018`; the log `Applied migration versions: 0018` is historical evidence for migration 0018 only. Current `main` contains `0001`–`0026`, so this run predates migrations `0019`–`0026` and does not prove that migrations `0024`, `0025`, or `0026` are live.

Before starting the workflow again, verify the GitHub Actions secret `AI_COMP_DATABASE_URL` targets the intended Supabase project `ai-comp-db`. Review the known impact of migration `0021`: any existing one-liner with status `VERIFIED` but no independently recorded reviewer identity is reset to `NEEDS_REVIEW`; live affected-row count is unknown. Then, only after that target/impact check, use the existing `.github/workflows/database-migrations.yml` on current `main` with the explicit `APPLY` choice. Do not edit SQL, create an alternate migration workflow, or claim success until the run's exact commit and applied-version output are checked. Phase 6.56 remains IN_PROGRESS, Phase 6.57 remains PLANNED.

## Controlled migration verification update — 25 October 2026

The current-main [Apply database migrations run #4](https://github.com/snchat78-svg/AI-COMP/actions/runs/40190212101) succeeded on commit `dd676617d5c4ac0feb123a309b6ba4984aec531d`. Its job log reports `Applied migration versions: 0019, 0020, 0021, 0022, 0023, 0024, 0025, 0026`. The Phase 6.56 schema migration gate is therefore cleared for migrations 0024–0026; do not rerun migration workflow without a new documented reason.

Migration 0021 also demotes legacy `VERIFIED` one-liners without a recorded independent reviewer to `NEEDS_REVIEW`. The workflow output does not report how many records were affected, so that count remains unknown; do not assume seeded or live content is verified.

Latest documentation PR #57 head `757ad0c56cf51cc5b30d5f580671028a3bd737cc` passed CI in [run #583](https://github.com/snchat78-svg/AI-COMP/actions/runs/40190025937).

**Next single operational gate:** verify the protected GitHub Actions environment `official-source-review` contains `AI_COMP_SYLLABUS_ADMIN_TOKEN` and `AI_COMP_SYLLABUS_REVIEW_TOKEN`, with values matching the deployed API and not equal to one another; verify Render has distinct `AI_COMP_SYLLABUS_AUTHOR_ID` and `AI_COMP_SYLLABUS_REVIEWER_ID`. Do not share secret values in chat. Once those prerequisites are confirmed, use the existing `.github/workflows/register-and-fetch-official-syllabus.yml` workflow with `REGISTER_AND_FETCH`. Its result must remain pending until the fetched PDF bytes, document identity/version and every syllabus page are independently reviewed. Phase 6.56 remains IN_PROGRESS and Phase 6.57 remains PLANNED.

## Live syllabus-fetch incident and next action — 26 October 2026

The first live workflow run passed candidate input validation and created `rssb-cet-graduation-2026-candidate-20261026-01` (`201 Created`). The subsequent API fetch returned `502 SOURCE_FETCH_TIMEOUT`. Render logs confirm both requests; the candidate remains pending and the unsuccessful fetch is audited. Do not reuse its ID with `REGISTER_AND_FETCH`, because that action attempts a new insert.

A fix is being proposed in branch `fix/phase-6-56-retry-existing-syllabus-fetch`: it adds a separately explicit `FETCH_EXISTING` action that retries the protected API fetch for the existing candidate without registering another row. Await exact-head CI and merge before using the new action. If the retry still times out, treat that as a live network/official-host access blocker—not an auth or ID-format issue. Keep TLS verification enabled and use no secondary mirror as official evidence.

Next after the retry: confirm persisted PDF bytes, title, issuing board, notification/version, page count and SHA-256; independently inspect all pages; then complete the full syllabus inventory, evidence-backed concept mappings and real mobile E2E. Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED.

## Diagnostic-link query compatibility — 26 October 2026

Render request logs pinpoint the diagnostic failure: the clicked URL carried `utm_source=chatgpt.com`, so `/diagnostics/official-source-health` returned `400 UNSUPPORTED_QUERY` before running DNS/TCP/TLS probes. A narrowly scoped fix is in branch `fix/source-health-chatgpt-tracking-query`: accept exactly the single `utm_source=chatgpt.com` analytics pair and continue rejecting arbitrary URL/host parameters, different values, or extra/duplicate parameters. Regression tests cover both behavior classes.

After the PR exact-head CI passes and the change is deployed to Render, reopen the existing diagnostic link and inspect `RSSB_OFFICIAL` fields. Then diagnose the real `SOURCE_FETCH_TIMEOUT` according to measured DNS/TCP/TLS outcome. This tracking-query bug is separate from RSSB fetch connectivity and does not prove the PDF was fetched. Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED.

## Latest Render source-health measurements — 26 October 2026

The diagnostic URL compatibility fix reached main as `f49511a3ebca0a875c4ba8bae30f8ed66964e0a5` and Render deploy `dep-dbfea6dg1s2s73a8labg` is LIVE. [Render source-health workflow run #11](https://github.com/snchat78-svg/AI-COMP/actions/runs/40274447472) successfully queried the endpoint and emitted these results before its deliberate connectivity gate failed:

- `RSSB_OFFICIAL`: DNS OK; IPv4 TCP FAIL (`TimeoutError`); TLS NOT_REACHED; no IPv6 records.
- `RSSB_LEGACY_OFFICIAL`: DNS OK; IPv4 TCP PASS; TLS FAIL (`SSLError`); no IPv6 records. Prior measurements identified unsafe legacy renegotiation; do not weaken TLS.
- `RPSC_OFFICIAL`: DNS OK; IPv4 TCP FAIL (`TimeoutError`); IPv6 TCP FAIL (`OSError`); TLS not reached.

No official source currently passes both TCP connectivity and certificate-validated TLS. The workflow failure is evidence of the real source-network blocker, not a failure of the fixed diagnostic URL. Keep Phase 2.2 BLOCKED, Phase 6.56 IN_PROGRESS and Phase 6.57 PLANNED. Candidate `rssb-cet-graduation-2026-candidate-20261026-01` remains `REVIEW_PENDING`; no official PDF bytes/SHA-256 have been verified. Next task: restore or identify an approved, reachable official HTTPS route, then fetch and independently review the exact PDF and complete syllabus inventory.


## User-confirmed Question Bank behaviour — 26 October 2026

Read [QUESTION_BANK_PRODUCT_CONTRACT.md](QUESTION_BANK_PRODUCT_CONTRACT.md) before changing Question Bank code.

- **Old/Previous Year Papers is a separate section.** Actual papers come from official exam/recruitment sources. Registered official sources should be checked on schedule; newly published papers should be added automatically after validation, de-duplication and required review. Keep original paper identity/provenance and pair only the matching verified answer key where available.
- **All remaining topic-wise learning content is One-Liner Q&A.** Navigate Subject → Topic → Subtopic. Cover all examinable points in each applicable official-syllabus topic; write concise question → direct answer, not short notes. Count alone is not completion; missing points, unreviewed drafts and coverage gaps stay visible.
- A paper in Old Papers is not automatically a verified One-Liner. Keep the two lanes separate and use existing repositories/review workflows.
- The live official-source network/TLS gate is still blocked as of 26 October 2026. Automatic new-paper ingestion is the target behaviour but is not yet live-verified. Continue the existing Phase 2.2 / Phase 6.56 blocker; do not claim successful auto-update, weaken TLS, or advance phases based on empty-queue success.


## Current RPSC official archive route finding — 26 October 2026

A code review against the live official RPSC navigation found a concrete path mismatch: the existing discovery seeded `viewcommon?Slice=QP` and `viewcommon?Slice=AK`, whereas the official site exposes [Question Papers](https://rpsc.rajasthan.gov.in/quespapers) and [Answer Keys](https://rpsc.rajasthan.gov.in/answerkeys). Current branch `fix/rpsc-official-paper-archive-routes` corrects those seeds and adds regression coverage. This route fix must pass exact-head CI before merge. It does not make the site reachable from the ingestion runtime; Phase 2.2 / Phase 6.56 source-network gates stay blocked until real official documents are discovered and processed.


## Latest live run after official RPSC route correction — 26 October 2026

PR #64 is merged at `9984f3892a62740840b93db276ae13ec77ca8001`; exact-head CI [40279750490](https://github.com/snchat78-svg/AI-COMP/actions/runs/40279750490) passed pytest and API-container build. It corrects the RPSC crawl seed to official `/quespapers` and `/answerkeys` routes.

The merge automatically started [official-source-research run #18](https://github.com/snchat78-svg/AI-COMP/actions/runs/40279924824), which failed closed and persisted **0 paper candidates**. Measured errors: current RSSB TCP timeout; legacy RSSB TLS failure `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`; RPSC IPv4 timeout and IPv6 network unreachable. This is live runtime connectivity, not proof that the route fix failed. Do not disable TLS or switch to an unofficial mirror.

**Next action:** continue the same blocked Phase 2.2 / Phase 6.56 acceptance gate: find/restore an approved, reachable official HTTPS path for the existing crawler, then demonstrate nonzero real candidates before running paper extraction and answer-key matching. Keep Phase 6.57 PLANNED and do not report Old Papers auto-update as live until an official new-paper end-to-end test succeeds.


## Render source-egress investigation — 26 October 2026

- Render API metadata: service `ai-comp-api`, Free plan, Oregon region, linked to `snchat78-svg/AI-COMP` on `main`. The latest observed deployment `dep-dbff7mu7bikc73c54hkg` was `LIVE` after deploying commit `1db1e06cef6e6cfcd6090678a89e8fd95496b21c`. Deployment/health-check success must not be interpreted as successful upstream paper retrieval.
- Render request logs searched for `/diagnostics/official-source-health` from `2026-10-26T00:00:00Z` to `2026-10-26T12:00:00Z` returned no matching events. Routine `/openapi.json` health checks appeared in app logs; no new DNS/TCP/TLS sample is available from this query.
- Existing explicit evidence remains unchanged: source-health run [#11](https://github.com/snchat78-svg/AI-COMP/actions/runs/40274447472) showed `RSSB_OFFICIAL` DNS OK / TCP timeout, `RSSB_LEGACY_OFFICIAL` TCP pass / certificate-validated TLS failure (`UNSAFE_LEGACY_RENEGOTIATION_DISABLED`), and `RPSC_OFFICIAL` TCP timeout/network failure. Source-research run [#18](https://github.com/snchat78-svg/AI-COMP/actions/runs/40279924824) persisted zero candidates after the RPSC route correction.
- Render's [outbound-IP documentation](https://render.com/docs/outbound-ip-addresses) states that outbound traffic uses region-specific shared IP ranges, with an exception for some old Oregon workspaces. We have not obtained the actual CIDR list for this service, and the current evidence does **not** prove that a government host specifically blocks a Render IP.
- **Next single action:** inspect the service's Render Dashboard **Connect → Outbound** panel, record the listed ranges (never share credentials), and use an authorized official/network contact to verify whether the official endpoints reject or filter that traffic. Do not add proxies, weaken TLS, buy paid egress, or migrate the service without explicit approval and an evidence-backed plan.
- Keep the already-registered syllabus candidate pending; do not re-register or repeatedly retry it while reachability remains unresolved. After an approved route works, use the existing protected fetch workflow, inspect the exact official PDF/version/all pages and SHA-256, complete the full independently-reviewed topic/subtopic inventory and mapping review, then run real mobile E2E.
- **Current gate:** Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. The separate Old Papers auto-update and full-syllabus One-Liner requirements remain unproven in live production data.


## Fresh Render source-egress probe — 26 October 2026, 13:02 UTC

- The user supplied the Render Dashboard outbound CIDRs for `ai-comp-api`: `74.220.48.0/24` and `74.220.56.0/24`. These are region-shared outbound ranges, not a dedicated static IP; see Render's [outbound IP documentation](https://render.com/docs/outbound-ip-addresses).
- PR #66 is merged, and Render deploy commit `2ea757053b5eaa1cda3b037e6ddd5776333645a8` is live (deploy ID `dep-dbfksue7bikc73cbqujg`). The rerun of the existing [Render source-health job](https://github.com/snchat78-svg/AI-COMP/actions/runs/40274447472), job ID `121586949254`, received a fresh non-cached response from the currently deployed endpoint at approximately `2026-10-26T13:02:40Z`. The final workflow gate failed as expected because no official source passed both TCP connect and certificate-validated TLS. The diagnostic did not fetch paper content or modify database records.
- Results: `RSSB_OFFICIAL` DNS OK / IPv4 TCP timeout / TLS not reached; `RSSB_LEGACY_OFFICIAL` TCP PASS / certificate-validated TLS failed with `SSLError`; `RPSC_OFFICIAL` IPv4 TCP timeout / IPv6 TCP failure (`OSError`). These are the same failure classes seen earlier.
- We do not have evidence that the government hosts explicitly block these CIDRs. They are a hypothesis to investigate, not a proven root cause. Do not bypass TLS, add a proxy, purchase dedicated IPs or migrate services without separate approval.
- Next: request verification from an authorized official-host/network contact on whether traffic from the listed outbound ranges is filtered; otherwise, compare an approved reachable runtime/network route before changing architecture. Keep `rssb-cet-graduation-2026-candidate-20261026-01` pending and do not retry until there is route evidence.
- Status is unchanged: Phase 2.2 BLOCKED, Phase 6.56 IN_PROGRESS, Phase 6.57 PLANNED, Phase 6.58 BLOCKED. Old Papers automatic updates and complete independently reviewed One-Liner syllabus coverage remain unproven in live data.


## Next diagnostic increment — general HTTPS control vs official hosts (27 October 2026)

Current Render egress ranges supplied by the user: `74.220.48.0/24` and `74.220.56.0/24` (shared Oregon-region ranges). The fresh Render source-health run [#121586949254](https://github.com/snchat78-svg/AI-COMP/actions/runs/40274447472) still showed current RSSB/RPSC TCP timeouts and legacy RSSB TLS failure. No evidence yet proves an explicit CIDR block.

The current implementation increment adds one fixed, non-user-selectable `example.com:443` control to full source-health reports. It remains outside the official `results` collection; the operational gate still checks only registered official hosts. No page content is fetched; normal certificate validation and all existing host/robots restrictions remain unchanged. The Render source-health workflow will publish the control outcome separately from the official-source table. Single-source diagnostic calls do not probe the extra control host.

Next: merge only after exact-head tests and container CI pass, then inspect the automatic post-deploy Render source-health run. A control PASS combined with official-host failures would narrow the investigation to destination/path-specific reachability; it is not proof of an IP block. A control failure would indicate a broader runtime egress/TLS issue. Keep Phase 2.2 BLOCKED, Phase 6.56 IN_PROGRESS and Phase 6.57 PLANNED until the actual official HTTPS and paper-ingestion gates pass.


## Phase 2.5 fixed HTTPS control — post-deploy evidence (27 October 2026)

- PR [#68](https://github.com/snchat78-svg/AI-COMP/pull/68) merged at `7564cf4b2dcf251098da6e6662fbe159b5993932`. Exact-head [CI run #609](https://github.com/snchat78-svg/AI-COMP/actions/runs/40449133149): **552 passed, 14 warnings**, API container build passed.
- Render deployment `dep-dbg2dlg473hc73fac31g` for that merge is `LIVE`. Render logs show the new `GET /diagnostics/official-source-health` route returned `200 OK` at `2026-10-27T04:22:16Z`.
- The first push-triggered health workflow [#12](https://github.com/snchat78-svg/AI-COMP/actions/runs/40449304879) accepted an older cached payload without the control field; rerunning that existing job (attempt 2, [job 122025472235](https://github.com/snchat78-svg/AI-COMP/actions/runs/40449304879/job/122025472235)) returned `network_control`. The report was marked cached, so its exact original probe timestamp is unavailable.
- Fixed `example.com:443` result: DNS OK, IPv4 TCP PASS and certificate-validated IPv4 TLS PASS; IPv6 TCP FAIL (`OSError`), TLS not reached. In the same report, RSSB current host IPv4 TCP timed out; legacy RSSB TCP passed but validated TLS failed (`SSLError`); RPSC IPv4 TCP timed out and IPv6 TCP failed (`OSError`). The workflow remains red by design because no registered official source passed the TCP + TLS gate. No paper bytes were fetched and no database records changed.
- Interpretation: normal IPv4 HTTPS to the fixed control worked from the Render runtime while official-host connections remained blocked. This is a destination/path-specific failure pattern, **not proof that Render's `74.220.48.0/24` or `74.220.56.0/24` ranges are explicitly blocked**.
- PR [#70](https://github.com/snchat78-svg/AI-COMP/pull/70) merged at `688343ad1cb9f9347d55e0e82a9a47f2092f247f`. CI [#613](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455193390) and current-main [#614](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333691) passed 552 tests (14 warnings) plus API container build. Cross-runtime comparison [#1](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333663) succeeded; Render health report [#13](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333727) is fresh but fails its intentional official-host acceptance gate.
- Both the GitHub-hosted runner and Render report show the same result: fixed `example.com` IPv4 TCP/TLS pass; `RSSB_OFFICIAL` IPv4 TCP timeout; `RSSB_LEGACY_OFFICIAL` TCP pass but TLS `SSLError`; `RPSC_OFFICIAL` IPv4 TCP timeout and IPv6 TCP `OSError`. This is destination/path-specific behavior, not proof of explicit CIDR blocking. Cross-runtime check is diagnostic only; no page/paper content was downloaded and no DB was changed.
- Next: ask an authorized official/network contact to confirm filtering of the listed outbound ranges, or evaluate an approved reachable runtime route after cost/security review. Do not buy static egress, add a proxy, migrate region, weaken TLS or retry the pending candidate just on this evidence.
- Keep the candidate `rssb-cet-graduation-2026-candidate-20261026-01` pending and do not retry until a reachable approved official HTTPS route is demonstrated. Full PDF identity/digest review, complete syllabus inventory and mapping review, and real mobile E2E remain gates. Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED.


## Cross-runtime probe result — 27 October 2026

The merged PR #70 adds a read-only connectivity comparison against the same fixed host set from GitHub Actions and the deployed Render runtime. Exact-head CI #613 and post-merge/main CI #614 both passed 552 tests (14 warnings) and the API container build. The GitHub-hosted comparison [run #1](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333663) completed successfully. Render source-health [run #13](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333727) returned a fresh report and correctly failed its operational gate because no official source passed both TCP and certificate-validated TLS.

Observed from both environments:
- Fixed control `example.com`: DNS OK, IPv4 TCP PASS, validated IPv4 TLS PASS; IPv6 TCP fails with `OSError`.
- `RSSB_OFFICIAL`: DNS OK; IPv4 TCP `TimeoutError`; TLS not reached.
- `RSSB_LEGACY_OFFICIAL`: TCP PASS; validated TLS `SSLError`.
- `RPSC_OFFICIAL`: IPv4 TCP `TimeoutError`; IPv6 TCP `OSError`.

This cross-runtime match makes a Render-only deployment/cache issue less likely, but it does not prove that a government host explicitly blocks the Render CIDRs. The workflows perform DNS/TCP/TLS probes only and do not fetch pages/papers, access the DB, mutate records, or use secrets. Next action is to obtain authorized network-side confirmation or select an approved alternate runtime/egress route after cost/security review. Keep Phase 2.2 BLOCKED and Phase 6.56 IN_PROGRESS; Phase 6.57 and 6.58 cannot advance before the verified source/content gates pass.


## Current blocker and external unblock owner — 27 October 2026

The fixed general HTTPS control `example.com` passes IPv4 TCP + validated TLS from both Render and GitHub-hosted automation; the three official-source endpoints fail with the same pattern across both runtimes. Latest evidence: GitHub-hosted comparison [run #1](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333663), Render source-health [run #13](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333727), and user's Render Outbound panel (`74.220.48.0/24`, `74.220.56.0/24`). This is not proof of an explicit CIDR block; code changes alone cannot authorize or repair a remote official network policy.

External follow-up is tracked in [GitHub Issue #74](https://github.com/snchat78-svg/AI-COMP/issues/74). An authorized operator must request from the official board/network contact confirmation of filtering/rate-limits and, where applicable, an approved reachable official HTTPS hostname/API/CDN or allowlisting path. Publicly listed RSSB IT contact: `itcell.rssb@rajasthan.gov.in`; verify it on the current official contact page before sending.

No email has been sent by this assistant. No proxy, paid service, dedicated IP, or region change has been made or approved. Do not use an unverified `rsmssb.in` or unofficial mirror as an official source; preserve certificate validation and do not retry the pending candidate until an approved route is demonstrated.

**Next exact action after an authorized response:** probe the approved official endpoint from the deployed Render runtime, verify normal certificate-validated HTTPS + robots/allowed paths, run existing official-source discovery and require nonzero genuine candidates; only then proceed to byte/hash review, complete syllabus topic/subtopic inventory and independent mapping review, correct answer-key matching, and mobile E2E. Phase 2.2 stays BLOCKED; Phase 6.56 stays IN_PROGRESS; Phase 6.57 remains PLANNED; Phase 6.58 remains BLOCKED.


## No-contact public-route investigation — 27 October 2026

The user instructed not to call or email. No contact has been sent or initiated. The previously run read-only probes found general IPv4 HTTPS working to `example.com` from Render and GitHub-hosted automation, while official RSSB/RPSC hosts failed with TCP timeouts and the legacy RSSB host failed validated TLS. This does not prove that the Render CIDRs are explicitly blocked.

The next code increment probes two fixed public Rajasthan government portal hosts as connectivity-only diagnostics: `recruitment.rajasthan.gov.in` and `landrevenue.rajasthan.gov.in`. Both appear in government-origin contexts, but neither is assumed to publish question papers. The reports keep these results separate from official exam-source `results`; no generic portal can pass the official-paper acceptance gate by itself. No page or PDF bytes are downloaded by these probes, and all certificate validation stays enabled.

After CI and deploy, review the actual portal host results. For any reachable portal, inspect its public navigation, robots and terms and confirm it directly hosts the exact exam paper/syllabus with official provenance before considering an ingestion path. Do not use unofficial mirrors, contact the Board, weaken TLS, add proxies or buy static egress. Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED.


## Jan Soochna RSSB-papers alternate route — next read-only probe (27 October 2026)

The fresh Render report after PR #76 ([workflow #14](https://github.com/snchat78-svg/AI-COMP/actions/runs/40462219593)) confirmed that `recruitment.rajasthan.gov.in` and `landrevenue.rajasthan.gov.in` are reachable from the Render runtime using certificate-validated IPv4 TLS. The fixed general control `example.com` also passes. RSSB and RPSC official hosts remain TCP-timeout blocked; legacy RSSB still fails standard TLS. This narrows the issue to destination-specific connectivity without proving an explicit IP/CIDR block.

Public Rajasthan Jan Soochna listings expose separate service names for `Question Papers of RSSB` and `Answer Key of RSSB` ([services listing](https://jansoochna.rajasthan.gov.in/Services), [scheme listing](https://jansoochna.rajasthan.gov.in/Scheme)). The pages are currently only a lead, not proof that a paper PDF is directly hosted there.

A fixed Jan Soochna TLS control is being added to the existing read-only diagnostic and workflow summaries. It stays separate from official exam sources. After deploy, if reachable, inspect the public RSSB question-paper service to see whether it serves exact official files from Jan Soochna or links back to the blocked RSSB hostname. Do not guess document IDs, scrape protected endpoints, or treat a general service index as source evidence. No contact has been initiated; no proxies or TLS bypasses are planned.


## Jan Soochna public service inspection — 27 October 2026

The fresh Render diagnostic from workflow [#15](https://github.com/snchat78-svg/AI-COMP/actions/runs/40462990677) confirmed `jansoochna.rajasthan.gov.in` DNS OK, IPv4 TCP PASS and certificate-validated TLS PASS. The same report retained RSSB current-host and RPSC TCP timeouts and a legacy RSSB TLS failure; no official-source candidate was discovered by this diagnostic.

The next implementation adds a separate hidden diagnostic endpoint that:
1. Requests only Jan Soochna's fixed `/robots.txt`.
2. Refuses to read page content if robots is unavailable, invalid, or disallows the chosen user-agent for the page.
3. Reads only public `/Services` and `/Scheme` HTML where robots permits.
4. Parses anchor labels for RSSB Question Papers / Answer Key services. It does not follow those links, fetch a PDF, persist a candidate, or change the official-source registry.
5. Returns only same-host HTTPS link URLs for further public inspection, or a target hostname for external links without following them.

The route has no URL/host parameters, is absent from OpenAPI, bounded by time/size limits, verifies ordinary TLS and is read-only. After exact-head CI and Render deploy, inspect its result. If the service routes back to RSSB, maintain the block; don't use a proxy or bypass. Any directly hosted PDF must pass source identity, access policy, full-byte SHA-256 and independent review before ingestion.


## Jan Soochna diagnostic 404 during Render rollout — 27 October 2026

PR #78 is merged, exact-head CI [run #625](https://github.com/snchat78-svg/AI-COMP/actions/runs/40463742466) passed, and Render began deploying `e72807fa93183ff386622e3b74d010c6521e4291`. Post-merge source-health workflow [run #16](https://github.com/snchat78-svg/AI-COMP/actions/runs/40463899245) succeeded in reading the updated main source-health report, which again showed Jan Soochna TLS PASS; official RSSB/RPSC hosts remain blocked. The next endpoint request got HTTP 404 during rollout, before the new diagnostic route was consistently served. This run therefore has **no robots.txt / service-link finding**.

A follow-up fix branch adds a bounded retry loop to the GitHub workflow for the fixed `/diagnostics/jansoochna-rssb-service` endpoint. It waits for a response with the exact expected phase, hostname, robots object and pages list before continuing. It does not relax robots policy or inspect/download exam files. Do not interpret the previous HTTP 404 as a Jan Soochna policy block.

Current main after PR #78 is `e72807fa93183ff386622e3b74d010c6521e4291`; next task is validate and merge the deployment-retry-only PR, then review the actual robots-gated service-page result. No phone call or email has been sent or initiated.


## Jan Soochna public index result — first robots gate passed (27 October 2026)

Post-PR #79 Render diagnostic workflow [run #17](https://github.com/snchat78-svg/AI-COMP/actions/runs/40464311120) showed that the Jan Soochna public route is reachable and its `robots.txt` permits the `/Services` and `/Scheme` pages. Both returned HTTP 200 and exposed same-host RSSB question-paper service URLs. The workflow intentionally did not follow those links or fetch any paper bytes at that point. The official RSSB/RPSC endpoints remain inaccessible from the Render runtime under normal TLS.

The current implementation extension inspects only the same-host service URLs surfaced by those public index pages, after evaluating robots permission for each exact URL. It does not follow redirects, only reads text/HTML/JSON content, and rejects a PDF/binary MIME type before reading body bytes. It reports PDF-like links from a service detail response but never requests those links. This will decide whether Jan Soochna itself hosts a public PDF link or redirects/references another host.

Current main at this checkpoint is `78ec74b4aa13c5b8992d8e826621cc70d03d73e0`; the detail-inspection changes are in PR preparation on branch `phase-2-5-jansoochna-detail-inspection`. Wait for exact-head CI and post-deploy diagnostic before deciding whether a direct government-hosted document path exists. The question-paper candidate remains unverified. No phone call or email was made.

## PR #80 robots precedence fix — 27 October 2026

The first service-detail inspection implementation failed one regression in [CI run #629](https://github.com/snchat78-svg/AI-COMP/actions/runs/40464857614): Python's `RobotFileParser` used the first matching rule, so a broad `Allow: /Services` could override a more-specific `Disallow: /Services/GetMoreData`. The service URL must not be requested if its exact path is disallowed.

Fix commit `164536a1f84319a60e39b3305895108f97f03e5b` resolves robots permission using the longest matching rule, with `Allow` preferred on equal-length ties. [Exact-head CI run #630](https://github.com/snchat78-svg/AI-COMP/actions/runs/40469616564) passed **565 tests, 14 warnings, and the API container build**. A docs-only follow-up is being recorded in PR #80 and must pass a new exact-head run before merge.

**Next action:** once final exact-head CI passes, merge PR #80 and inspect the post-deploy Render report. If the detail route reports a PDF/binary content type, it must remain unread by this diagnostic. If document-like links appear, they remain metadata only. Do not register a candidate or invoke the protected PDF fetch until a directly hosted official document path and access policy are established. No phone call/email was made. Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED.

## Jan Soochna redirect destination investigation — 27 October 2026

After PR #80's exact-head CI passed (565 tests, 14 warnings, API image build), the deployed diagnostic did not yet expose the `service_link_inspections` schema. PR #81 made that schema mandatory, passed exact-head CI [run #40470380920](https://github.com/snchat78-svg/AI-COMP/actions/runs/40470380920) (565 passed, 14 warnings, API container build passed), and merged at `75b85316bd5ee567722ef51fa90a44cfa2be2c36`.

Post-deploy source-health [run #40470532495](https://github.com/snchat78-svg/AI-COMP/actions/runs/40470532495) now includes real detail-inspection rows. Both Jan Soochna service URLs (/Services/GetMoreData and /Services) are robots-allowed but return `REDIRECT_NOT_FOLLOWED`. The diagnostic did not follow them; no PDF bytes were read. The same run still fails the official-source acceptance check because current RSSB/RPSC connections time out and the legacy RSSB host fails validated TLS.

PR [#82](https://github.com/snchat78-svg/AI-COMP/pull/82) is merged at `ee305969d43bcddd95a0a35074ccb56a7dbb3d84`. Exact-head CI [run #40470902066](https://github.com/snchat78-svg/AI-COMP/actions/runs/40470902066) passed 567 tests, 14 warnings and API container build. Post-deploy Render report [#40471070621, attempt 2](https://github.com/snchat78-svg/AI-COMP/actions/runs/40471070621) recorded both service links redirect to paths on the same Jan Soochna host: `/Services/GetMoreData` → `/Services/ClickablePDF`, and `/Services` → `/Services/GetMoreData`. No redirect was followed; no paper or answer-key bytes were fetched.

PR [#83](https://github.com/snchat78-svg/AI-COMP/pull/83) merged at `9844ff2a21f8f6a34aab410d00bd0f4dbd7c3859`; exact-head CI [#40471579718](https://github.com/snchat78-svg/AI-COMP/actions/runs/40471579718) passed 569 tests, 14 warnings and API container build. Its post-deploy report [#40471826496, attempt 2](https://github.com/snchat78-svg/AI-COMP/actions/runs/40471826496) showed both one-hop target requests return HTTP 302 as well, while remaining on the fixed host.

**Next:** verify PR #83 exact-head CI; merge only if green. Review the post-deploy target status, robots decision and any document links as metadata only. Do not register candidates or start protected PDF ingestion until a direct, authorized official document route and source provenance are confirmed. Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. No email or call was made.

## PR #83 bounded robots-gated redirect inspection — 27 October 2026

The latest live report shows the service links redirect within `jansoochna.rajasthan.gov.in`, not to the registered RSSB host. This proves only the Location header's host/path; it does not prove that an official paper is available. PR #83 inspects one exact same-host redirect destination only after re-evaluating the full target URL against the already-read robots rules, and only for bounded text-compatible content. It still refuses to follow redirects, refuses PDF/binary body reads, and never registers candidates or changes source records.

Expected gates after deploy:
1. Robots disallowed, invalid, or unavailable → no redirect-target request.
2. External/insecure target → no request.
3. Robots-permitted same-host target → at most one bounded request; if target redirects again, report and stop.
4. PDF/binary MIME → report content type only, do not read body bytes.
5. Text/HTML/JSON/plain text → parse links as metadata only; keep all linked files unfetched.

Phase 2.2 stays BLOCKED, Phase 6.56 IN_PROGRESS, Phase 6.57 PLANNED and Phase 6.58 BLOCKED.

## PR #84 second redirect metadata — 27 October 2026

PR [#84](https://github.com/snchat78-svg/AI-COMP/pull/84) adds the second `Location` host/path to the report without following it. The prior live report establishes the first target URLs:
- `/Services/GetMoreData` → `/Services/ClickablePDF` (target responds 302).
- `/Services` → `/Services/GetMoreData` (target responds 302).
The new code inspects only response header metadata and strips query/fragment; it makes no third request. Exact-head CI and post-deploy report are pending. Do not interpret a redirect chain as a verified official paper. No candidate/source-registry/database write occurred.

## PR #85 — ephemeral cookie-session experiment

Main commit `96839e53ab0c94a4c72891f4528b84040608f481` passed exact-head CI [#40472275370](https://github.com/snchat78-svg/AI-COMP/actions/runs/40472275370): 570 tests, 14 warnings and API container build. Live source-health [#40472474696, attempt 2](https://github.com/snchat78-svg/AI-COMP/actions/runs/40472474696) identified a loop:
- `/Services/GetMoreData` → `/Services/ClickablePDF` → `/Services`
- `/Services` → `/Services/GetMoreData` → `/Services/ClickablePDF`

No third request was made and no paper bytes were fetched. Current RSSB/RPSC TCP access fails and legacy RSSB TLS validation fails.

Open PR [#85](https://github.com/snchat78-svg/AI-COMP/pull/85) changes the diagnostic transport to reuse a single in-memory CookieJar within one bounded probe. This tests a hypothesis only; it does not bypass cookies/authentication or follow redirects. Keep fixed HTTPS host constraints, exact robots checks and existing byte/time bounds. If the deployed report still loops, stop this public portal route investigation and continue to treat Phase 2.2 as blocked pending an approved direct official source.

Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. No call/email, proxy, TLS bypass, paper candidate registration or source-registry/database mutation.


## Phase 2.2 continuation — PR #85 deployed, response outcome not yet observed (27 October 2026)

- Current main commit: `1946891bcbd97cf456af430b12b62dcb0580fc25`; Render deployment `dep-dbg5vio473hc73fdsb4g` is LIVE.
- PR #85 test head `c3226b0f195c367fc9f6e5d3de8a73cdcd5467e0` passed [CI run #40473032296](https://github.com/snchat78-svg/AI-COMP/actions/runs/40473032296): 571 tests, 14 warnings and API container build.
- Render app logs show the post-deploy fixed Jan Soochna endpoint `/diagnostics/jansoochna-rssb-service` returned HTTP 200 at `2026-10-27T08:25:08Z` and again at `2026-10-27T08:26:17Z`. These logs contain status only, not the JSON body. A direct read from this workspace failed at DNS resolution, so the cookie-session result is **unknown**, not PASS.
- The last captured pre-cookie report showed the Jan Soochna service URLs cycling between `/Services/GetMoreData`, `/Services/ClickablePDF` and `/Services`; it read no PDF bytes. Do not infer that the cookie experiment succeeded or failed until the corresponding post-deploy GitHub Actions summary has been reviewed.
- No official document bytes, content hash, newly persisted candidate, or verified answer key is established. Phase 2.2 remains **BLOCKED**; Phase 6.56 remains **IN_PROGRESS**; Phase 6.57 remains **PLANNED**; Phase 6.58 remains **BLOCKED**. No email/call has been made.

**Next action:** inspect the latest `render-official-source-health` workflow summary for the post-PR #85 `service_link_inspections`. If the 302 loop persists, stop this Jan Soochna route and continue only with a directly accessible, approved official HTTPS source. Never weaken TLS, proxy around access controls, or register a guessed source.


## Phase 2.2 diagnostic report is now visible — Jan Soochna route stopped at robots gate (27 October 2026)

- Current main: `69d5e9eb98ae0fd42de9d9d4864153be38875f37`, PR [#87](https://github.com/snchat78-svg/AI-COMP/pull/87) merged.
- Exact-head backend/CI workflow [#40501903542](https://github.com/snchat78-svg/AI-COMP/actions/runs/40501903542) passed. Report-only live diagnostic workflow [#40501903388](https://github.com/snchat78-svg/AI-COMP/actions/runs/40501903388) completed. In PR events only, the registered-official-source acceptance step is skipped so the workflow can publish the diagnostic summary; main push and manual runs still enforce the gate.
- Fresh source-health table: fixed general HTTPS control `example.com` IPv4 TCP/TLS PASS; `RSSB_OFFICIAL` TCP timeout; `RSSB_LEGACY_OFFICIAL` TCP PASS but certificate-validated TLS error; `RPSC_OFFICIAL` TCP timeout. The Rajasthan recruitment, Land Revenue and Jan Soochna controls pass IPv4 connectivity only; they are not considered paper sources.
- Jan Soochna service endpoint returned HTTP 200 but safe metadata showed `status=ROBOTS_UNAVAILABLE`, `robots.status=HTTP_ERROR`, and no `service_link_inspections` array. Thus the robots check could not be completed and no service-detail URLs were inspected. Treat this route as unavailable and stop probing it; do not infer a PDF or paper was fetched.
- No PDF/answer-key bytes fetched, no candidate registered, and no database/source registry writes. No email or phone call was made.

**State/handoff:** Phase 2.2 **BLOCKED**; Phase 6.56 **IN_PROGRESS**; Phase 6.57 **PLANNED**; Phase 6.58 **BLOCKED**. Next, evaluate only another directly accessible, officially documented HTTPS endpoint. Validate standard TLS, robots/terms and exact official document provenance before using the existing protected ingestion workflow. No proxy, TLS bypass or guessed source host.


## Phase 2.2 — Render vs GitHub runner comparison (27 October 2026)

PR [#89](https://github.com/snchat78-svg/AI-COMP/pull/89) merged as 3b050227321bb29001c83c85f911537b4b0165d7. Exact-head tests [#40502982570](https://github.com/snchat78-svg/AI-COMP/actions/runs/40502982570) passed, and cross-runtime diagnostic [#40502982762](https://github.com/snchat78-svg/AI-COMP/actions/runs/40502982762) passed in report-only PR mode. Its GitHub-hosted runner probe and Render source-health report agree:

- RSSB_OFFICIAL: DNS OK; one IPv4 address; TCP timeout from both runtimes.
- RSSB_LEGACY_OFFICIAL: DNS OK; one IPv4 address; TCP pass but certificate-validated TLS fails from both runtimes.
- RPSC_OFFICIAL: DNS OK; one IPv4 address; TCP timeout from both runtimes; the GitHub runner also found one IPv6 address but IPv6 TCP failed.
- example.com:443: IPv4 TCP + TLS pass; Rajasthan recruitment and Land Revenue controls also pass connectivity. These controls are not approved paper sources.

This evidence does not support a Render-only egress issue or an untested extra IPv4 record. It does not reveal the cause of the destination-specific failures, so do not guess at or override network controls. Jan Soochna remains blocked before service-link inspection because its robots fetch returns HTTP_ERROR; no PDF or paper bytes were downloaded.

**Next:** pursue only another directly accessible, officially documented HTTPS paper route with normal TLS and a permitted robots/terms policy. Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. No email/phone contact or proxy/TLS bypass.


## Phase 2.2 — Recruitment Portal route investigation started (27 October 2026)

- Branch: `phase-2-2-recruitment-portal-route-probe`, base main SHA `73420ffe112424e725e6011c95bca2e0e66e37d7`.
- Added `src/ai_comp/research/recruitment_portal_probe.py`: only the fixed public Recruitment Portal host is permitted; `robots.txt` must return valid plain text before any public index path is requested; redirects are not followed; PDF/document links are metadata only.
- Added deterministic tests for robots-unavailable fail-closed behavior, robots allow/disallow, same-host/external link classification, query redaction, no document fetching and no DB/source-registry promotion.
- Added an internal, cached, query-rejecting API diagnostic `/diagnostics/recruitment-portal-paper-route` and a post-deploy workflow check to capture the live report on main. PR event skips only this live observation because the new API route is not deployed until merge.
- External-source acceptance remains OPEN: this route is a candidate investigation only. Must not promote a recruitment notice or generic document as a question paper; require official paper provenance, normal TLS/robots permission, actual bytes and SHA-256 through the existing protected fetch path. Current RSSB/RPSC evidence remains unchanged.
- No email/phone contact, TLS bypass, proxy, arbitrary host input, paper bytes, or database/source registry writes were used.

**Handoff:** Continue Phase 2.2 only. Current main `9284de26048a1299b68273c1d97112cbbef40ada`; [PR #96](https://github.com/snchat78-svg/AI-COMP/pull/96) merged and deployed. Treat official RSSB/RPSC PDF URLs found in search as metadata leads only. Next investigate a distinct official host/endpoint that is explicitly linked from the responsible board and accepts normal validated HTTPS from the app runtime. Do not ingest search snippets, parse Jan Soochna HTML as robots, repeat Recruitment Portal's exhausted indexes, weaken TLS, change DNS, use proxies/mirrors, or contact anyone. Phase 2.2 remains BLOCKED until actual official bytes/provenance/hash and nonzero candidates pass; Phase 6.56 IN_PROGRESS; 6.57 PLANNED; 6.58 BLOCKED.


## Phase 2.2 post-merge handoff — 27 October 2026

- PR [#91](https://github.com/snchat78-svg/AI-COMP/pull/91) merged at `0a2d5aef0daa084fbbb5e6f2a281fd38661510f9`; exact-head [CI run #40519631423](https://github.com/snchat78-svg/AI-COMP/actions/runs/40519631423) passed tests and API container build.
- Render deployed that commit. Main live diagnostic [run #40519877289](https://github.com/snchat78-svg/AI-COMP/actions/runs/40519877289): the new fixed recruitment route responds, but its `robots.txt` fetch returns `HTTP_ERROR`; status `ROBOTS_UNAVAILABLE`, `pages_inspected=0`, no paper bytes, no DB/registry writes and no candidates promoted. Do not request its index pages unless `robots.txt` is ordinarily readable.
- Main official-source research [run #40519877291](https://github.com/snchat78-svg/AI-COMP/actions/runs/40519877291): registry sync 2 conducting bodies / 12 exams / 22 paper categories / 3 sources; all registered sources failed/blocked and `paper_candidates_persisted=0`.
- Status remains **Phase 2.2 BLOCKED**, **Phase 6.56 IN_PROGRESS**, **Phase 6.57 PLANNED**, **Phase 6.58 BLOCKED**. Never start Phase 2.3 ingestion or Phase 6.57 acceptance work based on a green diagnostics/test run alone. Next action: evaluate only an independently documented official paper route that is reachable with normal TLS and explicit robots/terms permission; use the existing protected fetch/review workflow once actual paper provenance is established. No proxy, TLS bypass, DNS override, email or phone call.


## Officially listed legacy www-hostname diagnostic — 28 October 2026

The registered sources continue to fail normal network checks from both GitHub-hosted Actions and Render. The latest official-source research run [#40646313134](https://github.com/snchat78-svg/AI-COMP/actions/runs/40646313134) persisted 0 paper candidates: current RSSB and RPSC fail TCP, while the legacy RSSB hostname fails certificate-validated TLS. The general HTTPS control passes, so the evidence does not support treating this as a blanket HTTPS outage.

A government-hosted Rajasthan tender PDF explicitly lists `www.rsmssb.rajasthan.gov.in` as a departmental website alongside `https://rssb.rajasthan.gov.in/` ([official government PDF](https://rsmssb.rajasthan.gov.in/link_to_external_file/e%20bid15052024.pdf)). This change adds the documented `www` hostname only to the fixed diagnostic-control list. It checks DNS, TCP and standard certificate-validated TLS from GitHub Actions and, after deployment, from Render. It does not request a webpage or PDF, add the alias to the exam-source registry, admit candidates, or let this control satisfy the official-source gate.

The new check is a route diagnostic, not a claim that the access restriction has been solved. If the alias passes, a separate review must confirm redirects, public robots/terms, source identity and a directly fetchable paper before using the existing protected fetch/review flow. If it fails too, record that evidence and do not try proxy, alternate DNS, unsafe TLS or access-control bypasses. Phase 2.2 remains BLOCKED until real official document bytes and provenance pass the existing gates; Phase 6.56 remains IN_PROGRESS, Phase 6.57 PLANNED and Phase 6.58 BLOCKED.


## Post-deployment results for the legacy www-hostname test — 28 October 2026

PR [#93](https://github.com/snchat78-svg/AI-COMP/pull/93) merged at `2bac4cb16dd31e96d4861752b29a0c77bc442f47`; exact-head tests [#40688149278](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688149278) and PR diagnostic [#40688149274](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688149274) passed. Render deployed the commit to `live`. The cross-runtime check [#40688511687](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688511687) reports `www.rsmssb.rajasthan.gov.in` DNS `ERROR` with 0 returned address records from both the GitHub runner and Render; therefore this documented historical hostname does not provide a usable route in either tested runtime. No page/PDF was fetched from that alias.

Main source-health [#40688511772](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688511772) and official-source research [#40688511742](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688511742) both failed the unchanged official-source gate. Registered current RSSB and RPSC hosts still fail normal TCP connectivity; the registered legacy RSSB host still fails standard certificate-validated TLS; main research persisted **0 paper candidates**. The existing paper-processing and answer-key jobs being green with empty queues does not complete those stages.

## Next route decision: expose robots.txt HTTP response codes — 28 October 2026

The fixed Jan Soochna and recruitment-portal route diagnostics previously summarised a robots response as `HTTP_ERROR` without printing the exact HTTP status retained in the diagnostic JSON. The workflow now surfaces the status for both routes. For Jan Soochna only, the robots.txt request also prefers plain text while allowing ordinary HTTP content negotiation (`Accept: text/plain, */*;q=0.8`); the response must still have `Content-Type: text/plain` before parsing. This tests whether the restrictive Accept header caused the observed 406; it does not change robots rules, request index pages when robots is unavailable, or change the fail-closed policy.

Decision rule: inspect the exact response before any further route action. A 5xx or network/TLS failure remains unreachable and stays blocked. A 4xx is an RFC 9309 “unavailable” robots response, for which the standard says a crawler *may* access resources ([RFC 9309 §2.3.1.3–2.3.1.4](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.3.1.3)); it does not automatically authorize this application to change its stricter fail-closed policy or override an HTTP access-denial response. Any policy revision must be separately reviewed and explicitly documented before index pages are inspected. No redirects/proxies/TLS weakening, DNS override, calls or email.

Status remains **Phase 2.2 BLOCKED**, **Phase 6.56 IN_PROGRESS**, **Phase 6.57 PLANNED**, **Phase 6.58 BLOCKED** until actual paper bytes and provenance pass existing acceptance gates.


## Latest Phase 2.2 diagnostic checkpoint — 28 October 2026

- Current main at inspection: `e733241a2be558108d12ebe3b8b80e90c421cffa`. Render deployment `dep-dbguqh942hec739cknv0` is confirmed `live`.
- The latest diagnostic change requests robots.txt using ordinary content negotiation (`Accept: text/plain, */*;q=0.8`) but still requires `Content-Type: text/plain` before parsing. It also reports the exact HTTP status, so a response-format issue can be distinguished from a network/server failure. This is a diagnostic hypothesis test, not evidence that the access blocker is solved.
- Latest confirmed official-source research before this change: [run #40688511742](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688511742) persisted 0 paper candidates. Current RSSB and RPSC endpoints failed normal TCP checks; registered legacy RSSB failed certificate-validated TLS; the documented legacy `www` host did not resolve. The new post-deploy route result is not yet independently verified.
- Continue in Phase 2.2 only: retrieve the new fixed-host diagnostic output, record the exact robots HTTP status/content type, then make the documented route decision. Do not fetch index pages when robots is unavailable under the current fail-closed policy. Do not retry candidate ingestion, promote candidates, or start Phase 6.57/6.58 until an approved official HTTPS route returns actual official document bytes and those bytes are independently reviewed.
- No call or email has been made. No proxy, DNS override, unsafe TLS, or unofficial mirror is permitted. Phase 2.2 remains BLOCKED; Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED; Phase 6.58 remains BLOCKED.


## 2026-10-30 Phase 2.2 route continuation

- **Base main:** `6c819bacb7e8c9132f32124ade8435bd8b08fcad` (Render deploy `dep-dbgvhjeq1p3s73beuvh0` is live).
- **Current branch:** `phase-2-2-rbse-paper-archive-control`.
- **New official route lead:** [RBSE 2025 Examination Papers](https://rajeduboard.rajasthan.gov.in/books/PAPERS-2025/index.htm), which indexes Secondary and Senior Secondary papers, including Geography, Physics, Chemistry and Biology.
- **Evidence boundary:** the linked Senior Secondary Geography PDF URL timed out in the available online retrieval environment; `robots.txt` could not be retrieved. No raw PDF, headers, digest, reuse terms or provenance are available. Do not register or ingest this lead yet.
- **Code increment:** add `RAJASTHAN_BOARD_QUESTION_PAPERS_CONTROL` as a fixed DNS/TCP/certificate-validated TLS check in `government_portal_controls`. It must remain outside the registered official `results` collection, cannot satisfy the official-source gate, and must not download pages/papers or write the database.
- **Acceptance sequence:** exact-head backend tests/container build; PR diagnostic from GitHub runner; merge only after CI passes; Render deploy and report must contain the new control; then inspect the probe result. Only if normal TLS succeeds may a later small increment inspect the fixed index and robots policy. RBSE must remain a distinct school-board exam body, never be relabelled RSSB/RPSC.
- **Phase state:** Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. No calls/email, proxy, DNS override, unsafe TLS, or unofficial mirror.


## 2026-10-30 RBSE connectivity and next route probe

- **Main:** `d6a26219aad6462c87ff01ecf2a06bee2f1c8195`; PR #100 merged, Render deployment `dep-dbi3k5ivcj2c73c4ieg0` is live.
- **Connectivity evidence:** RBSE host `rajeduboard.rajasthan.gov.in` DNS OK / IPv4 TCP PASS / validated TLS PASS from GitHub-hosted runner and Render (runs `41014716960`, `41014717223`). Do not infer robots permission from this.
- **Next branch:** `phase-2-2-rbse-robots-index-probe`. It reads only the robots file first; if allowed (or exact HTTP 404), reads one fixed HTML index, and reports metadata for PDF links. It must not follow redirects or download PDFs.
- **No ingestion yet:** no paper bytes, SHA-256, provenance/reuse approval, database candidates, or source admission. RBSE remains distinct from RSSB/RPSC.
- **Phase state:** Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED.


## 2026-10-30 RBSE PDF-level robots and reuse-rights gate

- **Current main:** `9222d2f97f896861a149dc2eb243d99c29eb8a26`; PR #100 and #101 merged; Render deployment `dep-dbi3otss728c73a175tg` live.
- **Live RBSE index result:** source-health run [#41015710994](https://github.com/snchat78-svg/AI-COMP/actions/runs/41015710994) finally returned robots 200 `text/plain`, fixed index allowed, index HTTP 200, and 200 PDF link metadata records (probe cap 200). No PDF bytes downloaded, no database or source registry change, no candidates.
- **Rights review:** official RBSE main page `/main.asp` shows an informational Legal Disclaimer, not a reuse licence. No paper-specific permission/licence has been verified. Do not fetch/store/republish PDF contents until an applicable permission is identified. No calls/emails are to be made.
- **Current branch:** `phase-2-2-rbse-pdf-robots-rights-gate`. It checks robots permission for each same-host PDF path independently; an exact robots 404 exception applies to the fixed index only and does not authorize PDFs.
- **Next gates:** tests/container build; merge; Render deploy; inspect per-PDF robots outcomes; keep PDFs un-fetched absent explicit reuse rights. Keep RBSE separate from RSSB/RPSC.
- **Phase state:** Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED.


## 2026-10-30 live verification after PR #102

- **Main:** `bf7586f907861796f796744bc5a3ef5a365773a9`; PR #102 merged; Render deploy `dep-dbi3tj2vcj2c73c4r3fg` live.
- **CI:** PR run #713 / `41016548039`: 597 backend tests passed and API container build passed. Main push tests #714 / `41016698609` passed.
- **RBSE live route:** Render health run #63 attempt 2 / `41016698624`. robots 200 `text/plain`; fixed index allowed; HTML index 200. First 20 same-host PDF links printed in summary are each `robots_allowed=True`, `PDF_ROBOTS_ALLOWED_NOT_FETCHED`. The report supports up to 200 link records but the summary prints only the first 20. No PDF bytes, DB/source registry changes, or candidate promotions.
- **Competitive sources remain blocked:** official source research run #39 / `41016698619` fails closed; RSSB/RPSC persisted 0 candidates. The separate source-health gate also fails because no registered official competitive source passes TCP + validated TLS. RBSE does not satisfy this gate.
- **Reuse rights:** no applicable paper-specific licence/permission established from the official RBSE site reviewed; its main-page legal disclaimer is informational only. Keep papers un-fetched/unpublished. External link metadata is not a verified paper candidate or question-history evidence.
- **Phase state:** Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED.


## 2026-10-30 continuation — One-Liner generation and complete-topic requirement

- Phase 6.56 remains IN_PROGRESS. The original AI-assisted One-Liner PR #99 had green backend and Flutter CI, but GitHub rejected its merge due to stale-branch conflicts. Its implementation is being reapplied to current `main` in `phase-6-56-one-liner-candidates-mainline`; do not merge the stale PR #99.
- The authoring route accepts only an authorized editor's bounded source excerpt and an existing canonical concept ID. Gemini drafts question → direct answer pairs; exact evidence/answer quotes must appear in the supplied excerpt; duplicates are filtered; new records are always `NEEDS_REVIEW`. Learner reads remain limited to independent `VERIFIED` content.
- User requirement: every applicable subject must be browsable as **Subject → Topic → Subtopic**, with all examinable points in every selected exam's official syllabus covered. The five-Q&A minimum is only a baseline, never a completion rule. Use the persistent 340-row/14-subject starter ledger only as scaffolding; reconcile it to each official syllabus, add missing concepts, and keep uncovered topics visible.
- One-Liners remain separate from Old Papers. Papers must be authentic official artifacts; paper questions are not automatically One-Liners. AI output cannot self-verify or count as covered until independent review passes.
- Phase 2.2 remains BLOCKED: the deployed RBSE index and first 20 listed same-host PDF paths passed robots checks, but no PDF bytes or reuse licence has been verified. RSSB/RPSC remain unreachable/failed validated TLS, and official-source research run #40 persisted zero candidates. No email/phone contact, proxy, TLS bypass or robots bypass.
- Next: exact-head backend tests + API container, then merge only if current-main PR checks pass; configure no secrets in Git; do not mark Phase 6.56 complete until official exam profile, syllabus inventory/mappings, live DB state and authentic mobile E2E are proven.


## 2026-10-30 continuation — topic-wise One-Liner quality gate merged

- Main includes PR [#104](https://github.com/snchat78-svg/AI-COMP/pull/104) at `43e5209f70e729e7f68af9e4931e9ed529d08e0f`: bounded source-grounded Gemini candidate generation for one canonical concept at a time. All generated items remain `NEEDS_REVIEW`.
- Main includes PR [#105](https://github.com/snchat78-svg/AI-COMP/pull/105) at `b68043fbc6b18616bbe75a31abd3b63977addc5a`: deterministic Q&A format gate (one terminal `?` or `？`, no line breaks, <=240 characters in each field, and no question mark in the answer), stronger Gemini instruction and Hindi/English regression cases.
- Exact-head commit `e7957a81573093f77a6d7f97b82d3b3e98239971`; GitHub Actions [run #721](https://github.com/snchat78-svg/AI-COMP/actions/runs/41025914983) passed **620 tests, 14 warnings**, and the API container build. This was a backend-only change; it did not prove a mobile E2E run or live content generation.
- Next within Phase 6.56: add examinable-point coverage dimensions, topic-level near-duplicate checks and reviewer batch audit counts. Do not use question count alone as a completeness signal.
- Phase 2.2 remains BLOCKED; Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED; Phase 6.58 remains BLOCKED. Official source bytes/reuse rights, complete reviewed syllabus mapping, live migrations/secrets and real-data mobile E2E are still outstanding. No email/calls, proxy, DNS override, TLS/robots bypass or unlicensed PDF use.


## 2026-10-30 — Current in-progress Phase 6.56 increment (PR #107)

- PR: [#107 — topic-level One-Liner near-duplicate guard and batch audit](https://github.com/snchat78-svg/AI-COMP/pull/107), branch `phase-6-56-topic-batch-audit`.
- Adds bounded duplicate scan of existing Q&A for the same concept/language across review states, deterministic Unicode-aware near-duplicate triage, same-batch duplicate checks, and separate generated/rejected/duplicate/pending-review/verified audit counts.
- Database exact-hash uniqueness remains in place. Incomplete scan or >5,000 existing items fails closed. Candidate generator cannot self-verify; all generated items remain `NEEDS_REVIEW`.
- Backend Actions run [#730](https://github.com/snchat78-svg/AI-COMP/actions/runs/41061934522) passed full pytest and API container build on initial PR head. Flutter run [#144](https://github.com/snchat78-svg/AI-COMP/actions/runs/41061934507): analyze and mobile tests passed; release APK build/artifact validation were still running at this checkpoint. Recheck the latest head and both workflows before merge.
- Next within Phase 6.56 after this increment: reviewer-facing examinable-point coverage checklist/gap report. Full parent-phase acceptance still needs the official exam profile/document bytes and SHA-256, complete independently reviewed syllabus inventory and mappings, controlled live migrations/secrets, and authentic-data mobile E2E.
- Phase 2.2 remains BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. No source-access bypass, no unlicensed paper reuse, no contact attempts.


## 2026-10-31 restart — full-topic One-Liner coverage worklist

- Latest main was checked first: PR #107 is merged; Phase 6.56 remains IN_PROGRESS, Phase 6.57 remains PLANNED, Phase 2.2 remains BLOCKED and Phase 6.58 remains BLOCKED.
- PR #106's backend and Flutter CI passed on its own head, but its base was before PR #107. Its dimension-tag code is being reapplied on current main in PR #108; do not merge the stale PR #106 branch.
- The new `QUESTION_BANK_EXAMINABLE_POINT_MATRIX.csv` represents all 340 Git catalogue concepts against 13 examinable-point lenses: 4,420 review rows. All rows start `NOT_ASSESSED`; the matrix is not a question count and not a live database result.
- Generator tags are reviewer aids only. The authoring response returns tags for saved candidates; each candidate stays `NEEDS_REVIEW` until independent human approval. Learner reads remain VERIFIED-only.
- The authoring path remains one concept at a time and requires checked source text/evidence. It does not fetch arbitrary URLs or generate unsupported factual answers from model memory. Catalogue topics must be reconciled against a selected exam's exact official syllabus before exam-specific completeness can be asserted.
- Next: run exact-head PR #108 backend pytest/API-container and Flutter/APK workflows. Then author content in bounded, evidence-backed batches beginning with applicable high-gap concepts; update each matrix row with evidence and accepted Q&A IDs. Keep Old Papers separate.
