# AI-COMP One-Liner Content Coverage — Permanent Requirement

**Canonical phase/status source:** [Phase Registry](PHASE_REGISTRY.md)  
**Machine-readable topic ledger:** [QUESTION_BANK_CONTENT_COVERAGE.csv](QUESTION_BANK_CONTENT_COVERAGE.csv)  
**Roadmap:** [Topic-wise Question Bank roadmap](PHASE_6_53_TOPICWISE_QUESTION_BANK_ROADMAP.md)  
**Last checkpoint:** 2026-10-30

## Non-negotiable product goal

The Question Bank must eventually cover **every applicable subject, topic and subtopic for each supported exam profile** with concise, useful One-Liner Questions & Answers. Do not treat the current starter catalogue as proof of full syllabus coverage. Use each exam's official notification/syllabus to mark topic applicability; different exams may include different topics.

The assistant/implementation agent should proactively analyse the topic and draft important question-answer candidates. This includes definitions, dates, people/places, facts, differences/comparisons, cause/effect, lists, formulas and calculation methods as appropriate to the subject. AI drafting is allowed; AI self-certification is not. Every factual candidate needs an attributable source URL and a short locator/evidence note and stays NEEDS_REVIEW until an independent reviewer confirms it.

## What “complete topic coverage” means (explicit product rule)

**The user’s intended meaning of coverage is full examinable-point coverage, not merely reaching a question count.** For every applicable official-syllabus topic/subtopic, analyse the topic and its authoritative sources until all syllabus-relevant, reasonably testable knowledge points have been considered and covered. Do not label a topic complete just because it has five (or any fixed number of) questions.

**Question-bank format: write each item as a clear question followed by its short, direct answer (Q → A).** Do not store only a bare fact sentence as the final learner-facing One-Liner. A factual line may be used in research notes, but turn it into an exam-useful question, for example:
- Fact note: “The Luni River drains into the Rann of Kutch.”
- One-liner: “Where does the Luni River drain? — Into the Rann of Kutch.”
- Where a fact has multiple separately testable parts, create separate questions for those parts rather than hiding several answers inside one overloaded question. Do not inflate coverage with superficial rewordings of the same fact.

For each topic, use a documented completion checklist tailored to its content and syllabus. Consider the applicable lenses below, then mark each as covered / not applicable / still missing, with evidence:
- Definitions, meaning, identity and distinguishing features.
- All named people, places, institutions, events and dates/years required by the syllabus.
- Categories, lists, examples, classifications and their members.
- Differences, comparisons, relationships, causes/effects and sequences.
- Formulae, units, methods, rules, legal provisions, exceptions and boundary conditions.
- Important data and exam-relevant static facts; date-stamp facts that can change.
- Diagrams, maps, tables, works or named items when they are part of the official syllabus/source.
- Common confusions and frequently testable distinctions, without duplicating an already-covered fact.
- Every official-syllabus subtopic and any subtopic discovered in authoritative source material that is genuinely required by that syllabus.

The checklist is complete only after the source-backed knowledge points have been reviewed for omissions, candidate questions cover those points without material gaps, duplicates have been removed, and independent review accepts the set. If a topic is broad, split it into smaller concepts/subtopics in the ledger first. A source or a human reviewer may justify why a lens is not applicable; never silently skip it.

The “at least five distinct Q&As per applicable subtopic” rule below is a **minimum progress floor**, not the definition of completeness and not permission to stop at five. A narrow topic may warrant fewer only with a documented reviewer rationale; a broad or high-weight topic will usually need substantially more. Report status as NOT_STARTED / DRAFTING / NEEDS_REVIEW / PARTIALLY_COVERED / VERIFIED_COMPLETE (or the repository’s equivalent) so a partial set is never presented as fully complete.

## Coverage standard

For the initial baseline, target **at least 5 distinct, non-duplicate, source-backed, independently verified one-liners per applicable subtopic**. This is a minimum baseline, not a limit: important/high-weight topics may need more. A topic is not "fully covered" just because it has five questions if those five repeat the same fact or omit required parts of the official syllabus.

For a topic to be counted as VERIFIED_COMPLETE, all must be true:

1. The topic is mapped to the selected exam profile using an official exam notification/syllabus, with source and date.
2. The topic-specific completion checklist above is complete with no unresolved syllabus-relevant knowledge-point gaps; at least five accepted distinct Q&As are present as a minimum floor, unless the exam-specific syllabus/reviewer documents why a smaller number is appropriate.
3. Each accepted item is phrased as a clear question with a concise direct answer and carries concept_id, Hindi/English language, HTTPS source URL, source evidence/section locator, importance score, source-check date, independent reviewer, review note and VERIFIED status.
4. No unresolved disputed/current/outdated claim is counted as covered. Volatile facts carry an as-of date and refresh rule.
5. Coverage summaries distinguish drafted, needs_review, verified, and rejected; candidates in Git migration files are not proof of live database population.
6. Empty/null coverage stays visible. Never inflate the count with duplicates, generated MCQs, previous-paper appearances copied between sites, or unreviewed candidates.

## How to build the content

For each ledger row, analyse the exact topic/subtopic; research the official exam syllabus and authoritative primary government/department/official reference first; draft concise question → direct answer pairs; attach URL + section/page/heading evidence; calculate/check duplicate hash against the existing canonical store; add candidates through the existing one-liner authoring path as NEEDS_REVIEW; and send them to a separate reviewer. Use the existing question_bank_one_liners, PostgresTopicQuestionBankRepository, authoring endpoint and independent-review endpoint. Do not create a duplicate Q&A table or a parallel taxonomy.

