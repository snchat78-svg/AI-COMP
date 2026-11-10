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

## First content slice

- Subject: Rajasthan History
- Topic: Ancient History
- Subtopic: Kalibangan
- Concept ID: `catalog.rajasthan_history_ancient_history_kalibangan`
- Notes: [Kalibangan — one-liner Q&A notes](rajasthan-history/ancient-history/kalibangan.md)
- Current state: `DRAFTING / NOT COMPLETE`; 160 main Q&A stems are AI-authored question wording with source-paraphrased answers (not copied PYQs), 3 classroom-source items are labelled corroborative, 2 ASI-hosted images are linked, all items remain `NEEDS_REVIEW`, and no exam-specific official-syllabus mapping is claimed.

## Standard for every notes file

Each notes file must include:
- stable catalogue concept ID and hierarchical subject/topic/subtopic;
- concise, unambiguous Hindi Q → A pairs (English terms in brackets where useful);
- source reference IDs with URLs and exact evidence locators;
- a topic checklist showing covered, not-applicable and still-missing knowledge-point dimensions;
- known source conflicts, uncertain claims and excluded myths/unsupported facts;
- explicit status and a next research/review action.

Do not create a fixed question-count ceiling. Add Q&As until all syllabus-relevant and source-supported examinable points have been considered, duplicates removed and independent review completed.
