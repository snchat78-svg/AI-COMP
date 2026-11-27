# AI-COMP Project Continuity Checkpoint

**This file is the first-read checkpoint for every new AI-COMP chat/session.** Do not restart from conversation memory alone. Check the repository state in GitHub because it is the shared durable record.

**Last updated:** 2026-11-27 (main checkpoint `d45c738bba63be610c88078a9c227cd228c9e072`; active branch `content/phase6-56-ahb-source-corrections-041-042`). Phase states: 6.56 IN_PROGRESS, 6.57 PLANNED, 6.58 BLOCKED. Active parent remains Rajasthan History book Chapter 2; 392 candidates are review-pending, not verified.
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

## User priority — Study Notes first (2026-11-10)

The user has set the immediate content priority: before adding more MCQ generation, topic tests, mastery or revision features, build concise **Subject → Topic → Subtopic → One-Liner Question + Direct Answer notes** that cover the full set of examinable points.

- Follow the 14 existing subject categories and concept order in `docs/QUESTION_BANK_CONTENT_COVERAGE.csv`; do not create a parallel taxonomy.
- First slice: Rajasthan History → Book Chapter 2 “राजस्थान के प्राचीन सभ्यता स्थल”.
- Canonical notes file: `docs/study-notes/rajasthan-history/ancient-history/ancient-civilization-sites.md`.
- Child-sites retain the concept IDs from `docs/QUESTION_BANK_CONTENT_COVERAGE.csv`; Kalibanga and Ahar-Banas are not separate main book chapters.
- PR #112 merged at `949ee0baf4ba7cadf0abe75b1319348617d04d22`, adding notes-first workflow and 34-topic Rajasthan History index.
- PR [#113](https://github.com/snchat78-svg/AI-COMP/pull/113) is merged and contributes KAL-001–KAL-287. Review branch `content/kalibangan-single-topic-hierarchy-structure` extends the same canonical topic file with KAL-288–KAL-304, bringing the branch total to 304 primary AI-authored Q&A drafts, 3 separately labelled corroborative items and 2 ASI Jodhpur Circle site photographs.
- Every item remains `NEEDS_REVIEW`; parent Chapter 2 remains DRAFTING / NOT COMPLETE. No exam-specific official syllabus mapping is claimed.
- Every note needs a reliable source URL and precise evidence locator. Keep disputed facts visible/excluded. Only independent review can approve a factual candidate.
- Generate practice MCQs from reviewed notes afterward. Keep real past-paper questions and generated practice questions separate.
- Do not start Phase 6.57 early. Phase 6.56, Phase 2.2 and Phase 6.58 retain their existing acceptance gates.

### Kalibangan content expansion — 2026-11-10

- Reviewed PR #112's merged content and the 34-topic Rajasthan History tracker before continuing; no subject/topic sequence was skipped.
- Draft PR [#113](https://github.com/snchat78-svg/AI-COMP/pull/113) is open on branch `content/kalibangan-full-topic-coverage-asi`.
- Added KAL-065 through KAL-142: fabrics A–F, construction phases and houses, museum gallery evidence, mature pottery and graffiti, copper assemblage and source hypothesis, crops/animal traction, gypsum interpretation, querns/kitchen tools, bead types, measuring devices, shell and textile objects, small finds, animals/birds, games, drainage pipes and detailed cemetery/burial evidence.
- Added 2 direct image links from the official ASI Jodhpur Circle museum page (excavation trench; present-day KLB-2) with credit and reuse-permission caution.
- Added explicit authorship statement: Hindi question wording is AI-authored in new phrasing; answers are sourced paraphrases; these are not copied verbatim questions and are not PYQs. All are NEEDS_REVIEW.
- Recorded two source issues rather than hiding them: museum establishment year differs between Rajasthan Tourism (1983) and ASI Jodhpur Circle (1985); ASI Part II Ch. 14's parenthetical gloss for Cicer arietinum needs botanical/expert review.
- Still open: review ASI Part I / Early Harappan monograph (official catalogue entry found, but 17 MB PDF download exceeds the current reader size limit), detailed seal and script corpus, lithic-tool typology, full faunal evidence, small finds, figures/plans/plates, duplicates against live question bank, independent verification, and exam-syllabus applicability. Do not mark topic complete or start Ahar-Banas until these are reconciled.
- No production database, One-Liner review API or APK content has been changed. This remains documentation research; the learner-facing database is not populated by this PR.
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


## 2026-10-30 — Phase 6.56 topic-level duplicate guard and batch audit merged (PR #107)

- PR [#107](https://github.com/snchat78-svg/AI-COMP/pull/107) was squash-merged as `0f8da54ca22ec5e76857587e92df2a9913b92521`; branch `phase-6-56-topic-batch-audit`.
- Implementation/test head `49feab1ce05ec712415b208c141d74fdab0d3b7d`: backend workflow [#730](https://github.com/snchat78-svg/AI-COMP/actions/runs/41061934522) passed full pytest and API container build; Flutter workflow [#144](https://github.com/snchat78-svg/AI-COMP/actions/runs/41061934507) passed analyze, mobile tests, release APK build, APK verification and artifact upload. APK artifact [12980571357](https://github.com/snchat78-svg/AI-COMP/actions/runs/41061934507/artifacts/12980571357), SHA-256 `acf231349a7735a485748463bf5eb571a4587cb2a470a58449a644959cb042a8`.
- Render deployment `dep-dbi9khqa6svs738okt7g` for main commit `ee1a0d6f5ff8c9c778c0b01adba74a9045b564bf` (which includes the PR #107 merge) completed with status `live` at 2026-10-30 13:24:26Z.
- Same-topic/language near-duplicate scan, same-batch checks and separate generated/rejected/duplicate/pending-review/verified batch counts are now in main. Exact PostgreSQL content hash remains the final concurrent-duplicate guard. Scan failure or more than 5,000 existing topic records fails closed. Generated output remains `NEEDS_REVIEW`, never self-VERIFIED.
- Next within Phase 6.56: build the reviewer-facing examinable-point coverage checklist/gap report. Do not use generated question count as proof of full topic coverage.
- Parent-phase gates still open: official exam-profile/document identity and actual bytes/SHA-256, complete independently reviewed unit/topic/subtopic inventory, all concept mappings, controlled migrations/author-review secrets, and authentic-data mobile E2E. Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. No source-access or copyright bypass, no email/calls.




## 2026-10-31 — Phase 6.56 examinable-point coverage continuation

- Base main at branch start: `83841e01ef1a6a60d1d5a2a72daa53c70def9579`; latest confirmed Render service deploy before this documentation-only branch: `dep-dbi9lq2f2vlc73e1l940`, status `live`, commit `83841e01ef1a6a60d1d5a2a72daa53c70def9579`.
- Started branch `phase-6-56-examinable-point-coverage`; added `docs/PHASE_6_56_EXAMINABLE_POINT_COVERAGE.md` and linked it from the Phase 6.56 mapping doc. Contract defines point-level coverage dimensions, raw counters, reviewer gates, incomplete-inventory output and fail-closed semantics.
- This increment is documentation only. It does not create a new API/schema, does not certify any syllabus, and does not alter Render. Next implementation task: inspect existing inventory and One-Liner review tables; design additive examinable-point/dimension storage and read-only gap report; add synthetic-fixture tests for missing mappings/dimensions, draft-only/duplicate/rejected items, incomplete inventory and empty denominator.
- Current phase state unchanged: Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. Do not skip to Phase 6.57. No email/phone, TLS/robots bypass, proxy or unlicensed document use.


## 2026-11-08 continuation — Phase 6.56 examinable-point implementation started

- **Verified main:** `0f4c9607e8c2a29ac028131c8df580623fa13dde`. Branch `phase-6-56-examinable-point-gap-report` started from this exact main head.
- **Official-source blocker:** [research run 42349804271](https://github.com/snchat78-svg/AI-COMP/actions/runs/42349804271) failed closed on 2026-11-07; RSSB requests timed out, RPSC was network-unreachable, and 0 paper candidates persisted. No access control, robots or TLS bypass used; no calls/emails.
- **Phase 6.56 implementation proposal:** migration 0027 adds point, multi-concept mapping, nine dimensions and point-to-verified-One-Liner link tables; API routes provide protected author/reviewer workflows, inventory attestation/reopen and paginated gap reporting. Only exact point-linked, independently verified One-Liners count. Historical question linking is explicitly not implemented in this increment and remains a separate pool.
- **Data policy:** tests use synthetic fixtures only. No real profile or official syllabus is seeded, no old-paper/one-liner pool is merged, and no completion percentage is shown while source/inventory gates are incomplete.
- **Status:** implementation branch and synthetic tests prepared; exact-head CI, SQL migration execution, deployment, Flutter/mobile parity and official data verification are still pending. Phase 6.56 remains IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED; Phase 2.2 BLOCKED.
- **Next action:** PR review and exact-head CI; repair any failing tests/schema before merge. Then run migration through the existing database workflow only after CI is green; do not advance Phase 6.57 until all Phase 6.56 parent gates are met.



## 2026-11-08 — latest connectivity and Phase 6.56 verification (PR #111)

- PR [#111](https://github.com/snchat78-svg/AI-COMP/pull/111), branch `phase-6-56-examinable-point-gap-report`, exact head `d43ef8d33380b29a52c97a2dece93de0e65d471c`, remains OPEN / NOT MERGED.
- Backend exact-head [run #746 / 42450211828](https://github.com/snchat78-svg/AI-COMP/actions/runs/42450211828): **645 passed, 14 warnings**; API container build PASS. The migration integration test ran through the repository migration runner against the ephemeral CI PostgreSQL service; all four new tables and selected trigger invariants passed. No production database migration was run.
- Exact-head source diagnostics [run #72 / 42450211838](https://github.com/snchat78-svg/AI-COMP/actions/runs/42450211838) completed: Render-side RSSB current + legacy IPv4 TCP timed out; RPSC IPv4 TCP timed out and IPv6 unreachable. The fixed `example.com` control passed validated IPv4 TLS and the general recruitment portal control had a passing IPv4 TCP/TLS address, but this did not open the registered RSSB/RPSC sources.
- The fixed recruitment public-index inspection read three HTML paths and found no paper or answer-key links; robots.txt was not published (HTTP 404), which is not itself permission to fetch or reuse documents. Jan Soochna RSSB service route returned `ROBOTS_UNAVAILABLE`; RBSE archive route returned `ROBOTS_UNAVAILABLE` on this run. No PDF bytes fetched; no source registry/database changes; 0 candidates promoted.
- Conclusion: general HTTPS egress works to a control host, while the registered RSSB/RPSC endpoints remain destination/path-specific blocked from the deployed runtime. Do not use proxy, DNS override, unsafe TLS, robots bypass, or mirrors. Phase 2.2 stays BLOCKED.
- PR #111 implements point-level records, reviewer-separated authoring, nine assessment dimensions, exact point-linked VERIFIED One-Liner coverage with content-hash de-duplication, inventory attestation/reopen and read-only gap report. Coverage stays UNKNOWN when source/inventory gates are incomplete. Old Papers remain separate; historical-paper point linking and Flutter/mobile report UI remain future slices.
- Phase 6.56 remains IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. PR review/merge, production migration, production deploy, mobile parity and authentic official-data validation remain open.


## 2026-11-10 — Kalibangan ASI Part II research checkpoint

- User-directed content priority remains subject → topic → subtopic One-Liner notes before MCQ/test expansion. Continue the existing Kalibangan topic; do not move to Ahar-Banas yet.
- PR [#113](https://github.com/snchat78-svg/AI-COMP/pull/113), branch `content/kalibangan-full-topic-coverage-asi`, currently carries **160 primary AI-authored Q&A drafts (KAL-001–KAL-160)**, 3 separately labelled corroborative points and 2 ASI-hosted Jodhpur Circle images. All candidate items remain `NEEDS_REVIEW`; status DRAFTING / NOT COMPLETE.
- New source pass: ASI MASI catalogue lists the Kalibangan Early Harappan report (MASI 98), and *Excavations at Kalibangan — The Harappans (1960–69), Part I and Part II*. The catalogue was read. Part II Chapter 11 “Lithic Tools” (printed pp. 723–765) and Chapter 13 “Ivory and Bone Objects” (printed pp. 809–835) were examined at text level and yielded KAL-143–KAL-160.
- Lithic draft coverage now includes the Early/Mature Harappan presence, jasper/agate/chalcedony small-blade industry, chert long blades, parallel-sided blades, lithic assemblage forms, pressure/percussion flaking, prismatic cores, Crested Guiding Ridge technique and cautious author-attributed interpretations of possible tool functions/wooden sickles.
- Bone/ivory draft coverage now includes the report's count of 392 objects/materials including fragments/raw material/waste, evidence the authors interpret as local manufacture, object categories and four ivory combs (three described/illustrated).
- **Access/visual limitation:** the official Part I and MASI 98 PDF endpoints returned large files (~17–19 MB) beyond the reader's size limit. The Part II browser screenshot tool also failed on the large PDF; page-image/plate verification is therefore still open. Do not pretend the full reports or plates were inspected. ASI Part II itself includes a disclaimer that object identifications/descriptions are the authors' responsibility; preserve interpretations as attributed.
- Remaining Kalibangan gates: full Part I/MASI 98 review; seals and sign corpus; complete faunal evidence; remaining small finds; plan/figure/plate cross-check; resolve or explicitly retain conflicts; scan exact/semantic duplicates against live question-bank data; verify selected exam syllabus mapping; image reuse permission; independent reviewer approval. No learner publication or VERIFIED count is claimed.
- No Phase 6.x code, database, secrets, APK or app data was changed in this research-only increment. Phase 2.2 remains BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. Do not skip phase gates.
- Next exact action: continue normal, official-source review for Part I/MASI 98 and seals/fauna/small finds; then complete plan/plate checks and independent review. Keep Ahar-Banas NOT STARTED until Kalibangan is accepted.


## 2026-11-10 — Kalibangan seals, faunal and archaeobotanical checkpoint

- Current content branch `content/kalibangan-full-topic-coverage-asi`, PR [#113](https://github.com/snchat78-svg/AI-COMP/pull/113), now has **177 primary AI-authored Q&A drafts (KAL-001–KAL-177)**, 3 separately labelled corroborative points and 2 ASI Jodhpur Circle images. All primary and corroborative candidates remain `NEEDS_REVIEW`; the topic remains DRAFTING / NOT COMPLETE.
- New source S10: Zoological Survey of India, *Annual Report 2021–22*, project “Zooarchaeology of Faunal remains of Kalibangan” (printed pp. 34–35). It reports 5,230 fragmentary specimens, 36 species, 30 genera, 18 families, 11 orders and 5 classes; mostly domestic cattle, buffalo, sheep, goat, camel and fowl; dietary-waste context and charring/cut/chopping traces; and selected wild fauna including deer, rhinoceros and gaur plus turtle/molluscan remains. Used for KAL-169–KAL-174.
- New source S11: ASI, *Indian Archaeology 1974–75 — A Review* (published 1979), printed p. 79. Vishnu-Mittre and R. Savithri's re-examination of plant remains in Kalibangan terracotta cakes and pai identifies barley and, in a few cases, wheat; absence of rice epidermis and rice's characteristic chess-board pattern leads them to challenge the previous rice identification. This creates a documented disagreement with the ASI Jodhpur Circle museum page crop list; no final resolution claimed. Used for KAL-175–KAL-177.
- New source S12: B. B. Lal, “Some Aspects of the Archaeological Evidence Relating to the Indus Script”, *Puratattva* No. 7 (1974), printed pp. 22–23. It discusses two overlapping inscribed Kalibangan potsherds, Lal's right-to-left direction inference, possible boustrophedon second lines, seven repetitive-legend clay sealings in the citadel, use of seals and materials carrying inscriptions, and a tentative V-like sign/vase interpretation. Used for KAL-161–KAL-168, with all interpretations clearly attributed to Lal (not definitive script decipherment).
- PDF text/lines opened and inspected; screenshot renderer timed out on the ASI annual review and rejected the large Puratattva PDF due size. No visual plate-image verification is claimed.
- Existing limitations persist: Part I and MASI 98 PDFs exceed the reader size limit; complete plate/plan inspection, live question-bank duplicate check, source review by an independent reviewer, image-use permissions and exam-specific syllabus mapping remain open. All candidates NEEDS_REVIEW.
- No app code, database, migration, secret, APK, or learner-visible content was changed. This is content research/documentation only; automated application tests not run. Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED.
- Next: audit Part I/MASI 98 and the remaining seal/sign/archaeobotanical material through normal official/academic source access; continue small-find and visual plan/plate review; then independent review. Do not move to Ahar-Banas until Kalibangan's coverage gate closes.


## 2026-11-10 — Kalibangan faunal phase linkage addendum

- Added KAL-178 from ZSI *Annual Report 2021–22*, printed p. 35: ZSI associates the studied faunal remains with both pre-Harappan and Harappan cultural phases.
- Current Kalibangan branch count is **215 primary AI-authored Q&A drafts (KAL-001–KAL-178)**, plus 3 corroborative items and 2 photos. All remain NEEDS_REVIEW / DRAFTING; no phase or application status changed.


## 2026-11-10 — ZSI faunal monograph lead (not yet reviewed)

- A specialist book catalogue lists Supriya Nandy, *Zooarchaeology of Faunal Remains of Kalibangan, Rajasthan: An Indus Valley Site*, ZSI Occasional Paper No. 430 (2026), ISBN 9788199884809. Listed contents include domestic species, wild/free-living species, bone modification and bone measurements.
- This is an unverified bibliographic lead from a distributor listing only; the book text has not been obtained or read, and no Q&A relies on it. ZSI's digital archive page returned a retrieval error in this research pass.
- Next source action: locate an authorized ZSI/library copy, inspect the species tables and bone-modification/measurement sections, and reconcile them with the ZSI Annual Report 2021–22 before any additional faunal Q&A are drafted. Current total remains 178 primary Q&A; all NEEDS_REVIEW.


### 178-Q&A draft integrity check

- Fetched the exact current Kalibangan notes file from the working branch and audited its Markdown Q&A rows: **178 rows, IDs KAL-001–KAL-178, no missing or repeated IDs, no malformed four-field rows**.
- Ran an in-file exact/normalized duplicate scan using Unicode NFKC normalization, case folding, punctuation removal and whitespace normalization. No normalized duplicate question or exact normalized Q&A pair was found within this 178-item draft.
- This is not a semantic similarity review and does not query the live production question-bank records. Live exact/semantic duplicate reconciliation and separate human fact-review remain required; do not mark any item VERIFIED.


## 2026-11-10 — Kalibangan corpus-level seals and staged faunal progress

- Current notes branch `content/kalibangan-full-topic-coverage-asi`, PR [#113](https://github.com/snchat78-svg/AI-COMP/pull/113), contains **215 primary AI-authored Q&A drafts (KAL-001–KAL-188)**, 3 separately labelled corroborative points and 2 ASI Jodhpur Circle photographs. Every candidate remains `NEEDS_REVIEW`; Kalibangan remains DRAFTING / NOT COMPLETE.
- New source S13: *Corpus of Indus Seals and Inscriptions*, Vol. 1, ASI Memoirs No. 86 (1987), edited by Jagat Pati Joshi and Asko Parpola. It lists Kalibangan catalogue references K-1 to K-122 on printed pp. 298–326. This is a corpus-reference range, not a count of seals; K-122 is specifically categorised as “Miscellaneous — copper objects” (p. 326).
- New source S14: Iravatham Mahadevan, *The Indus Script: Texts, Concordance and Tables*, ASI Memoirs No. 77 (1977). It describes Kalibangan seal 8011 as pink terracotta with a boss on the reverse, two lines of text and a left-facing rhinoceros field symbol in relief; Mahadevan classifies it as a separate “raised seal” subtype. It also records his 1976 revision of sign lists after unpublished Lothal/Kalibangan texts became available and his rule of relying on original objects or mechanically reproduced originals.
- New source S15: ZSI Annual Reports 2018–19 and 2020–21. The 2018–19 snapshot records 11 Mammalia, 1 Aves and 2 Reptilia species; the 2020–21 snapshot records 1,075 specimens, 19 species, 9 families and 6 orders. Both mark the project ongoing. The completed 2021–22 result (5,230 specimens, 36 species) remains separately recorded; these are date-specific project milestones.
- **Terminology correction:** ASI's official list separates (1) *Excavations at Kalibangan: Early Harappans* (MASI No. 98, 2003) from (2) *Excavations at Kalibangan: The Harappans (1960–1969), Part I* (a Mature Harappan report in the MASI No. 110 series). Their large official PDFs are about 19.5 MB and 17 MB respectively and exceed the reader size limit. Neither full report is claimed as reviewed. The Part I table of contents names separate chapters on inscribed material and crafts, but no facts are drafted from those inaccessible chapter contents.
- Integrity audit of current notes: 188 Q&A rows; continuous unique IDs KAL-001–KAL-188; zero malformed rows; no duplicate normalized questions or exact normalized Q&A pairs within this file (Unicode NFKC, case-fold, punctuation and whitespace normalization). This is not a semantic scan against the live database or independent review.
- PDF screenshots of the Corpus, Mahadevan scan and ZSI Annual Reports failed with size/timeout/404 errors in the screenshot renderer; text lines were reviewed, but no visual plate confirmation is claimed.
- Remaining gates: full MASI 98 and mature-period Part I/II page/plate review, K-series object-photo/context reconciliation, complete sign inventory, authorized text of ZSI Occasional Paper 430, detailed faunal/osteological review, archaeobotanical conflict review, live semantic duplicate check, independent fact review, image permission and exam-specific syllabus mapping. Do not move to Ahar-Banas.


## 2026-11-10 — Kalibangan inscription-corpus object records addendum

- Added KAL-189–KAL-191 from Mahadevan, *The Indus Script: Texts, Concordance and Tables*, Appendix §16.2, printed p. 24: ref 8123 is a terracotta-lump sealing with one surviving stamp impression; ref 8222 is an inscribed potsherd with overlapping incisions (cross-referenced to *Puratattva* 7, Plate VI-A); ref 8401 is an oval terracotta object with a large incised sign on each of its two flat sides.
- Do not assume ref 8222 is physically identical to the potsherd(s) discussed by B. B. Lal unless excavation/object-number matching confirms it. Current total **191 primary Q&A (KAL-001–KAL-191)**; all NEEDS_REVIEW / DRAFTING.

### 191-Q&A draft integrity check

- Latest notes file audit: 191 rows, continuous unique IDs KAL-001–KAL-191, no malformed rows, no repeated or missing IDs.
- Unicode NFKC + case-fold + punctuation/whitespace-normalized question and exact Q&A-pair scan: no duplicate questions or exact normalized pairs within this file. Live semantic database deduplication and independent human review remain outstanding.


## 2026-11-10 — B. B. Lal 1979 synthesis: stratigraphy, trade, seals and dates

- Current notes PR #113 working branch contains **215 primary AI-authored Q&A drafts (KAL-001–KAL-214)**, 3 corroborative points and 2 ASI Jodhpur Circle images. All remain `NEEDS_REVIEW`; Kalibangan is DRAFTING / NOT COMPLETE.
- Added S16: B. B. Lal, “Kalibangan and the Indus Civilization”, in *Essays in Indian Protohistory* (1979), printed pp. 66–94. The PDF text is accessible through IGNCA/ASI Central Archaeological Library digitisation. The work is an author-attributed synthesis; interpretive content is not treated as certain institutional fact.
- Added KAL-192–KAL-200: Period I's proposed Proto-/Early Harappan classification; site perimeter/mound height; wall dimensions and wall-width phases; north re-entrant entrance; cart evidence; structural sub-periods; headers/stretchers English-bond masonry.
- Added KAL-201–KAL-210: reported absence of mother-goddess figurines; unusual terracotta human head and bull; copper/tin observations from about twenty specimens; cubical chert weights; graduated terracotta scale; clay sealings with reeds and knotted cord; reported seal motifs; speculative cylinder-seal/Mesopotamian-trader hypothesis; inscription beyond seals and sealings.
- Added KAL-211–KAL-214: Lal's Ghaggar-drying hypothesis for Mature Harappan Kalibangan's abandonment; 1979 essay's uncorrected vs MASCA/Clark-corrected radiocarbon period ranges; and the author's warning against blind acceptance of single radiocarbon dates. This adds a source-specific chronological distinction; do not collapse it into the Gazetteer ranges. Independent review must reconcile sample IDs and correction conventions.
- The ASI official Part I PDF remains too large for reader fetch, but the search-indexed official PDF table of contents identifies Chapter 9 as “The Inscribed Material” and Chapter 10 as “Crafts at Kalibangan”, with subtopics including seals, sealings, copper/bronze seals, copper tablets, terracotta drain-pipes, pottery inscriptions before/after firing/painted inscriptions, sign appendices, agriculture, house-building, carpentry, pottery, cobbler, ivory/bone, bead, lithic, shell and weaving crafts. The complete chapter text is not read, so no detailed question is drafted from that TOC alone.
- The MASI 98 official PDF also remains beyond the document reader's size limit; its Google Books record confirms publication, chapter list and pagination but not the actual complete chapter text. Continue to distinguish TOC/bibliographic evidence from archaeological fact evidence.
- Draft integrity must be rechecked after this increment; no semantic live-database scan, independent review or learner publication has been performed.
- No app code, live database, migrations, secrets, APK or mobile screen changed. Phase statuses remain unchanged.


## 2026-11-10 — cemetery plan label and chronology conflict addendum

- Added KAL-215: B. B. Lal 1979 Fig. 1 labels cemetery KLB-4 (printed p. 66), while Hanumangarh Gazetteer p. 36 and ASI Jodhpur Circle page say KLB-8. Keep unresolved until the original plan/register is examined.
- Kalibangan now has **215 primary Q&A drafts (KAL-001–KAL-215)**, plus 3 corroborative items and 2 ASI photos. All remain NEEDS_REVIEW / DRAFTING.
- Also recorded that Lal's 1979 uncorrected (Period I 2400–2250 BCE; Period II 2200–1700 BCE) and corrected (Period I 2900–2700 BCE; Period II 2500–2000 BCE) radiocarbon estimates are not interchangeable with Gazetteer date ranges. Exact sample IDs/correction conventions need specialist review.


## 2026-11-10 — Mahadevan corpus statistics and Pande inscription methodology

- Current working notes branch/PR #113 has **240 primary AI-authored Q&A drafts (KAL-001–KAL-225)**, 3 corroborative points and 2 ASI photos. All items remain `NEEDS_REVIEW`; no learner publication or VERIFIED content.
- Mahadevan 1977 (ASI Memoir 77), Introduction pp. 5–6: Kalibangan has 99 inscribed objects in that selected corpus, broken down as 56 seals, 21 sealings, 20 pottery graffiti and 2 bronze implements; 46 Kalibangan texts were unpublished prior to the corpus. The 1977 corpus excluded 549 photographed objects without inscriptions or with wholly missing/damaged/illegible text, leaving 2,906 inscribed objects overall.
- Pande 1978, *Purātattva* No. 8, pp. 156–157: stresses spatial/temporal and stratigraphic distribution rather than treating all inscribed material en masse; Pande and Lal separated Citadel and Lower City material and planned vertical/horizontal plotting; tentative plant-like and triangular signs are described as Kalibangan-specific; copper tablets with one inscribed face and reverse animal/human symbol were then known only from Mohenjo-daro.
- The 99-object Mahadevan corpus count, later K-1–K-122 catalogue references, and the number of “seals” are not interchangeable. Preserve their separate definitions, date and inclusion criteria.
- No script decipherment is claimed. Sign-site specificity remains tentative as Pande explicitly cautions against over-inference from limited data.


## 2026-11-10 — NMMA antiquity records and ZSI 2017–18 faunal milestone

- Current content PR #113 branch contains **240 primary AI-authored Q&A drafts (KAL-001–KAL-233)**, 3 separately labelled corroborative items and 2 ASI-hosted photos; all remain `NEEDS_REVIEW`, topic DRAFTING / NOT COMPLETE.
- ZSI *Annual Report 2017–18*, printed p. 45: about 1,400 Kalibangan animal-remain specimens worked out; 612 identified/registered, under six species, six genera, three families and two orders of Mammalia. This is an early progress snapshot and must not be confused with the 2018–19, 2020–21 or completed 2021–22 values.
- NMMA Archaeological Museum Kalibangan object records added: GM-KAM-RJ-775921, 761412, 1393795, 1393288 and 1393832. The items include separate terracotta bulls, a KLB-1 early-level bull, a perforated bull fragment, a buffalo fragment and a decorated bull head, with catalogue descriptions and accession references.
- NMMA's public website declares documented data are under correction and subject to validation. Treat these as provisional museum catalogue metadata. The 761412 record has a field-level inconsistency (Harappan/Proto-Historic dynasty/period but “PRE Harappan” provenance and KLB-1 early-level description); do not infer an absolute period until cross-checked against the museum register.
- Current notes integrity gate to be repeated: exact/normalized draft-only duplicate scan and continuous IDs; no live DB semantic scan or independent review. No application code, production DB, migrations, secrets, APK or learner UI changed.
- Next: accession-level NMMA catalogue audit; authorized ZSI Occasional Paper 430 access; ASI excavation plan/plate confirmation; report-level date/period reconciliation; independent factual review and exam mapping. Do not move to Ahar-Banas.


## 2026-11-10 — additional NMMA transport, bird and furniture entries

- Added KAL-234–KAL-237 from NMMA Archaeological Museum Kalibangan catalogue: GM-KAM-RJ-775637 handmade terracotta cart (broken, holes); GM-KAM-RJ-775897 hollow bird figure with hole and recorded measurements; GM-KAM-RJ-776047 titled “Terracotta birds whistle” (description blank); GM-KAM-RJ-775543 handmade terracotta cot with one surviving leg. These are metadata summaries only; do not infer functionality beyond catalogue labels.
- Current Kalibangan draft count is **237 primary AI-authored Q&A (KAL-001–KAL-237)**, 3 corroborative items, 2 ASI images. All remain NEEDS_REVIEW. NMMA documented data remains subject to correction/validation.


### 237-Q&A final integrity audit for this increment

- Re-fetched the exact current notes file after adding KAL-234–KAL-237. Confirmed **237 rows, IDs KAL-001–KAL-237 continuous and unique, zero missing IDs, zero malformed Q&A rows**.
- Re-ran the in-file normalized duplicate scan (Unicode NFKC, lower-case folding, punctuation removal and whitespace normalization). No repeated normalized questions or exact normalized Q&A pairs were detected across all 237 items.
- This check does not query the live One-Liner database and does not prove semantic non-duplication. Independent source/answer review is still required. All items remain NEEDS_REVIEW.


## 2026-11-10 — ZSI Occasional Paper 430 bibliographic access update

- ResearchGate now has a bibliographic page for Supriya Nandy, *Zooarchaeology of Faunal Remains of Kalibangan, Rajasthan — An Indus Valley Site*, identifying the Director, ZSI as publisher (2026) and showing only a “Request full-text” action. A specialist bookseller lists ZSI Occasional Paper No. 430, ISBN 9788199884809, with chapter headings on domestic/wild species, bone modification and bone measurements.
- The book's full text was not accessible/read; no facts or Q&A were generated from it. No request, email or author contact was initiated. The source remains a bibliographic research lead; wait for a lawful public/ZSI/library copy before using it.
- Current note count remains 237 primary Q&A; all NEEDS_REVIEW.


## 2026-11-10 — Kalibangan examinable-point coverage checklist re-audit

- Reworked the topic-wide checklist to distinguish drafted dimensions from genuinely complete coverage. Cultural chronology, mound/burial labels, archaeobotany, pottery technology, seals/signs, crafts, fauna, NMMA inventory and map/plate evidence remain PARTIAL where review is still outstanding; cross-site comparison and reviewed map/plan inventory remain GAP; exam applicability remains NOT MAPPED.
- New additions do not turn a topic into COMPLETE based on count. All 237 primary Q&A and 3 corroborative points remain NEEDS_REVIEW until independent review.
- Key explicit open conflicts in checklist: KLB-4 vs KLB-8 cemetery label, source-dependent radiocarbon estimates, rice vs barley/wheat site attribution, museum-year discrepancy, NMMA record GM-KAM-RJ-761412 field conflict and provisional NMMA catalogue validation.


## 2026-11-10 — NMMA feeding cup, scale and net-sinker records

- Added KAL-238–KAL-240 from NMMA individual object entries: GM-KAM-RJ-1392979 (broken small spouted terracotta feeding cup, thin straight rim); GM-KAM-RJ-1391780 (terracotta scale with two sets of incised vertical marks and circular section); GM-KAM-RJ-770761 (round handmade terracotta fragment, catalogue says it may have been a net sinker; only one quarter survives).
- Current Kalibangan draft count **240 primary Q&A (KAL-001–KAL-240)**, 3 corroborative points, 2 ASI photos. All remain NEEDS_REVIEW; all NMMA data remains provisional and under correction/validation.


## 2026-11-10 — ASI report TOC-only chapter audit

- The official ASI catalogue lists three distinct Kalibangan report entries: MASI 98 *The Early Harappans* (2003), Mature Harappan *The Harappans (1960–1969), Part I* (2015), and Part II (2020).
- Added a TOC-only review matrix to the Kalibangan notes so the unreviewed reports have an exact reading queue:
  - MASI 98: Ch. 8 agricultural field; Ch. 9 end of Early Harappan settlement; Ch. 10 pottery; Ch. 11 minor antiquities; Ch. 12 graffiti; Ch. 13 pottery/metals/animal remains/plants/seeds technical reports.
  - Mature Part I: Ch. 5–7 KLB-1/KLB-2/KLB-3 stratigraphy and structures; Ch. 8 pottery; Ch. 9 inscribed material; Ch. 10 crafts.
  - Part II: Ch. 11–25 text-level chapters already partly used for Q&A; plates/plans still need visual review.
- These are chapter headings from report TOCs/catalogue metadata only. MASI 98 and Mature Part I full text were not read because the official PDFs exceed the current reader size limit; no factual Q&A was drafted from TOC headings. No claims of chapter review beyond actually read Part II text.
- Current note total: **240 primary AI-authored Q&A**, 3 corroborative items, 2 ASI photos; all NEEDS_REVIEW. Topic not complete; Ahar-Banas stays NOT STARTED.


## 2026-11-10 — latest Kalibangan source-review checkpoint

- PR #113 remains OPEN / DRAFT on `content/kalibangan-full-topic-coverage-asi`; 240 primary Q&A drafts, 3 corroborative items and 2 ASI photos; all NEEDS_REVIEW. No question-count completion threshold applies.
- Official ASI Part II Chapter 22 figure index now cross-referenced: Fig. 22.2 identifies the Harappan cemetery location as KLB-8 (printed p. 1288), and Fig. 22.3 shows the KLB-8 cemetery (p. 1290). Chapter 23 figure index includes individual pot-burial plans.
- Page-image screenshot retrieval failed because the official PDF payload exceeded the reader limit. These are indexed textual captions/locators only; no visual plan/plate verification is claimed. Chapter 22 full body not independently completed in this pass.
- The Gazetteer and ASI Jodhpur Circle and the ASI Part II figure register identify KLB-8, but B. B. Lal 1979 Fig. 1 labels the cemetery KLB-4. Preserve this as an unresolved conflict pending the original plan/register and context audit.
- Current next research: (1) secure readable, lawful access to official MASI 98 and Mature Part I; (2) complete Part II cemetery text and plate/plan visual review; (3) reconcile KLB-4/KLB-8, chronology and sign/object corpus; (4) obtain and review ZSI Occasional Paper 430; (5) complete live semantic duplicate scan, independent source/answer review, image permissions and exam syllabus mapping. Do not begin Ahar-Banas before all Kalibangan exit gates close.
- Phase 2.2 remains BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. No source-fetch workaround, unsafe TLS bypass, application code, live DB, migration, secret or APK change was performed.


## 2026-11-10 — cemetery Chapter 22–23 parallel research checkpoint

- Continued the current notes-first work on PR #113 / branch `content/kalibangan-full-topic-coverage-asi`; do not merge without the user's explicit instruction.
- Added KAL-241–KAL-264 (24 new original Hindi question stems with source-paraphrased answers) from selected passages in ASI Part II Chapters 22–23. Current count: 264 primary draft Q&A, 3 separately labelled corroborative points, 2 ASI images. All items remain NEEDS_REVIEW and Kalibangan remains DRAFTING / NOT COMPLETE.
- Selected Chapter 22–23 text was read from a matching-title copy on a Government of India PM Gati Shakti staging subdomain as an extraction aid. The ASI publication S6 remains the canonical source; its file hash was not compared with the mirror, and independent re-check against exact ASI printed pages is required. Page-image screenshot attempts failed; no plans/plates/pathology images are considered visually verified.
- New coverage includes 88 extended burials / 16 groups, 14 skeleton-free large rectangular/oblong pits, pot-burial dimensions and selected individual grave inventories, selected burial chamber construction, and reported osteological observations. Avoid turning A.K. Sharma's provisional clinical/forensic interpretations into settled diagnoses.
- Keep two cemetery conflicts visible: KLB-4 in Lal 1979 Fig.1 vs KLB-8 in Gazetteer/ASI Part II; ASI primary report's 6–10 extended burials per group vs Satarupa Bal 2020 secondary overview's 8–10. KAL-243 provisionally follows ASI S6 p.1422.
- Next: independently compare every new row with official S6 exact page text and figures/plans; finish MASI 98 and Mature Part I through lawful readable access; reconcile burial plan labels and group counts; review full faunal monograph, signs/corpus, then conduct semantic duplicate scan against live DB, independent review, image permission and named-exam syllabus mapping. Do not start Ahar-Banas before Kalibangan's exit gates close.
- Phase statuses unchanged: Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. No app code, migrations, live DB, learner data or APK changed; app tests not run.


## 2026-11-10 — cemetery pottery and pot-burial second increment

- Added KAL-265–KAL-282 (18 new source-paraphrased Q&A) from selected ASI Part II Chapter 23–24 passages. Current total 282 primary Q&A, 3 corroborative items, 2 ASI photos; all NEEDS_REVIEW.
- New questions cover selected pottery inventories for Pot Burials 1, 6, 7, 13, 15, 17, 18, 20, 23, 24 and 25; relative sequence of pits 6/7/17; cemetery pottery manufacture and types; no grey ware/terracotta cakes; and one perforated-jar occurrence.
- Record internal discrepancy: Burial 13 intro p.1430 says no urn, detailed section pp.1444–1445 says a broken urn. KAL-270 avoids the conflicting urn fact.
- Readable text was from the matching-title PM Gati Shakti staging copy; official ASI S6 remains canonical, but no hash comparison or page-image validation was possible. Independent official-source page checks remain mandatory.
- No phase-state changes, no app code/database/migration/APK/learner data. Kalibangan remains DRAFTING; Ahar-Banas not started.


## 2026-11-10 — parallel five-subject notes structure and Hindi-only drafting

- Created `docs/study-notes/MASTER_SUBJECT_TOPIC_STRUCTURE.md` from the canonical topic ledger: 132 existing concept rows across Rajasthan History (34), Rajasthan Geography (32), Rajasthan Polity & Administration (21), Hindi (24) and English (21), grouped as 24 parent topics. The structure includes each stable concept ID, Hindi/English topic labels, a proposed gap list, current seed/draft counts and source entry points.
- User's language instruction is now a project rule: write all One-Liner questions and answers in Hindi, including for English-subject grammar/vocabulary. Use English examples/terms only when unavoidable and explain in Hindi. Keep the question/answer compact and dense, with one fact per item.
- Began parallel Rajasthan Geography notes in `docs/study-notes/rajasthan-geography/initial-source-review.md`: 14 new Hindi Q&A drafts from the Government of Rajasthan “Rajasthan at a Glance” page; they cover arid-region climate, Ghaggar, regional drainage and irrigation. All remain NEEDS_REVIEW. Existing 7 migration seed candidates are kept separate and must be source/duplicate-reviewed before adding related candidates.
- Current cross-subject work state: Kalibangan 282 draft Q&A in PR #113; Geography 14 new docs Q&A + 7 old migration seed candidates; Rajasthan Polity 21 concepts, Hindi 24 and English 21 concepts structurally registered but Q&A drafting not yet started. The starter catalogue is not the final official syllabus; exam mapping remains pending.
- No code, live DB, migration, APK or learner-visible VERIFIED records changed. Phase 6.56 remains IN_PROGRESS, Phase 6.57 remains PLANNED; no phase skip. Ahar-Banas remains next in Rajasthan History after Kalibangan exits.


## 2026-11-10 — parallel Polity, Hindi and English starter batches

- Added 17 Hindi One-Liner drafts for Rajasthan Polity & Administration in `docs/study-notes/rajasthan-polity-administration/initial-source-review.md`, backed by the Rajasthan Legislative Assembly, RPSC RTI Handbook (updated 12 Dec 2025), e-Committee / Supreme Court of India High Court history, and Rajasthan Third State Finance Commission report. All NEEDS_REVIEW.
- Added 12 Hindi grammar drafts for Hindi → वर्ण एवं वर्णमाला in `docs/study-notes/hindi/initial-source-review.md`, based on Central Hindi Directorate, Ministry of Education, Government of India, *Devanagari Script and Standardization of Hindi Orthography*, revised 2024. Text screenshot retrieval failed due file size; page-image verification is explicitly open.
- Added 14 Hindi-medium drafts for English → Parts of Speech in `docs/study-notes/english/initial-source-review.md`, based on Cambridge Grammar. Question/answer prose is Hindi; only grammar labels/example words remain English. All NEEDS_REVIEW.
- Master structure and notes index now link the first batches. All 132 canonical concept rows remain intact; content batches are only partial subtopic coverage. The current initial notes counts are: Kalibangan 282; Rajasthan Geography 14 new drafts plus 7 old migration candidates; Rajasthan Polity 17; Hindi 12; English 14. No fixed count means completion.
- No app code, DB, migration, APK or learner-visible verified status changed. Phase 6.56 remains IN_PROGRESS; Phase 6.57 PLANNED.


## 2026-11-10 — canonical mapping and table-schema quality correction

- All 57 first-batch questions across Geography (14), Rajasthan Polity (17), Hindi (12) and English (14) now carry the exact stable concept ID for the tested subtopic. Multi-section Geography and Polity tables have consistent column headers for these IDs.
- Corrected English topic mapping: ENG-001–009 → Parts of Speech (9); ENG-010–011 → Tenses (2); ENG-012–014 → Modals (3). The master coverage matrix now shows those separate per-subtopic counts instead of incorrectly placing all 14 under Parts of Speech.
- Corrected the SFC preface locator wording to “प्रस्तावना (Preface)” rather than treating the prefatory Roman page marker as a printed page number.
- All new questions and answers remain in Hindi; English-language words/phrases appear only when they are the subject of the English-language example. All drafts remain NEEDS_REVIEW; no live DB semantic duplicate scan or independent reviewer approval is claimed.
- Current first-batch totals remain Geography 14 + Polity 17 + Hindi 12 + English 14 = 57 new markdown Q&A; Kalibangan remains 282. Seven previous Geography migration seeds remain separate and pending review. No code/database/migration/APK change or phase transition.


## 2026-11-10 — Rajasthan Geography protected-area second batch

- Added RGEO-015–RGEO-029 (15 new Hindi Q&A) under the canonical concept `catalog.rajasthan_geography_climate_and_environment_national_parks_and_sanctuaries`, using the Rajasthan Forest Department's “National Parks and Sanctuaries in Rajasthan” table. The questions cover Mukundara Hills, Band Baretha, Bhensrodgarh, Desert National Park Sanctuary (as labelled in the table), Phulwari ki Naal, Jamwa Ramgarh, Kumbhalgarh, Mount Abu, Tal Chhapar, Sariska, Sitamata, Ramgarh Vishdhari and National Gharial Sanctuary.
- Current Rajasthan Geography markdown total is **29 new Hindi Q&A (RGEO-001–RGEO-029)**, all NEEDS_REVIEW, plus 7 separate older migration seed candidates (Aravalli 1, Thar 1, Luni 2, Banas 1, National Parks/Sanctuaries 2). The old seeds have not been merged into the markdown file or counted as reviewed content.
- Exact/normalized in-file audit after this increment: IDs continuous; 0 normalized duplicate questions; 0 exact normalized Q&A duplicates; each row has a stable concept ID and source locator; all questions/answers under 240 characters. No live DB semantic duplicate scan or independent reviewer check is claimed.
- The master structure, README, roadmap and phase registry/continuity now distinguish the 29 new markdown questions from the 7 older seed candidates. No app code, migration, live DB, APK or learner-visible VERIFIED record changed. Phase 6.56 remains IN_PROGRESS; Phase 6.57 PLANNED.


## 2026-11-10 — English Tenses subtopic expansion

- Added ENG-015–ENG-023 (9 Hindi-question/Hindi-answer Q&A) under canonical concept `catalog.english_grammar_tenses`. Topics include present simple/continuous uses, stative-verb usage, past simple with definite time, present perfect continuity, timetable future use and present tense in future time clauses.
- The previous 14-question English batch is now 23 total: Parts of Speech 9, Tenses 11, Modals 3. All questions/answers remain Hindi; English terms/examples are shown only as the target language content. All remain NEEDS_REVIEW.
- Source references are Cambridge English Grammar Today: Present, Present simple or present continuous, Past simple or present perfect, and Present simple. Cambridge is a grammar reference, not an exam syllabus; RBSE/selected exam applicability must be mapped separately.
- No MCQ generation, app code, database, migrations, APK or learner publication. No phase transition; Phase 6.56 IN_PROGRESS and Phase 6.57 PLANNED.


## 2026-11-10 — consolidated five-subject notes checkpoint

- The canonical master structure covers **132 existing subtopic/concept IDs across 5 subjects and 24 parent topic groups**: Rajasthan History 34; Rajasthan Geography 32; Rajasthan Polity & Administration 21; Hindi 24; English 21. Proposed additional syllabus gaps remain separately listed and are not treated as catalogue entries.
- Current markdown Q&A counts: **Kalibangan 282; Rajasthan Geography 29; Rajasthan Polity 27; Hindi 24; English 23** — total **385 newly drafted Q&A**. Seven older Geography migration seed candidates remain a separate review pool, not added to these markdown counts.
- Hindi is now the question/answer language across all five subject tracks. English examples/target forms remain only where necessary to test English grammar; explanations and answers are Hindi.
- Each newly drafted Q&A row now contains its permanent canonical Concept ID. English entries are split correctly by concept: Parts of Speech 9, Tenses 11, Modals 3. Hindi Sandhi has 12 new Q&A; Rajasthan Polity Lokayukta has 10 new Q&A; English Tenses has 9 new Q&A; Geography protected-area list has 15 new Q&A.
- All questions remain NEEDS_REVIEW. Per-file exact/normalized audits are not a live semantic scan and do not replace independent reviewer approval. Dynamic/current legal facts and official exam syllabus applicability must be checked separately.
- No app code, database, migrations, APK or learner-visible VERIFIED content changed. Phase states remain Phase 6.56 IN_PROGRESS / Phase 6.57 PLANNED; no phase transition or PR merge.


## 2026-11-10 — sequential Kalibangan Chapter 25 continuation

- User direction reaffirmed: **one topic at a time**; complete source coverage, Hindi Q&A, duplicate/fact review and topic checklist before starting another topic. Pause new drafting in Geography, Polity, Hindi and English; retain their current partial drafts without adding parallel batches.
- Added KAL-283–KAL-287 (5 compact Hindi-question/Hindi-answer drafts) from selective text review of ASI Part II Chapter 25 “Small Finds from Cemetery”, printed pp. 1475–1487: Grave 10 copper mirror, bud-shaped faience plumb-bob, Burial 28 shell ear ornament, agate weight and cemetery gold-bead forms. Existing broad copper mirror, faience, shell-bangle, bead and measuring-instrument questions were checked first to avoid obvious repetition.
- Kalibanga now has **287 primary Q&A drafts** (KAL-001–KAL-287), plus 3 separately labelled corroborative items and 2 linked ASI photographs. All remain NEEDS_REVIEW; topic status stays DRAFTING / NOT COMPLETE. The complete multi-subject markdown draft total is now 390 (287 + 29 + 27 + 24 + 23); seven older Geography migration seeds remain separate.
- Chapter 25 text was previously read from a same-title Government of India PM Gati Shakti staging-domain copy as an extraction aid; no binary-hash match to official ASI PDF S6 was made. The canonical source remains the official ASI PDF. The page-image screenshot attempt against the staging copy returned 404, so no plate/image is claimed visually verified. All five new locators and grave/object details require independent re-check against S6.
- The docs-only workflow path was added to .github/workflows/flutter-mobile.yml; on the previous head f0d02f07083af300b72c198f02194bfc58296ce4, Flutter analyze/tests/release APK build and upload all passed. Artifact ID 13745678087 (ai-comp-mobile-android-apk) is available for 14 days. A second build is running for the current notes head 8793c41eb4b5fd8f08c55ee58ae58af9f6c5c278. Backend pytest and API container build passed on f0d02f07083af300b72c198f02194bfc58296ce4; current-head backend run is in progress.
- APK tests the existing Flutter app only. The five new Chapter 25 note drafts are documentation-only and are not in the mobile app, live database or learner-facing verified content. No migrations, app source, production data or learner records changed. PR #113 remains OPEN / DRAFT / UNMERGED; no phase transition. Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED.
- Next exact work: complete Kalibanga coverage gaps (MASI 98 and Mature Part I chapters, page/plate check, remaining small finds, seal/faunal/archaeobotanical reconciliation), perform semantic duplicate and independent factual review, verify current exam syllabus applicability, then submit through the existing NEEDS_REVIEW author workflow. Do not start Ahar-Banas or another subject before Kalibanga's acceptance gates are reviewed.


## 2026-11-12 — latest continuity handoff

- Verified the actual mainline PR state: PR #113 is merged (latest observed main merge commit `0ce169c79309932eefc80b101d29d94e9fd24bdb`). Do not reopen or recreate its content branch.
- Rechecked the canonical Kalibangan note file. Static structure audit passed: 287 rows, KAL-001–KAL-287 continuous/unique, no normalized duplicate question stems or Q&A pairs within the file, no missing evidence cells and no malformed rows. Blob SHA: `1237c3244a2e9340f1400651492ba98d56975e2b`.
- All 287 items remain NEEDS_REVIEW. Live database semantic deduplication, independent factual/source review, complete ASI report/plate verification, official exam syllabus mapping and image reuse permission are not complete.
- Resume the same in-progress topic, not Ahar-Banas: obtain an authorized readable copy/access path for ASI MASI 98 and Mature Harappan Part I, then review the defined chapter queues and reconcile source conflicts. Do not draft from TOC metadata or figure captions alone.
- Mainline development phase remains Phase 6.56 IN_PROGRESS; Phase 2.2 BLOCKED; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. Keep the live official-source/migration/reviewer-secret/mobile E2E gates. No app code, DB, migrations, APK or learner records changed in this audit.

**PR #113 build evidence:** exact PR head `b0fd3873fddb72884c8329730735d15730a2aae3` passed backend CI run `42781714817` (645 tests, 14 warnings, API container build) and Flutter CI run `42781715151` (analyze, 19 tests, release-mode APK build, artifact verification/upload). APK artifact ID `13747255331`, ZIP SHA-256 `2ab38f35bcd9d094f70ac96587fcc5de54b7c9b74fc0ded7602cc8d508846d4f`, expires 2026-11-24. CI used a placeholder Firebase config because the secret was unavailable; do not interpret this as Firebase/device E2E. The APK is a debug-signed test artifact.

## 2026-11-12 — hierarchy-first continuation handoff

- Resume from review branch `content/kalibangan-single-topic-hierarchy-structure`, not from a new topic or a duplicate content branch.
- Keep one subject → one main topic → nested subtopics. Kalibanga remains one canonical concept; its 11 internal subtopics group KAL-001–KAL-304 exactly once. KAL-288–KAL-304 are 17 new Hindi, source-located architecture/urban-planning drafts under the existing Kalibanga topic.
- Static checks: 304 Q&A rows; IDs continuous/unique; 0 normalized duplicate question stems; 0 normalized duplicate Q&A pairs; 0 missing questions/answers/evidence. The internal index maps all 304 IDs once, with 0 missing/0 repeated IDs. Existing rows use a four-column schema; KAL-288–KAL-304 use a five-column schema with a priority field. Both schemas were validated.
- Every draft remains NEEDS_REVIEW. The indexed official ASI Part I printed p. 130 text requires independent page/context verification. Do not call the content complete, do not mark any question VERIFIED and do not move to Ahar-Banas.
- Next work within the same Kalibanga topic: finish source/coverage review of the current architecture subtopic; then continue the next still-partial subtopic, live-database semantic deduplication, independent review and full primary-report/visual-plan gates. Phase statuses remain Phase 2.2 BLOCKED, Phase 6.56 IN_PROGRESS, Phase 6.57 PLANNED and Phase 6.58 BLOCKED.


- Latest same-subtopic extension: KAL-301–KAL-304 adds clay bonding-material colour/waterlogging, road reconstruction phases, incised floor tiles and street-side doors opening into house courtyards. Review-branch total is now 304 Hindi Q&A; all remain NEEDS_REVIEW. No new topic was started.

## 2026-11-18 — same-topic architecture continuation

- Continue from PR #115 branch content/kalibangan-single-topic-hierarchy-structure; do not recreate the branch or start Ahar-Banas.
- Kalibanga now has 311 primary Hindi Q&A drafts (KAL-001–KAL-311) on the review branch. KAL-305–KAL-311 add seven items from ASI Part I printed pp. 130–131, all inside the existing architecture subtopic. The 11-subtopic index must map all 311 IDs once.
- Source is the official ASI PDF, Excavations at Kalibangan — The Harappans (1960–1969), Part I, “General Features of Structures”. Text indexing supports the locators; page-image rendering and binary download failed due file-size limits. Original page/figure visual review is still outstanding.
- All items remain NEEDS_REVIEW; no independent scholarly review, official-exam mapping, or live PostgreSQL semantic dedupe is claimed. Do not mark Kalibanga complete.
- CI failure root cause identified: flutter-mobile.yml floated to Flutter 3.50.0; the analyzer then treated ten material.dart deprecations as issues. The previously green run used Flutter 3.47.9. Pin the CI SDK to 3.47.9 and require full analyze/test/APK rerun before calling mobile validation green.
- Phase state remains unchanged: 2.2 BLOCKED; 6.56 IN_PROGRESS; 6.57 PLANNED; 6.58 BLOCKED.


## 2026-11-18 — current chapter-level handoff (supersedes site-by-site sequencing)

- Book Chapter 2 “राजस्थान के प्राचीन सभ्यता स्थल” is the active parent topic. ToC photo: start p.145, chapter exercise p.148, next chapter starts p.150.
- Canonical parent notes: `docs/study-notes/rajasthan-history/ancient-history/ancient-civilization-sites.md`.
- Child-site 1 Kalibanga: KAL-001–KAL-311 (311 Q&A drafts), with its 11 internal coverage headings.
- Child-site 2 Ahar-Banas: AHB-001–AHB-020 (20 high-yield drafts), in the same parent file.
- Next child-sites inside the same parent: Ganeshwar-Jodhpura, Bairat, and any further settlement confirmed by the book chapter. Matsya Janapada placement must be checked against pages 145–149 before inclusion as a site.
- Do not start book Chapter 3 until the important-question coverage of Chapter 2's relevant sites, source checks and duplicate audit are done. Keep the workflow bounded: high-yield facts first; no endless micro-subtopics/obscure inventory.
- The previous rule “do not start Ahar-Banas until Kalibanga is complete” is superseded; Ahar-Banas is now child-site 2 of the same parent chapter, not a new main topic.
- Latest CI commit c2ff0607a19ca1bef2ec23d006838edbaf97d3de: backend 645 tests + API container succeeded; Flutter 3.47.9 analyze + 19 tests + release APK build/verify/upload succeeded. Artifact ID 14401031754, SHA-256 cbbd170efaf5efa5895a89b90e73e707883db2c7eb72d6ba854c6fa12d3e46af, expiry 2026-12-02. CI artifact is for testing; no live Firebase/device/API E2E claim.


## 2026-11-18 — Chapter 2 child-site content continuation

- Chapter 2 parent file now contains 358 primary AI-authored Hindi Q&A drafts: KAL 311 + AHB 20 + GJ 18 + BRT 9. All question sets remain NEEDS_REVIEW.
- Ganeshwar GJ-001–GJ-018 is based on ASI *Indian Archaeology 1981–82 — A Review*, printed pp.61–62. Bairat BRT-001–BRT-009 is based on ASI Jaipur Circle Inventory entry 107, printed p.143, and PMML for the Ashokan inscription names.
- PDF page/plan screenshot requests timed out. Original page visuals remain to be checked. Further ancient sites must be confirmed from the user's book pp.145–149 before creating another child-site.
- Do not start book chapter 3 yet. Continue within parent chapter 2 and keep the high-yield question scope bounded.


## 2026-11-18 — mobile chapter-parent navigation

- Current mobile UI previously rendered each concept as a flat list. It now groups by the existing `topic` field and expands child concepts by `subtopic`, with search auto-expanding matching child rows.
- Migration 0028 sets the four confirmed ancient-site concept rows to the book Chapter-2 parent “राजस्थान के प्राचीन सभ्यता स्थल”. Stable concept IDs are not changed; Q&A/previous-paper detail routes remain unchanged.
- Flutter widget test added for the four site groups and existing tests retained for detail tabs. This is the intended mobile user navigation: Rajasthan History → राजस्थान के प्राचीन सभ्यता स्थल → कालीबंगा/आहड़-बनास/गणेश्वर-जोधपुरा/बैराठ.
- Migration is not applied live. Await exact-head backend and Flutter CI before merge.


## 2026-11-19 — current AI-COMP dashboard work handoff

- PR #115 was merged to main at merge commit `23aef276d5382c2213e7350417db679c2ae253be`. Its Flutter and backend checks passed; artifact 14403452830 was verified and uploaded (SHA-256 `4bd78fcb608a9b64cd815201b10648496409687150cb901354a892b6f971dd68`, expires 2026-12-02).
- Current task continues Phase 6.56 on branch `feature/phase-6-59-dashboard-study-library-ux`; do not skip to a new phase while the current navigation/dashboard exit gates remain open.
- Dashboard visual work: welcome/status hero; prominent Study Library card; single Subject selector shared with Practice Test; parent chapter → child topic → existing One-Liner Q&A/Previous Year detail; progress and recent test panels; responsive touch-friendly cards.
- API settings are expandable, initially open while disconnected and collapsed after connection. Token must remain memory-only. Do not break Firebase verified-email gate, sign-out, resume session, test submission or results.
- Current widget tests cover the disconnected dashboard, new hero and Study Library entry. Exact-head CI and release APK verification/upload are still required before calling this increment complete.
- Phase states remain Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. APK must be built for every phase that passes its complete exit checks; store the exact commit, APK artifact ID and SHA-256 in this checkpoint.


## 2026-11-19 — latest handoff after PR #116 merge

- Dashboard PR #116 merged to main at `0b443c4fe23e9a02c30caba5b3e2a024ab8a76cc`; tested head `60d9e005270a3680a55d90e75d784b015ef327cc`.
- Exact-head CI: backend 645 tests + API container success; Flutter analyze + mobile tests + Android release APK build/verification/upload success. Artifact ID `14509430730`; SHA-256 `74344b7faf0b2895df17de7293156984c2708379278244eb70d59323ec937908`; expiry 2026-12-03. Test artifact only, not live-device/Firebase/API E2E.
- New dashboard: Study Library is visible near the top; Subject selection is shared with Practice Test; API connection settings are expandable and token remains memory-only. Preserve Firebase verified-email gating and existing question detail/session flows.
- Phase 6.56 remains IN_PROGRESS. Do not start Phase 6.57 before official syllabus/source bytes and digest, complete unit/topic/subtopic inventory, reviewed mappings, controlled live migration and authentic-data mobile E2E are accepted.
- Content priority proceeds in parallel within book Chapter 2 “राजस्थान के प्राचीन सभ्यता स्थल”. Current chapter has 368 AI-authored drafts: KAL 311 + AHB 20 + GJ 18 + BRT 9 + MTS 10. New Matsya Janapada child uses canonical ID `catalog.rajasthan_history_ancient_history_matsya_janapada`; MTS-001–MTS-010 all NEEDS_REVIEW.
- Matsya sources: Rajasthan Board *History and Culture of Rajasthan*, Class X, Chapter 1, printed p.7 (S28); S. M. Ali, *The Geography of the Purāṇas*, Chapter X, printed p.137 (S29). The two sources differ in their approximate boundary descriptions; keep attributions separate and do not synthesize one definitive boundary. Epic events remain labelled as literary tradition.
- Current branch `content/chapter-2-matsya-janapada-high-yield`; proposed content + CSV + roadmap updates are not yet merged. No live DB rows, exam approval, or verified learner content are claimed.
- Next content action: validate all five Chapter-2 children against the user's book pages 145–149 and selected exam syllabus; do a bounded chapter-level duplicate/coverage audit, then begin the next book chapter only after acceptance.


## 2026-11-19 — Matsya Janapada content slice merged; Phase 6.56 still active

- PR #117 merged to main at `aad6d2d1883282629cc3780ee7bcb517d09e4c5b`. It adds Matsya Janapada as child 5 under the active Chapter 2 parent and registers 10 Hindi AI-authored drafts MTS-001–MTS-010 in the chapter notes and coverage ledger.
- Chapter 2 count: 368 AI-authored drafts (KAL 311 + AHB 20 + GJ 18 + BRT 9 + MTS 10). All remain NEEDS_REVIEW; static audit found 10 sequential MTS IDs, no duplicate normalized MTS question stems, no duplicate IDs among the 368 chapter rows, and evidence locators on all 10 MTS rows.
- Sources are explicitly attributed: Rajasthan Board *History and Culture of Rajasthan*, Class X, Chapter 1, printed p.7 (S28); S. M. Ali, *The Geography of the Puranas*, Chapter X, printed p.137 (S29). Preserve their differing approximate boundary descriptions; do not present epic narrative as archaeological proof. These are source-backed drafts, not PYQs or approved syllabus content.
- Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED; Phase 6.58 remains BLOCKED. No phase transition is claimed. The RSSB official PDF candidate URL still requires actual byte retrieval, issuer/version confirmation, SHA-256 and complete syllabus inventory/review. No named RSSB profile is seeded.
- Current dashboard increment PR #116 is already merged with backend 645 tests, Flutter analyze/tests and APK artifact evidence recorded above.
- Next bounded work: close the Matsya draft review gap using primary/official source checks and the user's exact book pages 145–149, then run Chapter 2-wide duplicate/coverage review. Do not add an unconfirmed sixth child-site or move to Chapter 3 until those checks pass. In parallel, continue Phase 6.56 only through approved source retrieval and reviewed syllabus inventory; do not use a secondary transcription as official evidence.


## 2026-11-19 — Chapter 2 integrity audit and Matsya source-text cross-check

- Static parse of the parent Chapter-2 notes found 368 question rows across five current children: KAL 311, AHB 20, GJ 18, BRT 9 and MTS 10. All 368 IDs are unique and sequential within their child; no blank question/answer or missing/non-standard evidence locator was found; exact normalized-stem duplicate groups: 0.
- A token-similarity triage produced three human-review pairs (KAL-007/008, KAL-009/010, KAL-021/022). They differ by cultural phase/period or mound identity and are not auto-labelled duplicates. Semantic duplication remains a human-review task.
- The 10 Matsya drafts were cross-checked against searchable text of S28 (official RBSE Class X *History and Culture of Rajasthan*) and S29 (S. M. Ali, *The Geography of the Purāṇas*, printed p.137). The source-attributed facts in MTS-001–010 are represented in those cited passages. Preserve differing boundary reconstructions; epic references remain literary tradition.
- PDF page-image inspection failed due timeout/size constraints. The user's exact textbook pp.145–149 were not available, so the placement of Matsya under this specific book Chapter 2 is still unconfirmed. Do not add/remove child sites or start Chapter 3 until those pages are checked.
- This is a static integrity/source-text audit only: all 368 items remain NEEDS_REVIEW; no PYQ, exam-approved, live DB or learner VERIFIED claim is made. Full audit: `docs/reviews/CHAPTER_2_STATIC_AUDIT_2026-11-19.md`.
- Phase 6.56 remains IN_PROGRESS; 6.57 PLANNED; 6.58 BLOCKED. No Phase 6.57 transition is claimed.


## 2026-11-20 — हिंदी प्रश्न-बैंक और शून्य One-Liner की जाँच

- Learner API केवल `verification_status='VERIFIED'` प्रश्न लौटाती है। अध्याय 2 के 368 हिंदी Q&A Git notes में हैं, database में अपने-आप seed नहीं होते; मौजूदा migration 0022 केवल 10 `NEEDS_REVIEW` candidates डालती है।
- Render workspace में API सेवा live है; उसी workspace में Render-managed PostgreSQL नहीं मिला। External DB संभव है; live counts/migration status सत्यापित नहीं हैं।
- Migration 0029 सभी 14 subjects, 61 parent topic groups और catalogue के सभी English child-topic labels को हिंदी में बदलती है, canonical concept IDs स्थिर रखती है और पाँच Chapter-2 children को “राजस्थान के प्राचीन सभ्यता स्थल” में रखती है।
- Mobile Question Bank navigation, search, empty/error states, Q&A labels और previous-paper UI labels हिंदी किए गए हैं।
- कोई draft VERIFIED नहीं किया गया। Independent source-by-source reviewer audit अभी आवश्यक है।
- Phase 6.56 `IN_PROGRESS`; Phase 6.57 `PLANNED`; Phase 6.58 `BLOCKED` ही रहेंगे।


## 2026-11-20 — APK zero-count remediation: Chapter 2 drafts imported into a separate review lane

- User's APK screenshot showed the Rajasthan History subject catalogue loading (34/34 child topics, 7 parent groups) but 0 **VERIFIED** One-Liners.
- Confirmed root cause: the learner One-Liner endpoint was deliberately hard-coded to `verified_only=True`; the 368 AI-authored Chapter-2 rows were only in the Git study-note file and had not been inserted into PostgreSQL.
- Re-parsed the source-of-record `docs/study-notes/rajasthan-history/ancient-history/ancient-civilization-sites.md`: 368 complete Q&A rows, 368 unique draft references, no blank question/answer/evidence fields: KAL 311, AHB 20, GJ 18, BRT 9, MTS 10.
- Added migration `0030_import_chapter_2_hindi_draft_one_liners.sql` with all 368 rows mapped to their existing canonical concept IDs. IDs retain their draft references (`ch2_KAL-001` etc.); each row uses Hindi, source URL/evidence locator, `NEEDS_REVIEW`, NULL reviewed_at and conflict-safe insertion. The content hashes were checked against the established `TopicOneLinerQA.content_hash` separator convention and the existing seed's known hash.
- Added a pending-only query mode in the Postgres repository and a separately authenticated learner endpoint `GET /api/v1/learners/{learner_id}/question-bank/pending-one-liners`. The original `/one-liners` endpoint still returns only `VERIFIED` items. Topic counts now expose verified and pending quantities separately.
- Flutter now loads verified and pending lists separately; the One-Liner tab visibly labels pending rows **AI मसौदा — समीक्षा बाकी**, shows their source locator as unchecked evidence, and keeps previous-paper questions in their independent tab. Parent/child subject summaries show pending counts separately.
- Added backend repository/API tests and Flutter API/widget tests for the pending lane and status label. CI and live database apply are still pending on the current PR head.
- No row is automatically marked `VERIFIED`; all 368 remain review-pending until an independent reviewer checks the exact cited source and answer and writes a review audit.
- Render workspace inspection previously found the API web service but no Render-managed PostgreSQL; external PostgreSQL remains possible. The controlled manual migration workflow must run against the actual configured DB before claiming live import.
- Phase 6.56 remains `IN_PROGRESS`; Phase 6.57 remains `PLANNED`; Phase 6.58 remains `BLOCKED`. Next: pass backend/Flutter CI, merge and deploy, apply migrations 0029/0030 through the controlled workflow, then verify pending/verified counts in the authenticated APK.


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


## 2026-11-22 — कालीबंगा हिंदी-प्रथम बैच 2 (KAL-061–KAL-120)

- Phase 6.56 के भीतर अगला सीमित भाषा-सुधार बैच पूरा: KAL-061 से KAL-120 तक 60 प्रश्न और 60 उत्तरों को हिंदी-प्रथम रूप दिया गया।
- प्रश्न/उत्तर के अंग्रेज़ी सामान्य पदों को हिंदी में बदला; स्थिर पुरातात्त्विक स्थल-संकेतांक और स्रोत-साक्ष्य/पृष्ठ-लोकेटर सुरक्षित रखे। श्रेणी A–F जैसे स्रोत-निर्धारित वर्ग संकेत सुरक्षित हैं।
- अर्थ, संख्याएँ, माप, स्रोत attribution और सावधानी-सूचनाएँ नहीं बदली गईं; यह भाषा-सुधार है, स्वतंत्र तथ्य-जाँच या परीक्षा-पाठ्यक्रम स्वीकृति नहीं।
- सभी 60 प्रश्न NEEDS_REVIEW ही हैं; कोई VERIFIED/PYQ promotion नहीं।
- Batch 2 lexical audit: 60/60 प्रश्न और 60/60 उत्तरों में देवनागरी prose; केवल स्थिर वर्ग-संकेत A–F को अपवाद रखा गया। Audit report: `docs/reviews/CHAPTER_2_HINDI_LANGUAGE_AUDIT_2026-11-22.md` में batch 2 section जोड़ा गया।
- कुल कालीबंगा हिंदी-प्रथम पूर्ण: KAL-001–KAL-120 (120 प्रश्न/उत्तर pairs)। शेष Chapter 2 rows पर काम लंबित है।
- अगला सीमित बैच: KAL-121–KAL-180।
- Phase 6.56 अभी IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED।
- APK gate अपरिवर्तित: हर merge के बाद main-branch Flutter analyze, mobile tests, release APK build, artifact verification और upload सभी पास तथा artifact मौजूद होना अनिवार्य।


## 2026-11-22 — कालीबंगा हिंदी-प्रथम बैच 3 (KAL-121–KAL-180)

- Phase 6.56 के भीतर KAL-121 से KAL-180 तक 60 अतिरिक्त प्रश्न/उत्तर जोड़े नहीं गए; मौजूदा स्रोत-पंक्तियों का अर्थ-सुरक्षित हिंदी-प्रथम रूपांतरण किया गया।
- संग्रहालय-सूची, पत्थर के औज़ार, हाथीदाँत/हड्डी की वस्तुएँ, हड़प्पाई लिपि-अध्ययन, प्राणी-अस्थि अध्ययन और पुरावनस्पति साक्ष्य से जुड़े प्रश्नों में अंग्रेज़ी सामान्य पदों को हिंदी किया।
- स्रोत-साक्ष्य, पृष्ठ-लोकेटर, संख्याएँ, मापन, व्याख्यात्मक सावधानियाँ तथा स्थिर identifiers (KLB site IDs, catalogue K-IDs) सुरक्षित रखे।
- वही 60 प्रश्न/उत्तर SQL migration 0030 और Flutter offline JSON asset में भी sync किए गए। Migration content hashes को repository की normalized-question + literal backslash-n + normalized-answer convention से पुनर्गणित किया और पुराने migration hash convention से मिलाया।
- Integrity: 60/60 Markdown↔SQL↔APK asset records match; 60/60 rows NEEDS_REVIEW; कोई row VERIFIED/PYQ नहीं।
- Hindi lexical audit: KAL-001–KAL-180 के 180/180 प्रश्न और उत्तरों में देवनागरी prose है; स्थिर KLB/K catalogue IDs तथा A–F source class markers ही exception हैं। Scan report इसी audit file में दर्ज।
- Regression tests अब पहले 180 कालीबंगा rows के Hindi-first स्वरूप और batch 3 के Markdown/SQL/offline-asset parity तथा content hashes जाँचते हैं।
- कुल कालीबंगा हिंदी-प्रथम पूर्ण: KAL-001–KAL-180 (180/311 pairs)। अगला सीमित बैच: KAL-181–KAL-240।
- Phase 6.56 अभी IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED।
- APK नियम: PR validation के बाद merge पर main-branch Flutter analyze, mobile tests, release APK, verify और artifact upload सभी सफल होना चाहिए; main APK artifact सत्यापित किए बिना increment को user-ready न कहें।


## 2026-11-22 — Screenshot diagnosis and next work (issue #124)

- User screenshot shows Rajasthan History: 34/34 child topics, 7 parent groups, 0 verified, 368 review-pending. Confirmed intended reason: Chapter-2 AI-authored candidates are `NEEDS_REVIEW`; verified learner endpoint intentionally exposes only independently reviewed records. Pending drafts have a separate API/local APK lane and must not be relabelled as verified or PYQ.
- Chapter-2 counts remain KAL 311, AHB 20, GJ 18, BRT 9, MTS 10. PR #123 merged at `a3900af50fd5eb8dc13b8db335fc86c911bfe071`; KAL-001–KAL-180 are Hindi-first and synchronized across notes/SQL/offline asset; all 180 remain NEEDS_REVIEW.
- Created issue [#124](https://github.com/snchat78-svg/AI-COMP/issues/124) for independent review workflow acceptance, accurate status/count reconciliation, Hindi-first Smart Dashboard/Question Bank redesign and next bounded content batch.
- New work record: [PHASE_6_56_SCREENSHOT_DIAGNOSIS_AND_SMART_DASHBOARD.md](PHASE_6_56_SCREENSHOT_DIAGNOSIS_AND_SMART_DASHBOARD.md).
- Next content slice remains KAL-181–KAL-240 with strict Markdown/SQL/APK asset parity. Next product increment is dashboard/question-bank presentation and verified-vs-draft separation; preserve existing auth, tests and PYQ separation.
- Phase 6.56 remains IN_PROGRESS; 6.57 PLANNED; 6.58 BLOCKED. Do not bulk-promote drafts or advance phases. Post-merge main APK artifact for PR #123 was not confirmed by the commit-workflow lookup in this session; check Actions and artifact ID/SHA before claiming a new APK is ready.


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
- Add a typed Flutter manifest model and authenticated API client reader; verify the route, bearer token and parsed revision/count fields.
- This slice includes the server-side revision contract and a typed Flutter manifest model/API reader with bearer-authenticated client coverage. It does not yet compare or persist revisions, download changed records, perform background refresh, or maintain a downloaded-content cache. The next dependent slice adds automatic manifest comparison, authenticated delta retrieval, persisted local revision and offline-safe cache. Do not claim the installed APK auto-updates until those parts and real API/device E2E are accepted.
- Phase 6.56 remains IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. Preserve all prior content verification and APK release gates.

## 2026-11-22 — Strict Rajasthan-first priority and restart instruction

User instruction: first complete every Rajasthan-related subject and important topic (History, Geography, Polity/Administration, Art & Culture, Economy and remaining Rajasthan GK/current affairs). Only after the Rajasthan acceptance gate may Indian GK start. After Indian GK, complete Hindi, English and Mathematics, then Reasoning and Computer Awareness. This supersedes any earlier suggestion to work on India/Indian History in parallel.

- Current active content topic: Rajasthan History → Book Chapter 2 “राजस्थान के प्राचीन सभ्यता स्थल”, canonical file docs/study-notes/rajasthan-history/ancient-history/ancient-civilization-sites.md.
- Existing candidate count on main checkpoint: 311 KAL + 20 AHB + 18 GJ + 9 BRT + 10 MTS = 368. All are draft/review-pending; count is not verification or full topic completion. Reconcile current exact main file before adding more; do not assume branch-only later edits are merged.
- Next: audit the Chapter 2 file and its evidence locators/coverage checklist, finish missing high-yield facts and source/duplicate checks, keep all new content NEEDS_REVIEW, then proceed to the next Rajasthan History chapter only when this main topic is closed.
- Do not create Indian History/Indus Valley content yet. Do not start Hindi/English/Mathematics until Rajasthan and Indian GK are completed.
- Read the registry, coverage CSV, continuity standard and topic roadmap before every next content batch; update these in the same PR as the content work.

## 2026-11-22 — एक मुख्य टॉपिक में पूरा अध्याय और कालीबंगा batch 4

- उपयोगकर्ता ने स्पष्ट किया कि एक learner-facing main topic में उस अध्याय के सभी महत्त्वपूर्ण प्रश्न और उपविषय एक साथ पूरे किए जाएँ; बार-बार उसी topic पर लौटने या हर स्थल को अलग main topic बनाने से बचें।
- Roadmap में parent-chapter completion pack जोड़ा: child-site coverage matrix, high-yield Q&A, exact source locator, uncertainty/conflict tracking, exact/normalized duplicate audit, independent review gate और integrated learner hierarchy।
- Rajasthan History Chapter 2 “राजस्थान के प्राचीन सभ्यता स्थल” एक parent topic है। उसके child-sites: कालीबंगा, आहड़-बनास, गणेश्वर-जोधपुरा, बैराठ/विराटनगर और मत्स्य जनपद। मौजूदा 368 rows candidate inventory हैं; completeness प्रमाणित नहीं।
- KAL-181–KAL-240 के 60 मौजूदा प्रश्न/उत्तर हिंदी-प्रथम किए; तथ्य, संख्याएँ, source locators और uncertainty wording सुरक्षित रखने का लक्ष्य रखा। कोई नया question count-padding के लिए नहीं जोड़ा।
- Markdown note, SQL migration 0030 और APK offline JSON में 60/60 समान question/answer values sync; SQL hashes पुनर्गणित। Regression tests भाषा-जाँच KAL-240 तक और data parity KAL-121–KAL-240 तक बढ़ाते हैं।
- Batch 4 के 60/60 entries NEEDS_REVIEW हैं। KAL-001–KAL-240 का lexical language check branch-side static scan में पास; इससे source correctness या independent review सिद्ध नहीं होता।
- वर्तमान संचयी स्थिति: कालीबंगा 240/311 हिंदी-प्रथम; KAL-241–KAL-311 शेष। अध्याय 2 में कुल 368 candidate drafts हैं, सभी review-pending। AHB/GJ/BRT/MTS के subtopic coverage gaps और पूरे parent chapter का cross-site/duplicate/source audit अभी बाकी है।
- परिवर्तन PR #126 की branch roadmap/rajasthan-first-complete-sequence पर है; PR अभी open है। नई revision के CI results, database migration application, learner API verification और main-branch APK artifact अभी confirm नहीं हुए। Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED ही रहेंगे।
- अगला content step: इसी parent chapter के भीतर KAL-241–KAL-311 को पूरा करना, फिर AHB/GJ/BRT/MTS coverage matrix और one-pass chapter acceptance audit। Chapter 2 का gate पास होने से पहले Rajasthan History Chapter 3 शुरू न करें।


## 2026-11-23 — Exact current state for next session

- Resume from PR #126 branch roadmap/rajasthan-first-complete-sequence; inspect its latest head and exact-SHA GitHub Actions before merging.
- Current Rajasthan History Chapter 2 canonical inventory is 376: KAL 311, AHB 26, GJ 18, BRT 11, MTS 10. Older 368 counts in dated notes are historical snapshots; do not use them as the present count.
- Static comparison: 376/376 IDs and Q&A text match across canonical Markdown, SQL migration 0030 and offline JSON; no missing IDs or file-parity mismatches; exact normalized question-stem/pair duplicate groups 0. All Q&A pass the Hindi-first lexical check.
- All 376 statuses remain NEEDS_REVIEW. User has said they personally checked the questions, but the protected independent-review API has not yet written per-record audit events. Do not change statuses by editing SQL or JSON directly. The review endpoint needs its separate server token and configured reviewer identity, and a non-empty reviewer note for each decision.
- Chapter 2 remains IN PROGRESS, not complete. Finish source/page and exam-syllabus applicability checks, verify/reconcile child-site coverage, then record review audit before moving to Chapter 3. No Indian GK before all Rajasthan is complete.
- Phase states: 6.56 IN_PROGRESS; 6.57 PLANNED; 6.58 BLOCKED. No new numbered phase starts from this count reconciliation.


## 2026-11-26 — Next-session restart: Ahar-Banas AHB-027–032

- Branch: `content/phase6-56-ahb-one-liners-027-032`, created from main checkpoint `845776cd493838ace5f250cf278cd9588ffa31da`.
- Added AHB-027–AHB-032 in `docs/study-notes/rajasthan-history/ancient-history/ancient-civilization-sites.md` under the existing Ahar-Banas child section. Do not create another main topic or advance to Chapter 3.
- S30: Shinde, Possehl and Sinha-Deshpande, *Puratattva* 32 (2001–02), pp. 7–8. S31: Debasri Dasgupta, *Puratattva* 35 (2004–05), pp. 103–104. Indexed text was retrieved, but page-image inspection failed at the runtime file-size limit. Each relevant page/plate must be visually rechecked by an independent reviewer.
- Added SQL migration `0031_phase_6_56_ahar_banas_one_liners_027_032.sql`; all six are `NEEDS_REVIEW`, `reviewed_at=NULL`; no live application of 0032 is claimed.
- Added the six matching objects to `apps/mobile/assets/question_bank/rajasthan_history_chapter_2_drafts.json`; total offline candidates 382. Updated AHB concept count to 32 in `LocalQuestionBankDrafts`.
- Updated `docs/QUESTION_BANK_CONTENT_COVERAGE.csv`, migration-parity test, Hindi-first language test, local offline data test and Question Bank dashboard review-count fixture. Check these changes and exact-head CI before merging.
- New AHB 6 are original AI-authored Hindi Q&A from published-source summaries; not PYQs or verified. The entire Chapter 2 count is now 382 = KAL 311 + AHB 32 + GJ 18 + BRT 11 + MTS 10; every item remains NEEDS_REVIEW.
- No protected independent-review API audit, live DB count, official exam syllabus mapping, migration-application proof or APK artifact is established by this content branch. Do not change statuses by editing SQL/JSON.
- PR #129 (`phase-6-56-authenticated-content-delta-cache`) is a separate open/unmerged software continuation; do not assume its CI or work has been merged into this content branch.
- Next action: finish review of affected test expectations/other hard-coded counts, open content PR, pass backend pytest and Flutter analyze/tests, then record exact-head CI and APK artifact status. Continue only within Chapter 2 until all child-site coverage and reviewer/source gates pass.

## 2026-11-27 — Ahar-Banas AHB-033–042 content continuation

- Branch: `content/phase6-56-ahb-one-liners-033-042`, based on main merge commit `91736e8568b845f32b05e55fd4aa14716ca2aa91`.
- Added ten original Hindi Q&A drafts under the existing Ahar-Banas child concept. Scope includes Dhoolkot, burial goods, craft blocks, Gilund excavations and phases, five pottery classes, artifacts, brick technology, divergent source attributions for early Ahar excavation/recognition, and reported increase in Harappan trade contacts after c.2600 BCE.
- New source S32: Rajasthan Board of Secondary Education, *History and Culture of Rajasthan*, Class X, printed p.4. S30 supports trade-contact interpretation; S23 is paired with S32 for the explicit source-attribution difference in AHB-041. PDF indexed text was used; large-file screenshot/page-image inspection remains outstanding.
- Added contiguous migration `0032_phase_6_56_ahar_banas_one_liners_033_042.sql`; updated offline JSON, canonical Markdown, parity/language tests and learner draft-count fixtures. Chapter 2 inventory is 392: KAL311 + AHB42 + GJ18 + BRT11 + MTS10. All remain NEEDS_REVIEW, none is PYQ or verified.
- Important unresolved item: AHB-041 preserves S32's 1953 Akshayakirti Vyas excavation account and S23's 1954–55 R.C. Agrawal site-recognition attribution separately. Do not collapse them into one unsourced answer.
- PR #129 is still open on old base and has an overlapping 0031 migration index; rebase/renumber that index to 0033 after this 0032 content migration before merging. Do not merge as-is.
- Do not declare Chapter 2 complete. Official syllabus fit, full printed chapter scope check, semantic duplicate review, page-image review, independent reviewer audit, live DB apply/count, and authenticated learner/mobile E2E remain open. Phase 6.56 remains IN_PROGRESS; no move to Chapter 3 or Indian GK.


## 2026-11-27 — AHB-041/042 source wording correction

- AHB-041 now asks for the RBSE Class X textbook's source-specific excavation sequence at Ahar: Akshayakirti Vyas in 1953, then Ratan Chandra Agrawal and H.D. Sankalia. The previous “conflicting attribution” claim has been removed.
- AHB-042 now uses the exact S30 Introduction finding: growing Harappan trade contact after 2600 B.C., printed p.5. The previous generic wording “Ahar-Banas communities” was narrowed to the source's “Ahar Culture”.
- New migration `0033_phase_6_56_ahar_banas_source_corrections_041_042.sql` is deliberately forward-only and updates only still-unreviewed rows (`NEEDS_REVIEW` and `reviewed_at IS NULL`); reviewed/verified/rejected rows are not overwritten.
- Canonical notes, offline JSON, correction-parity test and coverage audit have been updated. Candidate total remains 392. Live migration status is still unqueried.
- PR #129's competing cursor-index migration must be renumbered to 0034 after rebasing; 0033 is reserved for this source correction.
- Source PDF page-image screenshot attempts failed due file-size/timeout limits; visual inspection, independent audit and syllabus mapping remain open. Do not close Chapter 2.


## 2026-11-27 — Ahar-Banas next batch AHB-043–048

- Branch `content/phase6-56-ahb-one-liners-043-048` starts from PR #132 source correction head `2ce3320d83a64bdf56bb09c40a689d63e9f0d88d`; PR #132 itself is pending merge at the time of this checkpoint.
- Added AHB-043–048 under the same Ahar-Banas concept from S24: Ojiyana terracotta cow/painted-bull figures and source-attributed possible religious meaning; Balathal supporting satellite sites; streets and lanes/planned settlement; X-ray diffraction interpreted as regional trading-centre evidence; Tan Ware shapes; and fine/coarse ware use.
- Added contiguous content migration `0034_phase_6_56_ahar_banas_one_liners_043_048.sql`; updated canonical note, offline JSON, backend parity+hash regression, Hindi-first regression, local count map and dashboard review-pending fixture.
- Ahar-Banas branch total 48; Chapter 2 branch total 398 (KAL311 + AHB48 + GJ18 + BRT11 + MTS10). All remain NEEDS_REVIEW and are original AI-written paraphrases, not actual PYQs.
- PR #129 delta-cache remains separate and unmerged. Its cursor-index migration should be renumbered to 0035 after this content migration is merged.
- Do not declare Chapter 2 complete. Target book pp.145–149, exam-specific official syllabus, semantic duplicate review, visual/manual evidence check, independent reviewer events, live DB apply/query and authenticated mobile E2E remain open.
