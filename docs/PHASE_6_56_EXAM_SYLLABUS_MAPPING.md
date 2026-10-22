# Phase 6.56 — Exam-profile and official-syllabus mapping slice

**Canonical phase state:** [Phase Registry](PHASE_REGISTRY.md)  
**Cross-chat handoff:** [Project Continuity Checkpoint](PROJECT_CONTINUITY_CHECKPOINT.md)  
**Full One-Liner requirement:** [Question Bank Coverage Policy](QUESTION_BANK_CONTENT_COVERAGE.md)  
**Status:** Phase 6.56 remains **IN_PROGRESS**. This document describes the first implementation slice on branch `phase-6-56-exam-syllabus-mapping`; do not describe the overall phase as complete.

## Gap being closed

The existing 340 canonical concepts are a generic navigation catalogue. Their presence alone does not prove that a concept belongs in a particular recruitment exam's official syllabus. Showing every catalogue topic for every exam would risk preparing learners against the wrong syllabus. Phase 6.56 now introduces explicit exam-profile and syllabus-source records and permits exam-scoped browsing only for a verified syllabus and independently reviewed concept mappings.

## Official-source status — intentionally conservative

The initial profile to research is **Rajasthan CET Graduation Level 2026**, associated with RSSB Advertisement No. 09/2026. The candidate PDF URL on the official RSSB hostname is:

- `https://rssb.rajasthan.gov.in/storage/advertisement_item/1782966142.pdf`

The URL was discovered, but direct retrieval/content and its SHA-256 could not be independently confirmed during this slice. A secondary transcription was not accepted as official evidence. The migration therefore seeds the document with `source_status = REVIEW_PENDING`, no document digest, and an explicit caution in the evidence note. No syllabus-to-concept rows are pre-certified. This is an exam profile to research, **not a claim that the official syllabus or its topic coverage is verified**.

The official board site/legacy domain may be used as navigation context, but only the actual official notification / syllabus document, reviewed with a digest and exact section/page/heading locator, may be used to promote the source to VERIFIED. A source URL being on an official domain is not, by itself, verification of its file contents.

## Storage added

Migration `0023_phase6_56_exam_syllabus_mapping.sql` adds:

- `exam_syllabus_documents`: links an existing `exams` record to one current HTTPS syllabus document, notification/version, source metadata, content SHA-256, source status and review evidence. One current document is allowed per exam. A VERIFIED source requires a digest, review timestamp, reviewer identity and source evidence **and** an independently reviewed full-syllabus inventory attestation. The database will not permit `source_status = VERIFIED` while the inventory is unreviewed.
- `exam_concept_applicability`: records each canonical concept as `IN_SCOPE`, `OUT_OF_SCOPE`, `UNMAPPED` or `NEEDS_REVIEW` for a specific syllabus document. IN_SCOPE/OUT_OF_SCOPE are rejected by the database unless independent-review metadata and evidence locator/note are present.
- The syllabus document itself includes `syllabus_inventory_complete` with reviewer/time/note fields. `source_status = VERIFIED` is rejected unless both the official-document evidence and whole-inventory attestation are present. Read APIs also require every canonical concept to have a reviewed applicability decision before returning any exam-specific topics; they do not expose a partially mapped list.
- An idempotent RSSB CET Graduation Level 2026 profile/source seed, kept in REVIEW_PENDING with zero asserted concept mappings.

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

## Remaining work inside Phase 6.56

1. Retrieve the official PDF over approved HTTPS, confirm document contents and SHA-256, and independently verify the exact notification/syllabus version.
2. Extract the entire official unit/subtopic inventory, cite exact page/section locators, reconcile it with the concept catalogue, add concepts for omitted units, and complete the coverage ledger.
3. Record a separately reviewed IN_SCOPE/OUT_OF_SCOPE decision for every catalogue concept and map every official syllabus unit to canonical concepts. Keep remaining/ambiguous items visible.
4. Once the official document and complete mapping are reviewed, make the profile ready and verify the mobile selector filters subjects/topics by profile with tests for two distinct scopes and an unmapped state.
5. Then resume topic-by-topic source-backed Q&A creation; complete knowledge-point coverage, not only a target question count, and keep drafts NEEDS_REVIEW until independent review.

Phase 6.56 must remain IN_PROGRESS until official-source retrieval, source evidence, mapping completeness, current-head CI and the remaining acceptance checks have been demonstrated.
