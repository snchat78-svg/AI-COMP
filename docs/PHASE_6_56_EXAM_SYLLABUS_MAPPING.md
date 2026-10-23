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

## Protected author/reviewer workflow — implementation in review

The follow-up implementation is being developed on branch `phase-6-56-syllabus-author-review` and must pass exact-head CI before merge:

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

## Structured unit/topic/subtopic inventory — PR #45

PR [#45](https://github.com/snchat78-svg/AI-COMP/pull/45) continues Phase 6.56 by replacing the bare inventory-complete assertion with concrete reviewable rows.

- Migration 0025 adds UNIT, TOPIC and SUBTOPIC rows with stable IDs, parent hierarchy, page numbers, section locators, supporting evidence, author identity and independent review metadata.
- POST /api/v1/admin/exam-syllabi/{syllabus_id}/units creates drafts only as NEEDS_REVIEW; server code validates the parent hierarchy.
- POST /api/v1/admin/exam-syllabi/{syllabus_id}/units/{unit_id}/review records independent VERIFIED, REJECTED or NEEDS_REVIEW decisions in the append-only audit log. Authors cannot review their own inventory rows.
- Source verification requires at least one inventory row and every row to be VERIFIED. A database trigger independently enforces this invariant.
- Inventory edits are blocked while the source is attested complete; an independent reviewer must reopen source review before changing the inventory. Authors cannot directly downgrade an approved concept mapping.
- PR #45 is open and exact-head CI must pass before merge. This proposed implementation is not complete until validation succeeds.

### Official syllabus discovery status

Research found a secondary transcription of RSSB CET Graduation Level 2026 that identifies Advertisement 09/2026 dated 1 July 2026 and lists 14 broad units: [TopKaro syllabus transcription](https://topkaro.com/rssb/cet-graduation/syllabus). The candidate official document URL is https://rssb.rajasthan.gov.in/storage/advertisement_item/1782966142.pdf, but direct retrieval failed in the current runtime. Official PDF bytes, complete page contents, document digest, and notification/version have not been independently verified. The secondary page can inform a draft checklist only; it cannot justify a VERIFIED exam profile or complete-inventory attestation.

## Follow-up slice: individually reviewed syllabus inventory (PR in preparation)

The next Phase 6.56 slice adds migration `0025_phase6_56_syllabus_unit_inventory.sql` and author/reviewer endpoints for each official syllabus UNIT, TOPIC and SUBTOPIC:

- `POST /api/v1/admin/exam-syllabi/{syllabus_id}/units` creates an individual source-located inventory row in `NEEDS_REVIEW`; parent hierarchy is enforced (UNIT → TOPIC → SUBTOPIC).
- `POST /api/v1/admin/exam-syllabi/{syllabus_id}/units/{unit_id}/review` permits an independent server-configured reviewer to mark a pending row VERIFIED or REJECTED.
- A source cannot receive the complete-inventory attestation unless at least one inventory row exists and every row is independently VERIFIED. A database trigger enforces this invariant, and the inventory is locked while marked complete.
- Review records include page number when known, official label, locator, source evidence, author/reviewer and audit entry. These fields are evidence records, not proof that an external source is official; humans must compare every row against the actual official document.
- Regression tests cover payload hierarchy and migration invariants. Exact-head CI remains required before merge.

The candidate RSSB syllabus is still unverified; no exam profile is seeded. Phase 6.57 remains blocked.
