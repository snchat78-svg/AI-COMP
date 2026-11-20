# Phase 6.56 — Mobile Question Bank Navigation and Topic Search

**Status:** IN_PROGRESS; the first navigation/search/paging slice was merged in PR #42 as d138d65d758efbde5c04126688566d499063da40. Official exam-profile/syllabus mapping remains the next acceptance gate.  
**Exam-syllabus implementation slice:** in branch `phase-6-56-exam-syllabus-mapping`; see [Exam Syllabus Mapping](PHASE_6_56_EXAM_SYLLABUS_MAPPING.md). The API contract, database migration, repository, client and selector are being validated in a separate PR; do not treat them as merged or CI-passing until the registry records exact evidence.  
**Canonical state:** [Phase Registry](PHASE_REGISTRY.md).  
**Persistent restart location:** [Project Continuity Checkpoint](PROJECT_CONTINUITY_CHECKPOINT.md).  
**Full subject/topic content goal:** [One-Liner coverage policy](QUESTION_BANK_CONTENT_COVERAGE.md) and [per-concept CSV ledger](QUESTION_BANK_CONTENT_COVERAGE.csv).

## Existing code to extend

- Dashboard's existing subject selection in PreparationHomeScreen.
- Existing QuestionBankScreen groups the existing concept catalogue by the `topic` field (main chapter) and expands matching `subtopic` concepts (sites/themes). Each child retains its canonical concept_id and opens the existing detail screen.
- Existing topic detail screen with separate One-Liner Q&A and Previous Year tabs.
- Existing authenticated endpoints/client methods for topic listing, verified one-liners and filtered previous papers.
- Existing current-session/test/result flows must remain untouched.

Do not create a parallel topic taxonomy, duplicate content APIs, a new question store, or another test engine.

## Scope in this implementation

- Fetch the topic list through bounded API pages, stopping on the first partial/empty page and enforcing a client-side safety bound.
- Add search across topic label, topic group, subtopic, subject and canonical concept ID.
- Display main-chapter and child-topic totals plus verified one-liner counts without treating catalogue presence as complete coverage.
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

A first implementation slice is now on `phase-6-56-exam-syllabus-mapping`: migration `0023_phase6_56_exam_syllabus_mapping.sql`, a repository that only reads independently reviewed mappings, `GET /question-bank/exam-profiles`, optional `exam_id` filtering for subjects/topics, and a separate mobile exam-syllabus selector. Tests were added for unreviewed-profile/learner-scope behavior and client filter parameters. Its PR and current-head CI status must be recorded in the checkpoint after review.

**Still open:** the official RSSB CET Graduation Level 2026 PDF URL is identified but direct file retrieval/content/SHA-256 has not been independently confirmed. The seed deliberately stays `REVIEW_PENDING`; all 340 generic concepts currently remain unmapped to that exam and no exam-scoped subjects should be shown. Next retrieve/hash/review the actual official document, extract its complete unit/subtopic inventory and exact evidence locators, add any concepts missing from the current catalogue, review every applicable/out-of-scope concept, and only then enable the profile selector. Do not infer official coverage from secondary syllabi.

Keep Phase 6.55's live migration/reviewer-secret gates visible. Continue Q&A authoring from `QUESTION_BANK_CONTENT_COVERAGE.csv` only after official profile scope is established; each topic needs full examinable-point coverage, not merely a fixed count, and draft candidates must remain `NEEDS_REVIEW` until independent review.

## 2026-11-18 — book-chapter grouped mobile navigation

- Mobile navigation is parent chapter → expandable child site/topic → existing content detail. It uses the existing `concepts.topic` and `concepts.subtopic` fields returned by the same topics API; no duplicate navigation API or question store is introduced.
- Migration `0028_book_chapter_hierarchy_for_question_bank.sql` updates only four confirmed Rajasthan History ancient-site concept labels/topic/subtopic values to the user's Chapter 2 parent. Canonical concept IDs are unchanged.
- Search filters child rows and opens the matching parent group automatically. A single group is expanded by default; multiple groups stay collapsed by default. One-Liner Q&A and Previous Year tabs, their paging and evidence display remain unchanged.
- Widget tests cover the four Chapter-2 child sites under one parent. Other book chapters remain on their existing catalogue topic values until the user's ToC confirms their grouping.
- The migration is in Git only; it has not been applied to any live database. Fresh backend and Flutter CI must pass on the exact commit before merging.


