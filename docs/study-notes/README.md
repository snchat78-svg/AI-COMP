# AI-COMP Subject-wise Study Notes

**Purpose:** Build source-backed Q&A as subject → book main chapter/topic → internal site/dynasty/theme subtopics before generating MCQ practice and tests. The learner UI should show the book chapter as the main topic, not every site or small subtopic as a separate main topic.

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

- [Rajasthan History](rajasthan-history/README.md): Book Chapter 2 “राजस्थान के प्राचीन सभ्यता स्थल” — 311 Kalibanga + 20 Ahar-Banas + 18 Ganeshwar-Jodhpura + 9 Bairat primary Hindi Q&A drafts in one canonical parent chapter file; all NEEDS_REVIEW.
- [Rajasthan Geography](rajasthan-geography/initial-source-review.md): 29 new Hindi Q&A drafts from the Rajasthan Government “Rajasthan at a Glance” and Forest Department protected-area tables; 7 earlier seed candidates remain separate and need review.
- [Rajasthan Polity & Administration](rajasthan-polity-administration/initial-source-review.md): 27 Hindi Q&A drafts; all NEEDS_REVIEW.
- [Hindi](hindi/initial-source-review.md): 24 Hindi grammar Q&A drafts across वर्णमाला and संधि; all NEEDS_REVIEW.
- [English](english/initial-source-review.md): 23 Q&A drafts across Parts of Speech, Tenses and Modals; questions/answers in Hindi with English examples only where needed; all NEEDS_REVIEW.
- The master structure still tracks all 21 + 24 + 21 canonical concepts in Polity, Hindi and English; these first batches cover only initial subtopics, not whole subjects.

## First content slice

- Subject: Rajasthan History
- Topic: Ancient History
- Main topic: Book Chapter 2 — राजस्थान के प्राचीन सभ्यता स्थल
- Notes: [Combined chapter-2 notes](rajasthan-history/ancient-history/ancient-civilization-sites.md)
- Child-site 1: Kalibanga — `catalog.rajasthan_history_ancient_history_kalibangan`, 311 KAL drafts (11 internal headings).
- Child-site 2: Ahar-Banas — `catalog.rajasthan_history_ancient_history_ahar_banas_culture`, 20 AHB drafts.
- Current state: `DRAFTING / NOT COMPLETE`; all 358 draft Q&A remain `NEEDS_REVIEW`. Ganeshwar-Jodhpura and Bairat have now been added within this same parent chapter; further child-sites require ToC/page scope confirmation. The book TOC image shows the Chapter 2 start at p.145, chapter questions at p.148 and next chapter at p.150. No exam-specific official-syllabus mapping is claimed.

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


## 2026-11-18 — hierarchy-first continuation

- Kalibanga review branch count is now 311 primary Hindi Q&A drafts (KAL-001–KAL-311), with KAL-305–KAL-311 added under the existing architecture subtopic from official ASI Part I printed pp. 130–131. All remain NEEDS_REVIEW; the page-image and figure checks are open.
- PR #115 remains an open review branch until all required checks pass. Flutter workflow SDK drift from 3.47.9 to 3.50.0 was the cause of the analyzer failure; the workflow is being pinned to the known-green 3.47.9 environment pending rerun.
- No Ahar-Banas, second subject, live DB publication, or phase transition is started by this update.


## 2026-11-18 — parent chapter workflow

Book chapters, not every internal site/subheading, are the main topic units. All relevant sites for a chapter must be nested below the same parent topic. For Rajasthan History Chapter 2, use [the combined ancient-civilization-sites file](rajasthan-history/ancient-history/ancient-civilization-sites.md); do not split Kalibanga and Ahar-Banas into separate main topics.


## 2026-11-18 — chapter 2 child-site question batches

The shared parent chapter now contains 358 primary Hindi drafts (KAL 311 + AHB 20 + GJ 18 + BRT 9); all remain NEEDS_REVIEW. New source locators are ASI *Indian Archaeology 1981–82 — A Review*, Ganeshwar excavation pp.61–62, and ASI Jaipur Circle Inventory entry 107, Bairat p.143, with PMML support for the two inscription names. No new main topic was created.

## 2026-11-22 — User-approved strict Rajasthan-first study sequence

The user has explicitly reset the content priority. Follow this strict sequence and do not begin Indian GK while any Rajasthan subject/topic has material coverage or review gaps:

