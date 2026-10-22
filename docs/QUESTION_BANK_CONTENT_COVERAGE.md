# AI-COMP One-Liner Content Coverage — Permanent Requirement

**Canonical phase/status source:** [Phase Registry](PHASE_REGISTRY.md)  
**Machine-readable topic ledger:** [QUESTION_BANK_CONTENT_COVERAGE.csv](QUESTION_BANK_CONTENT_COVERAGE.csv)  
**Roadmap:** [Topic-wise Question Bank roadmap](PHASE_6_53_TOPICWISE_QUESTION_BANK_ROADMAP.md)  
**Last checkpoint:** 2026-10-22

## Non-negotiable product goal

The Question Bank must eventually cover **every applicable subject, topic and subtopic for each supported exam profile** with concise, useful One-Liner Questions & Answers. Do not treat the current starter catalogue as proof of full syllabus coverage. Use each exam's official notification/syllabus to mark topic applicability; different exams may include different topics.

The assistant/implementation agent should proactively analyse the topic and draft important question-answer candidates. This includes definitions, dates, people/places, facts, differences/comparisons, cause/effect, lists, formulas and calculation methods as appropriate to the subject. AI drafting is allowed; AI self-certification is not. Every factual candidate needs an attributable source URL and a short locator/evidence note and stays NEEDS_REVIEW until an independent reviewer confirms it.

## Coverage standard

For the initial baseline, target **at least 5 distinct, non-duplicate, source-backed, independently verified one-liners per applicable subtopic**. This is a minimum baseline, not a limit: important/high-weight topics may need more. A topic is not "fully covered" just because it has five questions if those five repeat the same fact or omit required parts of the official syllabus.

For a topic to be counted as covered, all must be true:

1. The topic is mapped to the selected exam profile using an official exam notification/syllabus, with source and date.
2. The question bank has at least five accepted distinct one-liners for that topic, unless the exam-specific syllabus/reviewer explicitly documents why a smaller number is appropriate.
3. Each accepted item carries concept_id, Hindi/English language, HTTPS source URL, source evidence/section locator, importance score, source-check date, independent reviewer, review note and VERIFIED status.
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
