# AI-COMP Project Continuity Checkpoint

**This file is the first-read checkpoint for every new AI-COMP chat/session.** Do not restart from conversation memory alone. Check the repository state in GitHub because it is the shared durable record.

**Last updated:** 2026-10-23 (exact-head CI passed)  
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
- **Phase 6.56:** IN_PROGRESS. Navigation/search/paging was merged through PR #42 at `d138d65d758efbde5c04126688566d499063da40`. PR #43 is open: https://github.com/snchat78-svg/AI-COMP/pull/43. Its tested head is `6841d953be73608e1f0fd59bddfa2f674b639141`: backend workflow [39899673677](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673677) passed **512 tests with 14 existing warnings**, and the API container build passed; Flutter/APK workflow [39899673666](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673666) passed Flutter analyze, client/widget tests, release APK build, artifact verification and upload. Artifact [12478965187](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673666/artifacts/12478965187) is the uploaded APK artifact ZIP, SHA-256 `8e838dcde7a4e87f226b3114abf10b198a05868cf5dda7581cac424ee5675434`. The earlier backend failure was a stale test expecting a removed INSERT seed; the test now enforces the intended no-unverified-seed policy. **No live exam profile is seeded.** A third-party syllabus page points to the candidate RSSB PDF and claims it is Advertisement 09/2026, but official document bytes/content/digest remain unverified; see the phase spec. PR #43 remains unmerged at this checkpoint. Next: merge this tested implementation slice only after PR head recheck, then continue protected syllabus source + concept mapping author/reviewer workflow inside Phase 6.56. Full syllabus extraction, concept reconciliation, independent mapping reviews, controlled live migration and end-to-end evidence remain open. Do not start Phase 6.57 until all Phase 6.56 exit gates are met.
- **Phase 6.57:** PLANNED — topic coverage, learner mastery and revision.
- **Phase 6.58:** BLOCKED on approved official-source connectivity, live database migration/secrets, real official-paper + matched answer-key records, and live end-to-end proof.

## Full One-Liner coverage requirement

The target is full examinable-point coverage for every applicable subject/topic/subtopic in every supported exam profile—not just meeting a fixed question count. The current catalogue has 340 concept rows across 14 broad subject categories; that is scaffolding, not a complete official syllabus. Final learner-facing One-Liners must be written in question + concise direct answer (Q → A) format, not as bare fact statements. Analyse each topic against its official syllabus and authoritative sources, build a topic-specific checklist of testable knowledge points, draft questions to cover every applicable point, remove duplicates, and track missing points. Five distinct source-backed independently verified Q&As per applicable subtopic is only a minimum floor, not proof of completeness; broad/high-weight topics may require many more. All factual drafts must have source URL and evidence locator and remain NEEDS_REVIEW until an independent reviewer signs them off. No model-generated answer may self-certify as verified. See QUESTION_BANK_CONTENT_COVERAGE.md for the completion checklist and rules.

The CSV ledger currently shows candidate seeds in Git only: 10 pending Q&A across 6 concept IDs; the other 334 catalogue concepts have no candidate in that seed migration. Live database counts have not been queried and are labelled NOT_QUERIED_LIVE_DB.

## Exact next actions at checkpoint creation

1. Resume Phase 6.56 from open [PR #43](https://github.com/snchat78-svg/AI-COMP/pull/43), branch `phase-6-56-exam-syllabus-mapping`. Tested head `6841d953be73608e1f0fd59bddfa2f674b639141) has backend run [39899673677](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673677) passing 512 tests and container build, plus Flutter/APK run [39899673666](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673666) green including artifact [12478965187](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673666/artifacts/12478965187). Re-check current PR head and both checks before merge.
2. After merge of this code slice, create the next PR/subtask within Phase 6.56 for a protected, auditable source + concept-applicability author/reviewer workflow. Reuse review authorization patterns only after auditing their contracts; use distinct server-side author/reviewer secrets, server-derived reviewer identity and append-only audit. Never trust a client-supplied reviewer ID.
3. Official source status: the candidate RSSB URL is linked by [a secondary CET Graduation syllabus page](https://topkaro.com/rssb/cet-graduation/syllabus), which labels it Advertisement 09/2026, but the actual official PDF bytes have not been directly retrieved or hashed in this runtime. Do not create a real seed profile or VERIFIED inventory until the exact official file, issuing board, title/version, dates, content and SHA-256 are independently verified over approved HTTPS/TLS. Do not weaken TLS.
4. Extract the complete official unit/topic/subtopic inventory with exact page/section locators; reconcile every official unit with canonical concepts, add missing concepts/CSV ledger rows, and independently review an IN_SCOPE/OUT_OF_SCOPE decision for every catalogue concept. Until all gates are satisfied, keep exam-scoped subjects/topics unavailable.
5. Once the source, complete inventory and mapping are independently reviewed, test distinct exam scopes and unmapped behavior, apply migrations only through the approved live workflow, and demonstrate actual deployment/mobile E2E evidence.
6. Keep Phase 6.55 live migration/reviewer-secret/data work explicitly tracked; never infer live DB counts or VERIFIED records from Git seeds. Phase 6.57 remains PLANNED until Phase 6.56 acceptance; Phase 6.58 remains BLOCKED until approved official-source connectivity, authentic paper + matched answer key, migrations/secrets and real mobile E2E are proven.
7. Update this checkpoint, the registry and roadmap with observed exact SHA/checks/artifacts and gates, not assumptions. Never claim all subject/topic content or Q&A coverage is complete solely because a catalogue, profile or fixed number of questions exists.

## Known live-data/security gates

Do not include credentials in Git or chat. Content authoring uses server-side AI_COMP_CONTENT_ADMIN_TOKEN; independent content review requires a different AI_COMP_CONTENT_REVIEW_TOKEN and AI_COMP_CONTENT_REVIEWER_ID. Migration 0021 may demote legacy VERIFIED records without reviewer metadata to NEEDS_REVIEW; review this consequence before applying it. Official-source TLS must not be weakened to bypass the current Phase 6.58 blocker.