1. **Complete Rajasthan History** — all existing catalogue concepts and book chapters: sources, ancient sites, dynasties, regional states, battles/treaties, architecture, 1857, peasant/tribal movements, Prajamandal, integration, freedom fighters, personalities and all remaining syllabus-backed history themes.
2. **Complete Rajasthan Geography** — physical/location, boundaries, divisions/districts, relief, climate, rivers, lakes, soils, forests, wildlife, protected areas, minerals, energy, irrigation, agriculture, population, maps and regional geography.
3. **Complete Rajasthan Polity & Administration** — constitutional/administrative structure, Governor, CM/Council, Assembly, High Court, districts/divisions, local government, Panchayati Raj, commissions, institutions and state administration.
4. **Complete Rajasthan Art & Culture** — folk deities/saints, sects, fairs/festivals, dances, music, instruments, paintings, architecture, handicrafts, textiles, ornaments, language/dialects, literature and regional traditions.
5. **Complete Rajasthan Economy** — state budget and economic review by year, agriculture, livestock, irrigation, industries, MSME, minerals, energy, tourism, infrastructure, employment, banking/cooperatives, poverty/development indicators and current state schemes.
6. **Complete remaining Rajasthan-specific syllabus areas** — census/demography, tribes, society, education, sports, awards, institutions, environment, schemes and Rajasthan current affairs. Add/extend canonical concept rows rather than create a parallel taxonomy.
7. Only after the Rajasthan completion gate is independently accepted, start **Indian GK** (History → Geography → Polity → Economy → Science/Technology → Art/Culture → national current affairs).
8. Only after Indian GK, cover **Hindi → English → Mathematics → Reasoning → Computer Awareness**, in that order unless a specific official exam syllabus requires a justified reorder.

### One-Liner coverage standard
- Keep the hierarchy Subject → one main topic/chapter → subtopic; show the whole topic in one coherent learner-facing unit. Subtopics are sections within it, not scattered unrelated topic cards.
- Draft concise Hindi question → direct Hindi answer, including English subject questions/answers in Hindi with only necessary English terms/examples retained.
- Use a high-yield checklist (definitions, identities, names, places, dates, sequence, classifications, differences, causes/effects, data/tables/maps, formulas/rules/exceptions and current facts where relevant). No fixed question count; include all important examinable points and avoid repetition/obscure trivia.
- Every factual draft has a reliable source URL and precise page/section/table/notification locator; mark source date for changing facts.
- AI-created content remains NEEDS_REVIEW until independent review. Do not label it VERIFIED or PYQ. Keep real PYQs and practice content separate.
- Finish one main topic fully (content coverage, source audit, duplicate audit, review status and ledger update) before starting another topic.

### Immediate active content
Resume Rajasthan History → Book Chapter 2 “राजस्थान के प्राचीन सभ्यता स्थल” in its canonical parent file. The current 368 candidate Q&A (311 KAL + 20 AHB + 18 GJ + 9 BRT + 10 MTS) are draft/review-pending, not a completed or verified topic. Complete the missing high-yield site coverage, reconcile source conflicts and exact/semantic duplicates, then continue the next history chapter in the supplied book order. India topics are explicitly deferred.

## 2026-11-22 — एक parent topic में पूरा पुस्तक-अध्याय

एक main learner topic पूरा chapter होगा; उसके सभी child sites/themes/subtopics उसी के अंदर रहेंगे। Rajasthan History Chapter 2 “राजस्थान के प्राचीन सभ्यता स्थल” के child units कालीबंगा, आहड़-बनास, गणेश्वर-जोधपुरा, बैराठ/विराटनगर और मत्स्य जनपद हैं। मौजूदा 368 Q&A drafts completion प्रमाणित नहीं करते; प्रत्येक child-site की coverage, source locator, duplicate और independent review gate बाकी है।

**वर्तमान content increment:** कालीबंगा KAL-001–KAL-240 हिंदी-प्रथम हैं (KAL-181–KAL-240 अभी PR #126 branch पर); SQL migration 0030 और offline APK JSON में parity regression जोड़ी गई। सभी drafts NEEDS_REVIEW ही हैं। पूरा Chapter 2 स्वीकार होने से पहले अध्याय 3 या India topics शुरू नहीं होंगे।


## 2026-11-23 — Current Chapter 2 inventory

The exact current Chapter 2 parent file contains 376 question–answer candidates: KAL 311, AHB 26, GJ 18, BRT 11 and MTS 10. Markdown, migration 0030 and offline JSON reconcile at 376/376; exact normalized question-stem and Q&A-pair duplicates: 0. Full learner-facing Q&A text passes the Hindi-first lexical rule.

All entries remain NEEDS_REVIEW. The user has stated that they checked the set, but the formal review endpoint has not yet recorded per-item source-check audit events. Finish the protected review submission and Chapter 2 coverage gates before advancing to the next main topic.
