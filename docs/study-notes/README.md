# AI-COMP Subject-wise Study Notes

**Purpose:** Build a complete, source-backed Q&A notes collection subject → topic → subtopic before generating MCQ practice and tests from that content.

**Canonical coverage policy:** [Question Bank Content Coverage](../QUESTION_BANK_CONTENT_COVERAGE.md)  
**Canonical concept ledger:** [QUESTION_BANK_CONTENT_COVERAGE.csv](../QUESTION_BANK_CONTENT_COVERAGE.csv)  
**Phase status:** [Phase Registry](../PHASE_REGISTRY.md)

## Content-first order

1. Create study notes as concise one-liner questions with direct answers.
2. Break each concept into independently testable knowledge points. Include definitions, identity, names, places, dates, lists, classifications, comparisons, causes/effects, sequences, formulas/rules, exceptions and relevant applications.
3. Attach a reliable source URL and a precise page/section/heading/evidence locator to every factual answer.
4. Check exact and near-duplicate meaning before adding a candidate.
5. Keep all newly drafted facts in `NEEDS_REVIEW` until a separate reviewer checks the source and answer. AI drafting is not independent verification.
6. Maintain a topic coverage checklist. A topic stays `DRAFTING`, `PARTIALLY_COVERED` or `NEEDS_REVIEW` while any material point is missing or disputed.
7. After notes are reviewed, generate practice MCQs from those notes. Keep generated MCQs separate from actual previous-year questions and their official answer-key provenance.
8. Later map the notes to each exam's official syllabus. A generic reference note must not be labelled as an exam-specific verified syllabus item without an independently reviewed mapping.

## Master topic structure

See [Master Subject–Topic–Subtopic Structure](MASTER_SUBJECT_TOPIC_STRUCTURE.md) for the bilingual, canonical topic tree across Rajasthan History, Rajasthan Geography, Rajasthan Polity & Administration, Hindi and English. It lists all 132 existing subtopic concept IDs, current seed/draft status, the first gap-check list and the Hindi-only Q&A rule.

## Subject order from the existing catalogue

The existing 340 concept rows across 14 navigation subjects remain the working catalogue. They are not proof that any one examination syllabus is complete.

1. Rajasthan History — 34 concepts
2. Rajasthan Geography — 32
3. Rajasthan Polity and Administration — 21
4. Rajasthan Art and Culture — 29
5. Rajasthan Economy — 21
6. Indian History — 23
7. Indian Geography — 20
8. Indian Polity — 25
9. General Science — 25
10. Hindi — 24
11. English — 21
12. Mathematics — 22
13. Reasoning — 23
14. Computer Awareness — 20

## Subject progress trackers

- [Rajasthan History — all 34 catalogue topics](rajasthan-history/README.md). Work through the list in order and close each topic's coverage gaps before moving forward.

## Existing drafts — queued, not being expanded in parallel

- [Rajasthan History](rajasthan-history/README.md): Kalibangan — 304 primary Hindi Q&A drafts in the single canonical topic file on the current review branch; all NEEDS_REVIEW.
- [Rajasthan Geography](rajasthan-geography/initial-source-review.md): 29 new Hindi Q&A drafts from the Rajasthan Government “Rajasthan at a Glance” and Forest Department protected-area tables; 7 earlier seed candidates remain separate and need review.
- [Rajasthan Polity & Administration](rajasthan-polity-administration/initial-source-review.md): 27 Hindi Q&A drafts; all NEEDS_REVIEW.
- [Hindi](hindi/initial-source-review.md): 24 Hindi grammar Q&A drafts across वर्णमाला and संधि; all NEEDS_REVIEW.
- [English](english/initial-source-review.md): 23 Q&A drafts across Parts of Speech, Tenses and Modals; questions/answers in Hindi with English examples only where needed; all NEEDS_REVIEW.
- The master structure still tracks all 21 + 24 + 21 canonical concepts in Polity, Hindi and English; these first batches cover only initial subtopics, not whole subjects.

## First content slice

- Subject: Rajasthan History
- Topic: Ancient History
- Subtopic: Kalibangan
- Concept ID: `catalog.rajasthan_history_ancient_history_kalibangan`
- Notes: [Kalibangan — one-liner Q&A notes](rajasthan-history/ancient-history/kalibangan.md)
- Current state: `DRAFTING / NOT COMPLETE`; the merged mainline has 287 AI-authored question stems, and the pending hierarchy/content branch adds KAL-288–KAL-304 (17 more) for 304 total. Question wording is AI-authored Hindi and answers are source-paraphrases, not copied PYQs. The file has one canonical Kalibanga topic with an 11-subtopic internal index; 3 classroom-source items are separately labelled corroborative, 2 ASI-hosted images are linked, and all Q&A remain `NEEDS_REVIEW`. ASI Part II cemetery plan/view locators are pp. 1288–1290; visual review, KLB-4/KLB-8, group-count, Burial 13 urn and complete ASI MASI 98/Part I review remain open. No exam-specific official-syllabus mapping is claimed.

## Standard for every notes file

Each notes file must include:
- stable catalogue concept ID and hierarchical subject/topic/subtopic;
- concise, unambiguous Hindi Q → A pairs (English terms in brackets where useful);
- source reference IDs with URLs and exact evidence locators;
- a topic checklist showing covered, not-applicable and still-missing knowledge-point dimensions;
- known source conflicts, uncertain claims and excluded myths/unsupported facts;
- explicit status and a next research/review action.