Use the following lenses as applicable (not every lens fits every subject):
- Core definition/meaning and identifying feature.
- Key place, person, date/year, event, institution or legal provision.
- Important categories, lists, examples and classifications.
- Differences, relationships, comparisons and cause/effect.
- Formulas, units, rules, exceptions, and a small checked calculation/example.
- Exam-relevant static facts plus as-of date and refresh rule for changing facts.
- Common confusions and boundary conditions; no question should conceal ambiguity.
- Hindi wording and terms that match the relevant syllabus; maintain English candidates where that exam requires them.

## Current inventory snapshot (from Git, not live DB)

The starter catalogue migration currently defines **340 concept/topic rows across 14 broad subjects**. Candidate seed migration 0022_phase6_55_seed_one_liner_candidates.sql contains **10 pending Hindi candidates across 6 concept IDs**. The remaining **334 catalogue concept IDs have no candidate in that seed migration**. The database has not been queried here, so live counts are recorded as NOT_QUERIED_LIVE_DB; do not interpret that as a measured database count. No seeded candidate is considered verified merely because it exists in Git.

The 14 starter categories are Rajasthan History, Rajasthan Geography, Rajasthan Polity and Administration, Rajasthan Art and Culture, Rajasthan Economy, Indian History, Indian Geography, Indian Polity, General Science, Hindi, English, Mathematics, Reasoning and Computer Awareness. These are broad navigation groupings only; they must be reconciled to each chosen exam's official syllabus, and extra official syllabus topics must be added to the catalogue/ledger.

The current catalogue row count by subject is:

| Subject | Concepts in current catalogue |
|---|---:|
| Rajasthan History | 34 |
| Rajasthan Geography | 32 |
| Rajasthan Polity and Administration | 21 |
| Rajasthan Art and Culture | 29 |
| Rajasthan Economy | 21 |
| Indian History | 23 |
| Indian Geography | 20 |
| Indian Polity | 25 |
| General Science | 25 |
| Hindi | 24 |
| English | 21 |
| Mathematics | 22 |
| Reasoning | 23 |
| Computer Awareness | 20 |
| **Total** | **340** |

At five baseline Q&A per concept, the naive full-catalogue baseline would be 1,700 Q&As; the actual applicable target must first be reconciled to each exam's official syllabus. Current candidates are only 10 across 6 concepts (all pending review); 334 concepts have no candidate in the current seed migration.

## Ledger contract

QUESTION_BANK_CONTENT_COVERAGE.csv has one row per current catalogue concept and records:
- subject/topic/subtopic and stable concept_id;
- exam-syllabus mapping status;
- candidate count currently present in Git migration seeds;
- live verified count (currently NOT_QUERIED_LIVE_DB);
- baseline target of 5 verified unique Q&A;
- current gap and next concrete action.

Whenever a content seed, review, syllabus mapping, source check or live migration changes, update this CSV and record the commit/evidence in Phase Registry. Do not mark a ledger row covered without the evidence described above. For new concepts, add a row rather than leaving it invisible.

## Persistent restart instructions for every new chat/session

1. Open PROJECT_CONTINUITY_CHECKPOINT.md first.
2. Read PHASE_REGISTRY.md, then this file, then the CSV ledger before touching code or content.
3. Continue the phase currently marked IN_PROGRESS or the next PLANNED phase. Do not repeat merged phases; reopen them only for a concrete defect.
4. Prioritize the oldest/highest-gap ledger rows and source the facts. Keep all unreviewed candidates NEEDS_REVIEW.
5. Record completed work, PR/commit SHA, CI, live migration status, verified candidate counts and the exact next action back into the checkpoint/registry.


## Product separation: One-Liners vs Previous Year Papers (permanent requirement)

See the full [Question Bank Product Contract](QUESTION_BANK_PRODUCT_CONTRACT.md). Keep these as two separate learner-facing lanes:

- **One-Liners:** Subject → Topic → Subtopic → concise Q → A. The target is full examinable-point coverage for every topic applicable to the selected exam's official syllabus, with evidence, deduplication and independent review. A question-count threshold alone does not prove completeness.
- **Previous Year Papers / Old Papers:** actual historical and newly published paper artifacts from official sources, with paper identity, year, source provenance, original document and verified matching answer-key information where available.
- Existing official-source discovery/processing should poll registered sources on schedule and automatically surface newly published papers only after integrity and review gates pass. A paper appearing here does not automatically promote its questions into the approved One-Liner bank.
- Record blocked/failed connectivity honestly. As of 2026-10-26, the official-source network/TLS gate remains blocked; no successful live auto-update has been demonstrated. Do not claim otherwise or weaken TLS.


## 2026-10-30 generation workflow checkpoint

The mainline candidate-generation implementation is being added within Phase 6.56. It is concept-by-concept and requires an authorized operator to provide a bounded excerpt and locator from a checked source. It is not automatic source discovery and does not generate or certify the full 340-concept catalogue in one run. Continue to treat every catalogue row as a coverage obligation to reconcile against each chosen official exam syllabus; do not count a draft, AI importance score, question count, or Git seed as VERIFIED_COMPLETE.


## One-Liner format gate — 30 October 2026

AI-generated candidates must be short direct Q&A, not essay snippets: one question ending in a single question mark, no line breaks, at most 240 characters for each field, and a concise non-question answer. The application enforces these structural rules before persistence; malformed items are rejected. This is not a factual verification or completeness signal. Keep all candidates NEEDS_REVIEW until an independent reviewer verifies source authority, exact evidence, answer correctness, date-sensitivity and fit to the selected exam's reviewed syllabus. A per-topic count is not proof that all examinable points are covered.
