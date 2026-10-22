# Phase 6.56 — Mobile Question Bank Navigation and Topic Search

**Status:** IN_PROGRESS; the first navigation/search/paging slice was merged in PR #42 as d138d65d758efbde5c04126688566d499063da40. Official exam-profile/syllabus mapping remains the next acceptance gate.  
**Canonical state:** [Phase Registry](PHASE_REGISTRY.md).  
**Persistent restart location:** [Project Continuity Checkpoint](PROJECT_CONTINUITY_CHECKPOINT.md).  
**Full subject/topic content goal:** [One-Liner coverage policy](QUESTION_BANK_CONTENT_COVERAGE.md) and [per-concept CSV ledger](QUESTION_BANK_CONTENT_COVERAGE.csv).

## Existing code to extend

- Dashboard's existing subject selection in PreparationHomeScreen.
- Existing QuestionBankScreen subject → topic page list.
- Existing topic detail screen with separate One-Liner Q&A and Previous Year tabs.
- Existing authenticated endpoints/client methods for topic listing, verified one-liners and filtered previous papers.
- Existing current-session/test/result flows must remain untouched.

Do not create a parallel topic taxonomy, duplicate content APIs, a new question store, or another test engine.

## Scope in this implementation

- Fetch the topic list through bounded API pages, stopping on the first partial/empty page and enforcing a client-side safety bound.
- Add search across topic label, topic group, subtopic, subject and canonical concept ID.
- Display current topic-list totals and verified one-liner counts without treating catalogue presence as complete coverage.
- Keep One-Liner Q&A and Previous Year Papers as separate tabs, each with independent loading, error/retry and honest empty states.
- Load each content section with separate bounded 100-item requests and separate offsets/loading/error state; provide an explicit Load More action rather than assuming the first page is the complete bank.
- Preserve question source/evidence and official paper/answer-key provenance.

## CI evidence for the merged slice

- Backend tests and API container build passed on PR head c70313064c341b3f517c045a2dc63969b2c58341 (run 39758826307).
- Flutter analyze, all mobile/widget tests, release APK build, artifact verification and upload passed on the same PR head (run 39758826247; artifact 12416808828; SHA-256 10bf4f17bf3ada321c2ce3efab1a99d442f3cc311c34d9a031656f27fcaa1f55).

## Exam-profile/syllabus boundary

The current API's topic catalogue returns generic subjects and concepts; it does not yet prove which topics belong to each specific recruitment exam's official syllabus. This PR must not show the 340-row starter catalogue as a completed exam syllabus or invent exam applicability. Official exam-profile selection/filtered coverage requires sourced exam-notification/syllabus mappings and remains an explicit next gate. The content ledger marks those mappings NOT_YET_MAPPED_TO_EXAM_SPECIFIC_OFFICIAL_SYLLABUS until researched and checked.

## Full topic content objective

The mobile screen must be able to browse the complete ledger, and every applicable topic must eventually have at least five distinct, source-backed, independently reviewed VERIFIED One-Liner Q&A items as a baseline. AI analysis may draft additional candidates, including likely exam-important definitions, dates, facts, comparisons, formulas, rules, examples and common confusions as appropriate, but generated candidates remain NEEDS_REVIEW until the independent review endpoint accepts them. See the [coverage policy](QUESTION_BANK_CONTENT_COVERAGE.md); do not mark topics covered from an empty/partial list or from candidates still in Git.

Current snapshot from repository files only: 340 catalogue concept rows across 14 subjects; 10 candidate seeds across 6 concepts; 334 concepts have no candidate in the current seed migration. No live database count was queried and no migration application is claimed.

## Exit tests

- Flutter analyze and all mobile tests pass.
- Widget tests prove all topic pages can load, topic/subtopic search filters results, One-Liner and Previous Year empty/error states remain independent, and each section can page independently.
- Android release APK build, verification and artifact upload pass on current PR head.
- Existing authentication, dashboard, create/resume session, submit/result and adaptive practice paths continue to pass.
- Phase Registry and continuity checkpoint include current branch, PR, CI evidence, open exam-syllabus mapping gate, live migration gates and next action before merge.

## Next within Phase 6.56

Phase 6.56 stays IN_PROGRESS. First determine the supported exam profiles from existing registered exam records, then research their official notifications/syllabi and implement an auditable exam-profile → applicable canonical concept mapping. Add the profile selector and tests proving that subject/topic options are filtered to the selected exam and that unmapped topics are visible as unmapped rather than silently included. Do not claim the full phase complete until this source-backed mapping passes CI. Keep Phase 6.55's live migration/reviewer-secret gates visible and continue source-backed candidates from QUESTION_BANK_CONTENT_COVERAGE.csv, prioritising rows with no candidates.
