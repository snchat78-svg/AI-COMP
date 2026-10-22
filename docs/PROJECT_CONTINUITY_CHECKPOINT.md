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
- **Phase 6.56:** Starting now — full mobile Question Bank navigation, topic search and coverage visibility. Current screen already has a subject→topic list and distinct One-Liner/Previous-Year tabs; extend it rather than rebuilding it. Existing API has paginated topic and previous-paper queries. Exam-profile-specific syllabus applicability is not yet represented as confirmed data, so do not pretend the starter catalogue is exam-complete.
- **Phase 6.57:** PLANNED — topic coverage, learner mastery and revision.
- **Phase 6.58:** BLOCKED on approved official-source connectivity, live database migration/secrets, real official-paper + matched answer-key records, and live end-to-end proof.

## Full One-Liner coverage requirement

The target is every applicable subject/topic/subtopic for every supported exam profile. The current catalogue has 340 concept rows across 14 broad subject categories; that is scaffolding, not a complete official syllabus. The coverage policy sets an initial target of five distinct source-backed independently verified one-liners per applicable subtopic, more for high-weight topics. AI should proactively draft important, relevant Q&A after analysing the topic and authoritative sources. All factual drafts must have source URL and evidence locator and remain NEEDS_REVIEW until an independent reviewer signs them off. No model-generated answer may self-certify as verified.

The CSV ledger currently shows candidate seeds in Git only: 10 pending Q&A across 6 concept IDs; the other 334 catalogue concepts have no candidate in that seed migration. Live database counts have not been queried and are labelled NOT_QUERIED_LIVE_DB.

## Exact next actions at checkpoint creation

1. Finish Phase 6.56 UI additions in branch feature/phase-6-56-topic-navigation-coverage, starting with all-topic loading (bounded paging), topic/subtopic search, and honest available-vs-verified counts in existing QuestionBankScreen; preserve test sessions and authentication.
2. Add widget tests for searching/navigating the existing topic list, independent One-Liner and Previous-Year empty/error/loading states, and bounded/paged loads.
3. Update Phase Registry and roadmap to Phase 6.56 IN_PROGRESS; link the content coverage ledger and this checkpoint from README.
4. CI validate backend and Flutter/APK on the PR head before merge.
5. After UI acceptance, continue content gap work from the CSV in parallel: source candidates topic by topic, submit NEEDS_REVIEW, independently review, and update ledger counts from actual evidence. Do not apply live migrations without the approved deployment workflow and a database-state review.

## Known live-data/security gates

Do not include credentials in Git or chat. Content authoring uses server-side AI_COMP_CONTENT_ADMIN_TOKEN; independent content review requires a different AI_COMP_CONTENT_REVIEW_TOKEN and AI_COMP_CONTENT_REVIEWER_ID. Migration 0021 may demote legacy VERIFIED records without reviewer metadata to NEEDS_REVIEW; review this consequence before applying it. Official-source TLS must not be weakened to bypass the current Phase 6.58 blocker.
