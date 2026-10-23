# AI-COMP Project Continuity Checkpoint

**This file is the first-read checkpoint for every new AI-COMP chat/session.** Do not restart from conversation memory alone. Check the repository state in GitHub because it is the shared durable record.

**Last updated:** 2026-10-23  
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
- **Phase 6.56:** IN_PROGRESS; navigation/search/paging was merged through PR #42 at `d138d65d758efbde5c04126688566d499063da40`. PR #43 is still open: https://github.com/snchat78-svg/AI-COMP/pull/43. Before this repair, current head was `2ce303c178a3200a5407d234346350c8cd4f0457`: backend run `39788341935` failed one stale migration-test assumption (511 passed, 1 failed because the test attempted to slice a now-absent `INSERT INTO exam_syllabus_documents` block); Flutter/APK run `39788341858` passed on that older head. Migration `0023` intentionally seeds no exam profile until the exact official notification/syllabus is verified. The RSSB PDF URL in the mapping spec remains only an unverified research lead; document contents and SHA-256 are not confirmed. Continue fixing tests/spec/registry/checkpoint on branch `phase-6-56-exam-syllabus-mapping`, then run backend pytest + API-container build and Flutter analyze/client/widget/release APK/artifact checks on the latest exact commit. Do not merge on the old CI and do not begin Phase 6.57 until Phase 6.56 gates are accepted.
- **Phase 6.57:** PLANNED — topic coverage, learner mastery and revision.
- **Phase 6.58:** BLOCKED on approved official-source connectivity, live database migration/secrets, real official-paper + matched answer-key records, and live end-to-end proof.

## Full One-Liner coverage requirement

The target is full examinable-point coverage for every applicable subject/topic/subtopic in every supported exam profile—not just meeting a fixed question count. The current catalogue has 340 concept rows across 14 broad subject categories; that is scaffolding, not a complete official syllabus. Final learner-facing One-Liners must be written in question + concise direct answer (Q → A) format, not as bare fact statements. Analyse each topic against its official syllabus and authoritative sources, build a topic-specific checklist of testable knowledge points, draft questions to cover every applicable point, remove duplicates, and track missing points. Five distinct source-backed independently verified Q&As per applicable subtopic is only a minimum floor, not proof of completeness; broad/high-weight topics may require many more. All factual drafts must have source URL and evidence locator and remain NEEDS_REVIEW until an independent reviewer signs them off. No model-generated answer may self-certify as verified. See QUESTION_BANK_CONTENT_COVERAGE.md for the completion checklist and rules.

The CSV ledger currently shows candidate seeds in Git only: 10 pending Q&A across 6 concept IDs; the other 334 catalogue concepts have no candidate in that seed migration. Live database counts have not been queried and are labelled NOT_QUERIED_LIVE_DB.

## Exact next actions at checkpoint creation

1. Resume Phase 6.56 from open [PR #43](https://github.com/snchat78-svg/AI-COMP/pull/43) and the branch `phase-6-56-exam-syllabus-mapping`; do not restart merged phases or start Phase 6.57 early.
2. Fix the migration test so it enforces the intended no-unverified-seed policy: no profile/source/mapping INSERT before a real source review. The code's old backend test failure has been isolated; re-run all CI on the repair commit before merge.
3. Keep the candidate RSSB PDF URL in [the Phase 6.56 spec](PHASE_6_56_EXAM_SYLLABUS_MAPPING.md) as a research lead only. Do not claim its notification number, document contents, SHA-256 or syllabus are verified; no exam profile is seeded.
4. Establish approved official HTTPS/TLS retrieval; verify the exact issuing board/notification/document bytes, compute SHA-256, record provenance and independently review the source. Do not disable TLS validation or trust a secondary transcription.
5. Build a protected, auditable author/reviewer workflow with distinct server-side credentials; never accept a learner token or client-supplied reviewer identity as reviewer proof.
6. Extract the complete syllabus unit/topic/subtopic inventory with page/section locators; reconcile every official unit with canonical concepts; add missing stable concepts and CSV ledger rows; independently review an IN_SCOPE/OUT_OF_SCOPE decision for every catalogue concept. Until all gates are satisfied, profile-scoped subjects/topics must remain unavailable.
7. Once official source, complete inventory, and mapping are reviewed, test distinct exam scopes and unmapped behavior, finish exact-head backend + Flutter/APK CI, then complete Phase 6.56 acceptance. Only then begin Phase 6.57 (coverage/mastery/revision); Phase 6.58 remains blocked until live migrations/secrets, authentic official past-paper + matched answer key and real mobile end-to-end proof are available.
8. Keep Phase 6.55 live migration/reviewer-secret/data work explicitly tracked; never infer live DB counts or VERIFIED content from Git seed rows. Update this checkpoint, registry, roadmap and coverage ledger only with observed evidence.

## Known live-data/security gates

Do not include credentials in Git or chat. Content authoring uses server-side AI_COMP_CONTENT_ADMIN_TOKEN; independent content review requires a different AI_COMP_CONTENT_REVIEW_TOKEN and AI_COMP_CONTENT_REVIEWER_ID. Migration 0021 may demote legacy VERIFIED records without reviewer metadata to NEEDS_REVIEW; review this consequence before applying it. Official-source TLS must not be weakened to bypass the current Phase 6.58 blocker.