## 2026-11-19 — dashboard refresh and one-tap study entry

- Continued Phase 6.56 rather than creating a parallel dashboard flow.
- Dashboard order is now: welcome/status hero → study library → exam syllabus (when available) → verified-pool status → progress → practice test → focus topics → recent tests.
- A clear Study Library card selects a subject and opens the existing question-bank screen. That screen continues to show book chapters as expandable parent groups and sites/themes as child topics; selecting a child opens its One-Liner Q&A and Previous Year tabs.
- Practice Test reuses the same selected subject from Study Library; duplicate subject selectors and duplicate browse controls were removed.
- API connection settings remain accessible in an expandable panel. They are expanded until the first successful connection and collapsed after connection, without storing the access token.
- Dashboard uses responsive cards, a high-contrast welcome panel, clearer progress metrics and large touch targets. Existing Firebase auth, API authentication, session resume, results and adaptive-test logic remain unchanged.
- Phase exit requirement: Flutter analyze, all mobile widget/client tests, backend regression tests, Android release APK build, APK verification and artifact upload must all pass on the same commit. A phase is not completed by code merge alone.


## 2026-11-20 — हिंदी प्रश्न-बैंक और शून्य One-Liner समस्या

- कोड जाँच से कारण पुष्ट: learner API केवल `verification_status='VERIFIED'` वाले प्रश्न लौटाती है। मोबाइल उसी endpoint को उपयोग करता है। इसलिए GitHub के Markdown/CSV में मौजूद drafts API में अपने-आप नहीं आते और शून्य verified count दिख सकता है।
- अध्याय 2 में Git पर 368 हिंदी Q&A drafts हैं (कालीबंगा 311, आहड़-बनास 20, गणेश्वर-जोधपुरा 18, बैराठ 9, मत्स्य जनपद 10)। सभी `NEEDS_REVIEW` हैं। Migration 0022 केवल 10 अतिरिक्त starter candidates डालती है और वे भी `NEEDS_REVIEW` हैं।
- Render workspace में API सेवा `ai-comp-api` live है; उसी workspace में Render-managed PostgreSQL instance नहीं मिला। बाहरी PostgreSQL संभव है; इस जाँच में live DB counts और migration state सत्यापित नहीं हुए।
- नई migration `0029_hindi_question_bank_catalogue.sql` विषय, मुख्य अध्याय और उप-विषय नामों को हिंदी में बदलती है; स्थायी `concept_id` नहीं बदलते। अध्याय 2 के पाँचों उप-विषय “राजस्थान के प्राचीन सभ्यता स्थल” के नीचे रखे जाते हैं।
- मोबाइल Question Bank स्क्रीन के खोज, नेविगेशन, खाली/error संदेश, प्रश्न/उत्तर labels और पुराने प्रश्न lane के UI labels हिंदी किए गए।
- किसी draft को `VERIFIED` नहीं किया गया। स्वतंत्र reviewer स्रोत, प्रश्न, उत्तर, भाषा, topic mapping और duplicate जाँचकर मौजूदा review endpoint से audit note के साथ publish करेगा।
- Phase 6.56 `IN_PROGRESS`; Phase 6.57 `PLANNED`; Phase 6.58 `BLOCKED` रहेंगे। यह increment official syllabus gates या live database migration को complete नहीं बताता।
- शाखा: `fix/question-bank-hindi-catalogue-zero-count-diagnosis`. अगला क्रम: बाहरी DB की सुरक्षित पहचान, migration लागू करना, 368 drafts को existing author flow से `NEEDS_REVIEW` के रूप में load करना, independent review और authenticated APK में live count जाँचना।

See [zero One-Liner diagnosis](PHASE_6_56_ZERO_ONE_LINER_DIAGNOSIS_HINDI.md).
