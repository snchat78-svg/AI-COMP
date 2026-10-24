# AI-COMP Project Continuity Checkpoint

**This file is the first-read checkpoint for every new AI-COMP chat/session.** Do not restart from conversation memory alone. Check the repository state in GitHub because it is the shared durable record.

**Last updated:** 2026-10-24 (PR #44–#46 and #49 merged; live official-source retrieval remains blocked)  
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
