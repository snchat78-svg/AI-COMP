# Phase 6.56 — Exam-profile and official-syllabus mapping slice

**Canonical phase state:** [Phase Registry](PHASE_REGISTRY.md)  
**Cross-chat handoff:** [Project Continuity Checkpoint](PROJECT_CONTINUITY_CHECKPOINT.md)  
**Full One-Liner requirement:** [Question Bank Coverage Policy](QUESTION_BANK_CONTENT_COVERAGE.md)  
**Status:** Phase 6.56 remains **IN_PROGRESS**. This document describes the first implementation slice on branch `phase-6-56-exam-syllabus-mapping`; do not describe the overall phase as complete.

## Gap being closed

The existing 340 canonical concepts are a generic navigation catalogue. Their presence alone does not prove that a concept belongs in a particular recruitment exam's official syllabus. Showing every catalogue topic for every exam would risk preparing learners against the wrong syllabus. Phase 6.56 now introduces explicit exam-profile and syllabus-source records and permits exam-scoped browsing only for a verified syllabus and independently reviewed concept mappings.

## Official-source status — intentionally conservative

No exam profile or syllabus document is seeded by migration 0023. The following URL remains a **candidate official-source lead**, not yet a verified document:

- `https://rssb.rajasthan.gov.in/storage/advertisement_item/1782966142.pdf`