Do not create a fixed question-count ceiling. Add Q&As until all syllabus-relevant and source-supported examinable points have been considered, duplicates removed and independent review completed.


## 2026-11-10 — canonical mapping and table-schema quality correction

- All 57 first-batch questions across Geography (14), Rajasthan Polity (17), Hindi (12) and English (14) now carry the exact stable concept ID for the tested subtopic. Multi-section Geography and Polity tables have consistent column headers for these IDs.
- Corrected English topic mapping: ENG-001–009 → Parts of Speech (9); ENG-010–011 → Tenses (2); ENG-012–014 → Modals (3). The master coverage matrix now shows those separate per-subtopic counts instead of incorrectly placing all 14 under Parts of Speech.
- Corrected the SFC preface locator wording to “प्रस्तावना (Preface)” rather than treating the prefatory Roman page marker as a printed page number.
- All new questions and answers remain in Hindi; English-language words/phrases appear only when they are the subject of the English-language example. All drafts remain NEEDS_REVIEW; no live DB semantic duplicate scan or independent reviewer approval is claimed.
- Current first-batch totals remain Geography 14 + Polity 17 + Hindi 12 + English 14 = 57 new markdown Q&A; Kalibangan remains 282. Seven previous Geography migration seeds remain separate and pending review. No code/database/migration/APK change or phase transition.


## 2026-11-10 — Rajasthan Geography protected-area second batch

- Added RGEO-015–RGEO-029 (15 new Hindi Q&A) under the canonical concept `catalog.rajasthan_geography_climate_and_environment_national_parks_and_sanctuaries`, using the Rajasthan Forest Department's “National Parks and Sanctuaries in Rajasthan” table. The questions cover Mukundara Hills, Band Baretha, Bhensrodgarh, Desert National Park Sanctuary (as labelled in the table), Phulwari ki Naal, Jamwa Ramgarh, Kumbhalgarh, Mount Abu, Tal Chhapar, Sariska, Sitamata, Ramgarh Vishdhari and National Gharial Sanctuary.
- Current Rajasthan Geography markdown total is **29 new Hindi Q&A (RGEO-001–RGEO-029)**, all NEEDS_REVIEW, plus 7 separate older migration seed candidates (Aravalli 1, Thar 1, Luni 2, Banas 1, National Parks/Sanctuaries 2). The old seeds have not been merged into the markdown file or counted as reviewed content.
- Exact/normalized in-file audit after this increment: IDs continuous; 0 normalized duplicate questions; 0 exact normalized Q&A duplicates; each row has a stable concept ID and source locator; all questions/answers under 240 characters. No live DB semantic duplicate scan or independent reviewer check is claimed.
- The master structure, README, roadmap and phase registry/continuity now distinguish the 29 new markdown questions from the 7 older seed candidates. No app code, migration, live DB, APK or learner-visible VERIFIED record changed. Phase 6.56 remains IN_PROGRESS; Phase 6.57 PLANNED.


## 2026-11-10 — English Tenses subtopic expansion

- Added ENG-015–ENG-023 (9 Hindi-question/Hindi-answer Q&A) under canonical concept `catalog.english_grammar_tenses`. Topics include present simple/continuous uses, stative-verb usage, past simple with definite time, present perfect continuity, timetable future use and present tense in future time clauses.
- The previous 14-question English batch is now 23 total: Parts of Speech 9, Tenses 11, Modals 3. All questions/answers remain Hindi; English terms/examples are shown only as the target language content. All remain NEEDS_REVIEW.
- Source references are Cambridge English Grammar Today: Present, Present simple or present continuous, Past simple or present perfect, and Present simple. Cambridge is a grammar reference, not an exam syllabus; RBSE/selected exam applicability must be mapped separately.
- No MCQ generation, app code, database, migrations, APK or learner publication. No phase transition; Phase 6.56 IN_PROGRESS and Phase 6.57 PLANNED.


## 2026-11-10 — sequential topic rule

- Kalibanga now contains 287 AI-authored Hindi Q&A drafts (KAL-001–KAL-287), 3 separately labelled corroborative items and 2 ASI photographs. All Q&A remain NEEDS_REVIEW; the topic is not complete.
- User-directed workflow: finish Kalibanga first. Other subject drafts are parked; do not create fresh parallel question batches until the active topic passes its source, coverage, duplicate and independent-review gates.
- APK CI now also runs on documentation-note pull requests. Its APK represents the existing mobile app; documentation drafts are not automatically included in the app or live database.


## 2026-11-12 — hierarchy-first continuation

- Current review branch `content/kalibangan-single-topic-hierarchy-structure` keeps Kalibanga as one canonical topic and adds an 11-subtopic index inside that topic file.
- KAL-288–KAL-304 add 17 Hindi One-Liners under the existing “नगर-योजना, किलेबंदी, आवास और जल-निकासी” subtopic. They are AI-authored, source-located drafts, not PYQs, and remain NEEDS_REVIEW.
- The hierarchy examples are now permanent: dynasty histories stay under one dynasty subtopic; rulers are nested in chronological internal sections; a broad jewellery topic remains one parent topic with material/type/technique/region subtopics. No unrelated top-level topic proliferation.
- The new branch is not merged yet. No app code, database, migration, learner-visible verified content or APK changed.


- Latest subtopic extension: KAL-301–KAL-304 adds clay bonding-material colour and waterlogging, road reconstruction phases, incised floor tiles and street-side doors opening into courtyards. These remain within the same Kalibanga architecture subtopic. Review-branch total: 304 primary Q&A; all remain NEEDS_REVIEW.
