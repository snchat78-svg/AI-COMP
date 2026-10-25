# AI-COMP Project Continuity Checkpoint

**This file is the first-read checkpoint for every new AI-COMP chat/session.** Do not restart from conversation memory alone. Check the repository state in GitHub because it is the shared durable record.

**Last updated:** 2026-10-25 (main `dd676617d5c4ac0feb123a309b6ba4984aec531d`; live source run #16 blocked; downstream empty-queue runs #11/#9 verified; Phase 6.56 remains IN_PROGRESS)  
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

The supplied successful migration run #3 checked out commit `22d0fcb3a5972b241550b5d64de37207dcc651a2`. That exact commit contained only migrations `0001`–`0018`; the log `Applied migration versions: 0018` is historical evidence for migration 0018 only. Current `main` contains `0001`–`0026`, so this run predates migrations `0019`–`0026) and does not prove that migrations `0024`, `0025`, or `0026` are live.

Before starting the workflow again, verify the GitHub Actions secret `AI_COMP_DATABASE_URL` targets the intended Supabase project `ai-comp-db`. Review the known impact of migration `0021`: any existing one-liner with status `VERIFIED` but no independently recorded reviewer identity is reset to `NEEDS_REVIEW`; live affected-row count is unknown. Then, only after that target/impact check, use the existing `.github/workflows/database-migrations.yml` on current `main` with the explicit `APPLY` choice. Do not edit SQL, create an alternate migration workflow, or claim success until the run's exact commit and applied-version output are checked. Phase 6.56 remains IN_PROGRESS, Phase 6.57 remains PLANNED.