A current third-party syllabus page [TopKaro — CET Graduation Level 2026](https://topkaro.com/rssb/cet-graduation/syllabus) explicitly points to this exact URL, labels it Advertisement 09/2026 dated 1 July 2026, and presents a 14-unit syllabus transcription. That corroborates where research should continue, but it is secondary evidence only; it is not a substitute for reviewing the official bytes. The direct official PDF URL is inaccessible through the current research runtime, so this work has **not independently confirmed the document contents, notification identity/version, or SHA-256**. Do not copy secondary-transcribed syllabus into verified official inventory or seed a named profile on this evidence alone.

Before adding a real profile, retrieve the exact notification/syllabus through an approved official HTTPS path; confirm the issuing board, advertisement/notification number, title, relevant dates and the complete document contents; compute SHA-256 from the retrieved bytes; and record precise source evidence. If direct official retrieval remains unavailable, leave the profile absent and continue with clearly synthetic test fixtures. Do not weaken certificate validation or treat a secondary transcription as official proof.

## Storage added

Migration `0023_phase6_56_exam_syllabus_mapping.sql` adds:

- `exam_syllabus_documents`: links an existing `exams` record to one current HTTPS syllabus document, notification/version, source metadata, content SHA-256, source status and review evidence. One current document is allowed per exam. A VERIFIED source requires a digest, review timestamp, reviewer identity and source evidence **and** an independently reviewed full-syllabus inventory attestation. The database will not permit `source_status = VERIFIED` while the inventory is unreviewed.
- `exam_concept_applicability`: records each canonical concept as `IN_SCOPE`, `OUT_OF_SCOPE`, `UNMAPPED` or `NEEDS_REVIEW` for a specific syllabus document. IN_SCOPE/OUT_OF_SCOPE are rejected by the database unless independent-review metadata and evidence locator/note are present.
- The syllabus document itself includes `syllabus_inventory_complete` with reviewer/time/note fields. `source_status = VERIFIED` is rejected unless both the official-document evidence and whole-inventory attestation are present. Read APIs also require every canonical concept to have a reviewed applicability decision before returning any exam-specific topics; they do not expose a partially mapped list.
- No exam profile/source/mapping seed is included. A real profile must be added only after the exact official notification/syllabus bytes, identity and SHA-256 have been retrieved and independently confirmed; tests use clearly synthetic profile fixtures.

The mapping must remain faithful to the complete official syllabus. The repository refuses to expose exam-scoped subjects/topics unless the source is VERIFIED, the whole-syllabus inventory attestation is complete, and every current canonical concept has an independently reviewed IN_SCOPE/OUT_OF_SCOPE decision with evidence. If a syllabus includes a unit/subtopic absent from the current concept catalogue, create the missing stable concept and ledger row before the inventory reviewer attests completion. If a generic catalogue concept is not in the syllabus, record the reviewed out-of-scope decision rather than silently showing it.

## API and mobile slice

New API contract:
- `GET /api/v1/learners/{learner_id}/question-bank/exam-profiles` — includes source-review state, current concept counts and readiness state.
- `GET /api/v1/learners/{learner_id}/question-bank/subjects?exam_id=...` — exam-specific subject list only from independently reviewed IN_SCOPE mappings. A pending profile returns an honest empty list.
- `GET /api/v1/learners/{learner_id}/question-bank/topics?exam_id=...&subject=...` — topic list constrained to the chosen exam profile and reviewed mappings. Unknown profiles return 404. Without `exam_id`, the existing generic catalogue route is preserved for compatibility and is not represented as exam-specific coverage.

The mobile client parses the profile status and sends optional `exam_id` filters. The home screen displays a separate Official Exam Syllabus selector and the count of mapped/unmapped concepts; it explicitly disables exam-scoped browsing until the selected profile is ready. Existing generic browsing, adaptive practice, login, session, resume and results flows remain separate.

## Safety/quality gates

- Do not change `REVIEW_PENDING` to VERIFIED because the URL looks official or a secondary site reproduces syllabus text.
- Do not show generic topics under a named exam profile unless each concept has independently reviewed IN_SCOPE evidence.
- Do not claim 340 official syllabus concepts. The 340 number is the size of the current generic catalogue, not an official syllabus count.
- Do not count candidates as verified One-Liners. Each final item must be Q + direct answer, source-backed, duplicate-checked and independently reviewed, under `QUESTION_BANK_CONTENT_COVERAGE.md`.
- Keep credentials out of source control. Live migration application is a separate operational gate and must follow the controlled workflow.
- If the database is not migrated yet, the new profile endpoint can return an API/service-unavailable error. The mobile screen should show that honestly and preserve older flows.

## Required validation for this slice

- Backend pytest and API-container build pass on the exact PR head.
- API tests cover pending profile readiness, empty exam-scoped subjects, 404 for an unknown profile and learner-scope enforcement.
- Repository tests ensure unreviewed mappings never appear as in-scope topics.
- Flutter analyze, mobile/client/widget tests, release APK build, APK verification and artifact upload pass on that exact PR head.
- Review the generated OpenAPI contract and migration against the existing schema.
- Re-check all gates after CI runs on the latest commit; earlier green SHA is not enough.

## Protected author/reviewer workflow — merged implementation; live gates pending

The protected author/reviewer workflow merged in [PR #44](https://github.com/snchat78-svg/AI-COMP/pull/44), merge SHA `44a1da0ef6c5afd79e81e7367ea57fac15dbfc7c`. Tested head `4189742e9981f8f0d288e1260bd79b0a3b4d4918` passed [workflow 39904691212](https://github.com/snchat78-svg/AI-COMP/actions/runs/39904691212): 517 tests passed, 14 warnings and API container build passed. The merged code still requires live migration/secrets setup and independent review of the actual official PDF; it does not independently authenticate source contents.

- `POST /api/v1/admin/exam-syllabi` allows an authenticated server-side author to create a source candidate only as `REVIEW_PENDING`; it cannot self-certify a source as VERIFIED.
- `POST /api/v1/admin/exam-syllabi/{syllabus_id}/source-review` requires a distinct reviewer token and server-configured reviewer ID. VERIFIED is rejected unless SHA-256, source evidence, and a reviewer attestation that the full inventory is complete are supplied.
- `POST /api/v1/admin/exam-syllabi/{syllabus_id}/concept-mappings/review` records evidence-backed concept applicability decisions; IN_SCOPE/OUT_OF_SCOPE require official-unit, source-locator and evidence fields.
- Migration `0024_phase6_56_syllabus_review_workflow.sql` adds an append-only audit table and a database trigger that rejects UPDATE/DELETE of audit events.
- Configuration is server-side only: `AI_COMP_SYLLABUS_ADMIN_TOKEN`, `AI_COMP_SYLLABUS_REVIEW_TOKEN`, `AI_COMP_SYLLABUS_AUTHOR_ID`, and `AI_COMP_SYLLABUS_REVIEWER_ID`. Author and reviewer tokens must differ and must not reuse the Phase 6.55 one-liner credentials. Never put these values in Git, mobile config, or learner requests.

This workflow records a human reviewer attestation; it does not automatically retrieve or cryptographically validate a remote official PDF. Reviewers must independently retrieve the official document over normal certificate-validated HTTPS, confirm its issuing authority/version and complete contents, compute SHA-256 from the actual bytes, and inspect every page/unit before choosing VERIFIED. CI success alone does not satisfy those live evidence gates.

## Remaining work inside Phase 6.56

1. Establish an approved retrieval path for the candidate official PDF; confirm its actual issuing board, notification number, title/version, dates, full contents and SHA-256. A secondary source now points to the same URL, but official bytes remain inaccessible here and no profile is seeded.
2. Add a protected, auditable admin/reviewer workflow for source verification and concept-applicability authoring/review. Author and reviewer secrets must be distinct; never trust a learner token or client-supplied reviewer ID.
3. Extract the entire official unit/subtopic inventory, cite exact page/section locators, reconcile it with the concept catalogue, add concepts for omitted units, and update the coverage ledger before an independent reviewer attests that the inventory is complete.
4. Record a separately reviewed IN_SCOPE/OUT_OF_SCOPE decision for every catalogue concept and ensure every official syllabus unit maps to canonical concepts. Keep missing/ambiguous mappings visible. The read API must not expose partially reviewed subject/topic lists as exam-ready.
5. Once the official document, full inventory and complete mapping are reviewed, make the profile ready and verify the mobile selector filters subjects/topics by profile with tests for distinct scopes and an unmapped state.
6. Then resume topic-by-topic source-backed Q&A creation; complete knowledge-point coverage, not only a target question count, and keep drafts NEEDS_REVIEW until independent review.

Phase 6.56 must remain IN_PROGRESS until official-source retrieval, source evidence, mapping completeness, current-head CI and the remaining acceptance checks have been demonstrated.

## Structured unit/topic/subtopic inventory — merged PR #45

PR [#45](https://github.com/snchat78-svg/AI-COMP/pull/45) continues Phase 6.56 by replacing the bare inventory-complete assertion with concrete reviewable rows.

- Migration 0025 adds UNIT, TOPIC and SUBTOPIC rows with stable IDs, parent hierarchy, page numbers, section locators, supporting evidence, author identity and independent review metadata.
- POST /api/v1/admin/exam-syllabi/{syllabus_id}/units creates drafts only as NEEDS_REVIEW; server code validates the parent hierarchy.
- POST /api/v1/admin/exam-syllabi/{syllabus_id}/units/{unit_id}/review records independent VERIFIED, REJECTED or NEEDS_REVIEW decisions in the append-only audit log. Authors cannot review their own inventory rows.
- Source verification requires at least one inventory row and every row to be VERIFIED. A database trigger independently enforces this invariant.
- Inventory edits are blocked while the source is attested complete; an independent reviewer must reopen source review before changing the inventory. Authors cannot directly downgrade an approved concept mapping.
- PR #45 merged at `9694e01c11528157b8a1107fcf78c4c3a1e01ef9`; tested head `7b746257cbf06bc6c9d2a5f96a907ab637834adf` passed [backend run 39906458179](https://github.com/snchat78-svg/AI-COMP/actions/runs/39906458179): 527 passed, 14 warnings; API container build passed.

### Official syllabus discovery status

Research found a secondary transcription of RSSB CET Graduation Level 2026 that identifies Advertisement 09/2026 dated 1 July 2026 and lists 14 broad units: [TopKaro syllabus transcription](https://topkaro.com/rssb/cet-graduation/syllabus). The candidate official document URL is https://rssb.rajasthan.gov.in/storage/advertisement_item/1782966142.pdf, but direct retrieval failed in the current runtime. Official PDF bytes, complete page contents, document digest, and notification/version have not been independently verified. The secondary page can inform a draft checklist only; it cannot justify a VERIFIED exam profile or complete-inventory attestation.

## Next live acceptance task after PR #46

The protected official-source fetch implementation is already merged in PR #46 and passed its exact-head backend/container CI. Do not reimplement the fetcher or migration. The remaining work is operational and evidence-based:

1. Through the controlled migration workflow, confirm migrations 0024–0026 are applied to the intended live database and configure distinct server-side author/reviewer credentials and reviewer identity. Never commit or expose secrets in the mobile client.
2. From an approved deployed API host with outbound DNS/network access, use the reviewer-only `POST /api/v1/admin/exam-syllabi/{syllabus_id}/fetch-source` endpoint. It must fetch only the source URL already registered in the database; do not weaken TLS, bypass allowlists, or use unreviewed redirects.
3. Inspect the exact persisted PDF bytes, issuing board, advertisement/notification number, version/date, page count and content. A secondary transcription or synthetic CI fixture is not official evidence. No real document digest is currently verified.
4. Inventory every official UNIT/TOPIC/SUBTOPIC with source page/section locators, reconcile missing canonical concepts, and have an independent reviewer approve all IN_SCOPE/OUT_OF_SCOPE mappings. Only after every inventory row and mapping is reviewed may the profile become usable.
5. Verify end-to-end with real deployed data and the mobile app, including authentication, topic filtering, readiness counts and question display.

The latest source-research workflow [39908982194](https://github.com/snchat78-svg/AI-COMP/actions/runs/39908982194) failed with source-host TCP timeouts, legacy-host TLS renegotiation failure and RPSC network failure; it persisted zero paper candidates. PR #49 was squash-merged as `a5b4aafed39dee8831b3b2eef2a17832157d77f9`; final tested head `0bb1e06c50c9525c1520fe501b0afc1407a04f71` passed 544 tests/14 warnings plus API container build in [run 40061803084](https://github.com/snchat78-svg/AI-COMP/actions/runs/40061803084). This verifies code/tests only—not live official source access. Phase 6.56 remains IN_PROGRESS and Phase 6.57 must not start until the acceptance gates above pass.

## PR #46 — official PDF fetch and immutable evidence

PR [#46](https://github.com/snchat78-svg/AI-COMP/pull/46) adds reviewer-only `POST /api/v1/admin/exam-syllabi/{syllabus_id}/fetch-source`. The URL is loaded from PostgreSQL; caller-supplied URLs are ignored. Requests are restricted to an explicit RSSB/RSMSSB HTTPS host allowlist, redirects are validated at every hop, ambient proxies are disabled, default TLS certificate validation is retained, and nonstandard ports/userinfo/HTTP URLs are rejected. The fetch has a 12-second overall deadline and 10 MiB cap, checks content length/encoding/PDF header/EOF, parses at most 500 pages, rejects encrypted or unreadable PDFs, and computes SHA-256 from the actual bytes.

Migration `0026_phase6_56_source_fetch_evidence.sql` stores the exact PDF bytes, digest, source/final URLs, page count, title, fetcher, timestamp and immutable audit evidence. Failed fetch attempts are audited, and the latest failed attempt blocks verification. Source review must match the SHA-256 from the latest successful server fetch for the same registered URL; a reviewer-entered digest alone is insufficient.

PR #46 was squash-merged as `ea59fc9e4712b3b646c707e2abf6f30f3690975c`. Tested head `c0e293d58c70a3621f5bf6d51741384838c24549` passed [workflow 39907825229](https://github.com/snchat78-svg/AI-COMP/actions/runs/39907825229): 538 passed, 14 warnings; API container build passed. The actual RSSB PDF remains inaccessible to this research runtime, so no official PDF or digest is claimed verified. Next, apply migrations only through the controlled workflow and use the protected endpoint from an approved API host with outbound DNS/network; independently inspect the exact stored PDF, complete the inventory/mappings and prove live mobile E2E. Phase 6.56 remains IN_PROGRESS; do not start Phase 6.57.


## PR #46 merge evidence

- Merge SHA: `ea59fc9e4712b3b646c707e2abf6f30f3690975c`.
- Tested PR head: `c0e293d58c70a3621f5bf6d51741384838c24549`.
- [CI workflow 39907825229](https://github.com/snchat78-svg/AI-COMP/actions/runs/39907825229): 538 passed, 14 warnings; API container build succeeded.
- Migration 0026 stores immutable source-fetch attempts and exact successful PDF bytes. Latest failed fetch blocks source verification; VERIFIED requires a digest matching the latest successful fetch for the exact stored source URL.
- This is code/CI completion only. The real RSSB source, its notification/version/content/digest, the full syllabus inventory and concept mapping remain unverified until live data review is performed.

## Manual live candidate fetch workflow — branch `phase-6-56-manual-source-fetch`

The workflow `.github/workflows/register-and-fetch-official-syllabus.yml` is the next operational bridge for the existing PR #46 source-fetch endpoint. It is manually triggered, defaults to `DO_NOT_RUN`, and only runs when the operator explicitly chooses `REGISTER_AND_FETCH`. It does not introduce a new downloader or a second verification implementation.

### Required setup before running

1. Confirm database migrations `0024`, `0025`, and `0026` have been applied to the intended production database. Use the existing `.github/workflows/database-migrations.yml` with repository secret `AI_COMP_DATABASE_URL`; do not modify or print the secret. Run `confirm_apply=APPLY` only after verifying the target database, because that workflow applies all unapplied repository migrations.
2. Configure a GitHub Actions environment named `official-source-review`; put `AI_COMP_SYLLABUS_ADMIN_TOKEN` and `AI_COMP_SYLLABUS_REVIEW_TOKEN` in that environment as secrets. They must exactly match the corresponding server-side Render environment values, be distinct from one another, and must not reuse the Phase 6.55 content-author/reviewer tokens. Consider enabling required reviewers for this environment.
3. Verify on the server that `AI_COMP_SYLLABUS_AUTHOR_ID` and `AI_COMP_SYLLABUS_REVIEWER_ID` are present, non-empty and different. The API is fail-closed if these values or the distinct author/reviewer tokens are missing.

### What the workflow does and does not do

- It accepts only the four approved RSSB/RSMSSB HTTPS hosts; normal certificate validation remains enabled. It does not permit userinfo, a nonstandard port, or a URL fragment. API redirects are rejected so author/reviewer credentials cannot be forwarded to another host.
- It first submits the candidate through the protected author endpoint, which can create only `REVIEW_PENDING`, then calls `POST /api/v1/admin/exam-syllabi/{syllabus_id}/fetch-source` without passing a URL. The deployed API fetches only the source URL stored in the database, validates the PDF, computes SHA-256 from actual bytes and stores immutable evidence.
- The candidate title and notification number default to explicitly **UNVERIFIED/UNCONFIRMED** values. A successful fetch proves only that bytes were retrieved safely; it does not prove the source is the correct notification or that the syllabus is complete. The workflow never sets source status to `VERIFIED`.
- If the actual PDF cannot be fetched, the job reports a safe error code without printing tokens or raw API response bodies. The candidate stays pending if it was already created; check the audit table before retrying so duplicate syllabus IDs are not reused.
- After a successful fetch, an independent human reviewer must inspect the exact persisted PDF, identify the issuing board/notification/version/date, check every page and full unit/topic/subtopic inventory, and record evidence. Then the reviewer can complete inventory/mapping reviews through the existing gated APIs. Do not infer official content from the secondary TopKaro transcription.

Because this workflow is manually dispatched, the CI test suite validates its safeguards but does not run it against the live database during PR CI. Phase 6.56 remains IN_PROGRESS until controlled migration state, successful official PDF retrieval, human review, complete concept mapping and real mobile E2E are evidenced. Phase 6.57 stays PLANNED.
## PR #54 merge and CI evidence — manual fetch workflow

- PR [#54](https://github.com/snchat78-svg/AI-COMP/pull/54) was squash-merged at `1b3d1e7534f6bf0802caf396020bca0762c1769f`.
- Tested PR head: `23ae408ccb321b258bd88482b7ad65850984f666`.
- [Backend CI run 40073840875](https://github.com/snchat78-svg/AI-COMP/actions/runs/40073840875): **548 passed, 14 warnings; API container build passed**.
- The workflow `.github/workflows/register-and-fetch-official-syllabus.yml` is available in current main. It is manually dispatched, defaults to DO_NOT_RUN, requires REGISTER_AND_FETCH, registers the candidate only as REVIEW_PENDING, then calls the existing server-side source fetch endpoint without supplying a URL. API redirects are rejected to prevent forwarding review credentials.
- This workflow was not executed against live data during CI. Before a live run, apply any pending migrations 0024–0026 to the verified target through `.github/workflows/database-migrations.yml`, then configure the GitHub `official-source-review` environment secrets to exactly match server-side author/reviewer tokens and ensure server-side actor IDs are distinct.
- The candidate RSSB PDF has not been retrieved/independently inspected, and no real official document digest or complete mapping is claimed verified. Phase 6.56 stays IN_PROGRESS; Phase 6.57 remains PLANNED.

## Latest operational evidence — 25 October 2026

Current main `dd676617d5c4ac0feb123a309b6ba4984aec531d` was rechecked after the earlier runbook update:

- Official-source research [40167821936](https://github.com/snchat78-svg/AI-COMP/actions/runs/40167821936) failed closed across the three registered hosts; no paper candidates persisted.
- Paper processing [40173279948](https://github.com/snchat78-svg/AI-COMP/actions/runs/40173279948) completed with zero question candidates.
- Answer-key verification [40176782796](https://github.com/snchat78-svg/AI-COMP/actions/runs/40176782796) completed with zero selected candidates and zero matched pairs.
- These green downstream jobs are empty-queue no-ops; they do not establish a verified paper, answer key, mapping coverage or E2E success.

The next action is still within Phase 6.56: confirm controlled application of migrations 0024–0026, configure the protected `official-source-review` environment and matching-but-distinct author/reviewer credentials, then run the existing manually gated fetch workflow. Review exact stored PDF bytes and metadata before source approval. Do not start Phase 6.57, duplicate the fetch implementation, or relax TLS.

## Live migration evidence — 25 October 2026

The operator-provided successful migration run #3 checked out historical commit `22d0fcb3a5972b241550b5d64de37207dcc651a2`. That commit contained only SQL migrations `0001`–`0018`; the output `Applied migration versions: 0018` does not cover the later `0019`–`0026` migrations now present on `main). Therefore migrations `0024`–`0026` remain **NOT CONFIRMED applied to the live database**.

Before a new controlled run, verify that `AI_COMP_DATABASE_URL` is the intended `ai-comp-db` database and review migration `0021`'s safety effect: pre-existing `VERIFIED` one-liners without independent reviewer identity are demoted to `NEEDS_REVIEW`. The affected live-row count has not been queried. After the target/impact review, apply the pending migrations using the existing database-migrations workflow on current `main`, then record the exact run ID, checkout SHA and applied versions. Only after that should the existing official-source fetch workflow be considered. Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED.

## Controlled migration verification — 25 October 2026

The controlled [database migration run #4](https://github.com/snchat78-svg/AI-COMP/actions/runs/40190212101) succeeded on current-main commit `dd676617d5c4ac0feb123a309b6ba4984aec531d`. The supplied job log explicitly lists `0019, 0020, 0021, 0022, 0023, 0024, 0025, 0026` as applied. Migrations `0024`–`0026` are now applied according to the migration runner output; no repeat run is needed.

Migration `0021` demotes legacy one-liners that were marked `VERIFIED` without independent reviewer identity to `NEEDS_REVIEW`. No affected-row count was emitted. Do not infer the live question-bank pool is populated or verified from migration success.

Next step remains Phase 6.56 live acceptance: configure/check the protected `official-source-review` environment secrets and distinct server-side author/reviewer actor IDs, then use the existing manually gated official syllabus fetch workflow. A successful fetch will store unverified evidence only; the exact PDF and complete syllabus still require independent human review. Phase 6.57 stays PLANNED.
