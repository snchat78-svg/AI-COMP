# AI-COMP Project Continuity Checkpoint

**This file is the first-read checkpoint for every new AI-COMP chat/session.** Do not restart from conversation memory alone. Check the repository state in GitHub because it is the shared durable record.

**Last updated:** 2026-10-22  
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
- **Phase 6.56:** IN_PROGRESS. PR #42 merged at d138d65d758efbde5c04126688566d499063da40 delivered paged topic search and separate One-Liner/Previous-Year states. PR #43 is open: https://github.com/snchat78-svg/AI-COMP/pull/43. Latest code/test SHA for this slice is `ddb05682058fb2344dd41c473e697ca6cb9f921d`; backend workflow `39787466831` and Flutter/APK workflow `39787466651` were still running at the last check. The latest mapping slice adds migration `0023`, exam-profile API, optional `exam_id` topic/subject filtering, separate mobile selector and review-gated data model. It requires both source verification and an independently reviewed full-syllabus inventory before the source can be VERIFIED; API queries withhold all exam-specific subjects/topics until every catalogue concept has reviewed IN_SCOPE/OUT_OF_SCOPE evidence. Current candidate RSSB CET Graduation Level 2026 official PDF URL has not been directly retrieved/content-hashed/reviewed. Status remains `REVIEW_PENDING`; the 340 concepts are generic catalogue rows, all currently unmapped to this exam. The protected author/reviewer workflow, official inventory extraction, missing-concept reconciliation and independent mapping remain open. Check PR #43's latest exact-head CI before merge.
- **Phase 6.57:** PLANNED — topic coverage, learner mastery and revision.
- **Phase 6.58:** BLOCKED on approved official-source connectivity, live database migration/secrets, real official-paper + matched answer-key records, and live end-to-end proof.

## Full One-Liner coverage requirement

The target is full examinable-point coverage for every applicable subject/topic/subtopic in every supported exam profile—not just meeting a fixed question count. The current catalogue has 340 concept rows across 14 broad subject categories; that is scaffolding, not a complete official syllabus. Final learner-facing One-Liners must be written in question + concise direct answer (Q → A) format, not as bare fact statements. Analyse each topic against its official syllabus and authoritative sources, build a topic-specific checklist of testable knowledge points, draft questions to cover every applicable point, remove duplicates, and track missing points. Five distinct source-backed independently verified Q&As per applicable subtopic is only a minimum floor, not proof of completeness; broad/high-weight topics may require many more. All factual drafts must have source URL and evidence locator and remain NEEDS_REVIEW until an independent reviewer signs them off. No model-generated answer may self-certify as verified. See QUESTION_BANK_CONTENT_COVERAGE.md for the completion checklist and rules.

The CSV ledger currently shows candidate seeds in Git only: 10 pending Q&A across 6 concept IDs; the other 334 catalogue concepts have no candidate in that seed migration. Live database counts have not been queried and are labelled NOT_QUERIED_LIVE_DB.

## Exact next actions at checkpoint creation

1. Resume Phase 6.56 from open [PR #43](https://github.com/snchat78-svg/AI-COMP/pull/43), not by restarting or skipping to Phase 6.57. Check latest PR head and exact-head workflow checks first.
2. Finish/repair backend and Flutter CI on the current code/test SHA; update the checkpoint/registry after any fix. Merge only when relevant exact-head checks pass; phase remains IN_PROGRESS even after merge.
3. Add a protected, auditable syllabus source and concept-mapping author/reviewer workflow with distinct author/reviewer credentials and review-audit records; never accept a client-claimed reviewer identity.
4. Retrieve the candidate RSSB CET Graduation Level 2026 official PDF over approved HTTPS; validate the actual contents, notification/version, and SHA-256. The official-host URL is recorded in `docs/PHASE_6_56_EXAM_SYLLABUS_MAPPING.md`, but is not yet verified.
5. Extract the full official unit/subtopic inventory with exact page/section evidence. Reconcile every unit with canonical concepts, add missing concepts/CSV ledger rows, and independently review IN_SCOPE/OUT_OF_SCOPE mappings for every catalogue concept. Never label the profile ready based on the generic 340-topic catalogue alone.
6. Only after source + inventory + mapping review, enable profile-scoped subject/topic browsing; test distinct exam scopes and unmapped-state behavior. Then proceed with topic-by-topic full examinable-point coverage and Q→A candidate drafting, duplicate/evidence checks and separate review.
7. Continue Phase 6.55 live migration/reviewer-secret work only through the approved deployment workflow and explicit database-state review. Update checkpoint, registry and coverage ledger with actual CI, source, mapping and live DB evidence; do not claim VERIFIED or production-ready without evidence.

## Known live-data/security gates

Do not include credentials in Git or chat. Content authoring uses server-side AI_COMP_CONTENT_ADMIN_TOKEN; independent content review requires a different AI_COMP_CONTENT_REVIEW_TOKEN and AI_COMP_CONTENT_REVIEWER_ID. Migration 0021 may demote legacy VERIFIED records without reviewer metadata to NEEDS_REVIEW; review this consequence before applying it. Official-source TLS must not be weakened to bypass the current Phase 6.58 blocker.
