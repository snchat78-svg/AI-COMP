# Phase 6.53–6.58 — Topic-wise Question Bank and Complete Preparation

**Phase/status source of truth:** [AI-COMP Phase Registry](PHASE_REGISTRY.md). Phase 6.53 application code is merged (PR #36 plus follow-up PR #39); the repository CI checks passed on the PR #39 head before merge. This does **not** mean the question content is complete: one-liners and verified historical questions still depend on reviewed/source-backed records, controlled migration application, and server-side secret configuration. The starter topic list is not a substitute for each exam's official syllabus.  
**Base checkpoint:** Phase 6.52 is merged on `main` (commit `ff21194`, checkpoint commit `f7490fb`).  
**Primary outcome:** A learner can choose an exam profile → subject → topic/subtopic and see source-backed previous-exam questions, important one-liners, practice and revision material for that topic.

## 1. User experience contract

The question bank must be navigable without starting a test first:

1. **Choose exam profile** (start with Rajasthan government exams and allow more profiles later). The syllabus selected for one exam must not silently be treated as the syllabus for every other exam.
2. **Choose a subject**: Rajasthan History, Rajasthan Geography, Rajasthan Polity/Administration, Rajasthan Art & Culture, Rajasthan Economy, Indian History/Geography/Polity, General Science, Hindi, English, Mathematics, Reasoning, Computer and other syllabus-backed subjects.
3. **Choose a topic, then a subtopic**. Examples: Rajasthan Geography → Rivers → Luni River; Hindi → Grammar → Sandhi; Mathematics → Percentage → Successive Percentage; Reasoning → Series → Number Series.
4. The topic page must have clearly separated, independently selectable sections/options:
   - **One-Liner Questions & Answers** — the default study view when a learner opens a topic. Display the topic's available one-liner questions together with their direct answers, one by one or in a searchable/paginated list. The content may be authored directly as short question → answer pairs (for example, "राजस्थान की राजधानी क्या है? — जयपुर") and does not need to be an MCQ. Each entry is mapped to the exact topic/subtopic, carries source/evidence metadata where factual verification is required, and has a review status. Support quick revision and mark-for-review.
   - **Previous Year Papers** — a separate option, never blended into the one-liner list. Show the real past-paper question with its original options, exam/body, year/date, shift and question number where available. Show the verified historical answer only when backed by the paired official answer key; preserve the original paper and answer-key provenance. Do not silently turn an unverified answer into a correct answer.
   - **Practice MCQs** — accepted generated questions clearly labelled as practice, never represented as questions that appeared in an exam.
   - **Topic Test / Revision** — reuse the current test-session, result, weak-topic and adaptive-revision infrastructure. Keep one-liner revision distinct from scoring a previous-paper MCQ test.
5. One-liners may be created/maintained directly by an authorized content author/admin as concise question-and-answer pairs. Store/map them to the canonical subject/topic/subtopic and preserve source, language, verification/review status and timestamps where applicable. Bulk import and manual entry must detect duplicates and must not automatically label unverified facts as verified.
6. The topic page should show separate counts for one-liner Q&A, verified previous-year questions, practice MCQs and unreviewed/verification-needed content. Empty states must be section-specific; an empty previous-year pool must not hide available one-liners, and vice versa.
5. Show a topic coverage summary: subtopics in syllabus, covered subtopics, verified historic questions, accepted one-liners, practice-question count, and any unresolved source/verification gap. Provide search and filters for exam, year, content type and subtopic.

## 2. Existing foundations to reuse — do not rebuild

- `concepts` already stores `concept_id, label, subject, topic, subtopic`; `question_concepts` provides question-to-concept links through `PostgresConceptRepository`.
- Phase 2.2–2.4 already provides source registry, paper research/processing, extracted questions, answer-key resolution, provenance, matching and exam appearances.
- Phase 6.52 already reads verified official history into the bounded practice pool, keeps historical and generated items separate, records provenance in test snapshots, and exposes authenticated `GET /api/v1/learners/{learner_id}/question-bank/readiness`.
- Existing generated-question quality gates and preparation/test/results/revision services must stay the source of truth.

Before adding tables, APIs, services or mobile models, search the repository and existing migrations. Extend `concepts`, `question_concepts`, current history repositories, existing fact/material models and current session contracts wherever adequate. Add a migration only for a real missing persisted concept (for example, a provenance-bearing topic fact or explicit syllabus coverage state). Do not create a duplicate question table, a second test engine, a parallel learner progress store, or a second concept taxonomy without documented proof it is necessary.

## 3. Phase sequence and exit criteria

### Phase 6.53 — Syllabus-backed subject/topic taxonomy

**Starter catalogue currently added:** migration `0020_phase6_53_starter_topic_catalogue.sql` seeds 340 canonical concept/topic entries across 14 broad subjects: Rajasthan History, Rajasthan Geography, Rajasthan Polity and Administration, Rajasthan Art and Culture, Rajasthan Economy, Indian History, Indian Geography, Indian Polity, General Science, Hindi, English, Mathematics, Reasoning and Computer Awareness. The seeds use stable `catalog.*` IDs and are idempotent. They are navigation scaffolding, not a claim that every entry is in every recruitment exam's syllabus or that facts/questions for these topics have been verified.

**Deliver:** Canonical subject → topic → subtopic catalogue for the first supported Rajasthan exam profiles, with stable IDs, labels, parent/child relationship, exam applicability and syllabus/source provenance. Map existing `ConceptRecord` rows and linked questions into it; report unmapped, ambiguous and orphaned records.

**Coverage to seed:** Rajasthan History, Geography, Polity/Administration, Art & Culture, Economy; Indian History, Geography and Polity where in the selected syllabus; General Science (Physics/Chemistry/Biology/Environment); Hindi; English; Maths; Reasoning; Computer and other explicitly supported syllabus sections.

**Rules:** Use official exam notifications/syllabi for exam applicability. A generic subject label is not proof that every exam tests that subject. Seed/upsert must be idempotent; IDs must be stable; translated/alternate labels may be search aliases but cannot create duplicate topics.

**Exit tests:** taxonomy parent/child and exam-profile validation; deterministic/idempotent seed tests; old concepts/questions remain readable; coverage report identifies unknown/unmapped items.

### Phase 6.54 — Topic-wise Previous Exam Question API

**Implementation details:** See [Phase 6.54 Topic Previous-Paper API](PHASE_6_54_TOPIC_PREVIOUS_PAPER_API.md) and the [Phase Registry](PHASE_REGISTRY.md) for current status. Extend the existing route/repository; do not rebuild either.

**Deliver:** An authenticated, paginated topic-content API/query that returns eligible historic questions for a selected canonical topic/subtopic, with exam/year/shift/source filters and topic-level counts.

**Eligibility:** Only historical appearances backed by the existing official-paper and matched official answer-key gates enter the verified-history section. Use existing `exam_appearances`, `appearance_sources`, verification and resolved-answer records. Preserve question identity vs. repeated real exam appearances, and deduplicate copied text without erasing distinct exam appearances. Never infer a repeat count from how many websites copied the question.

**Exit tests:** correct topic and subtopic filtering; multiple exam appearances retained with one canonical question identity; source URLs and answer-key status preserved; pagination bounded; learner/auth scope enforced; unverified, secondary-source-only, malformed and unresolved-answer records do not appear as verified historic questions.

### Phase 6.55 — One-Liner Question-and-Answer Bank (manual authoring supported)

**Current implementation status:** PR #41 is merged as `abfdfbfa8c8b732012c04a247e443032c93f6d01`. The workflow and 10 source-backed Hindi candidate Q&As are in Git; all candidates remain `NEEDS_REVIEW` and are **not counted as verified content**. See [Phase 6.55 source-backed content and independent review workflow](PHASE_6_55_ONE_LINER_SOURCE_REVIEW.md) and the [Phase Registry](PHASE_REGISTRY.md). Migrations have not been applied to a live database and separate server-side reviewer credentials are still required. Registry status is `MERGED_CODE_DATA_PENDING`.


**Deliver:** A topic-linked list of short one-liner **questions with direct answers** (not necessarily MCQs), for example a fact question followed by its exact answer. Authorized editors may type/add these pairs directly in the content workflow. Each entry maps to subject/topic/subtopic and stores language, source/evidence, verification/review state, and timestamps. Reuse the repository's existing fact/material models where fit; introduce a separate persisted record only where the current schema cannot represent a reusable topic-linked Q&A pair.

**Trust rules:** Every factual one-liner needs traceable supporting source evidence. For Rajasthan exam facts, prioritize relevant official government/department publications and the official syllabus; use authoritative textbooks/standard references only under the configured source policy. Current/volatile facts (office holders, budgets, rankings, laws/rules) need an as-of date and refresh policy. AI may summarize or propose facts but cannot self-certify them as verified. Keep disputed/out-of-date facts out of the verified set and send them for review.

**Exit tests:** direct/manual Q&A entry and retrieval; source citation/evidence required for verified status; duplicate/near-duplicate checks; topic mapping; dates and formulas rendered faithfully; Hindi/English text preserved; unverified content visibly separated; no fact can be promoted solely because a model generated it.

### Phase 6.56 — Mobile Subject → Topic → Study page

**Current implementation status:** IN_PROGRESS. This work extends the existing QuestionBankScreen: loads all topics through bounded pages, adds topic/subtopic/concept search, independent One-Liner and Previous-Year content states, refresh/retry, and explicit per-section Load More paging. See [Phase 6.56 mobile navigation contract](PHASE_6_56_MOBILE_QUESTION_BANK_NAVIGATION.md), [Phase Registry](PHASE_REGISTRY.md), and [Project Continuity Checkpoint](PROJECT_CONTINUITY_CHECKPOINT.md).

**Persistent content completeness requirement:** every applicable subject/topic/subtopic for each supported exam must eventually have at least five distinct source-backed independently reviewed VERIFIED one-liners as the baseline. The assistant should proactively research and draft important Q&A, but generated facts remain NEEDS_REVIEW until independent review. The current 340-row generic starter catalogue is not proof of exam-specific syllabus coverage. Track every concept and its next action in [QUESTION_BANK_CONTENT_COVERAGE.csv](QUESTION_BANK_CONTENT_COVERAGE.csv); read the [coverage policy](QUESTION_BANK_CONTENT_COVERAGE.md) before adding candidates. Exam-profile selection cannot claim official applicability until syllabus mapping is evidenced.


**Deliver:** A question-bank entry point in the Flutter dashboard. Navigation: exam profile → subjects → expandable topic/subtopic list → topic page. The topic page must show **One-Liner Q&A** and **Previous Year Papers** as distinct tabs/options, plus Practice MCQs and Topic Test/Revision. One-Liners show short question → direct answer pairs; Previous Year Papers show historical MCQs with original options and verified historical answers, together with exam/year/shift/provenance metadata. Provide independent loading, empty, unavailable and partially populated states for each section.

**Exit tests:** Flutter analyze and widget tests; tap-through navigation and filters; one-liner Q&A and previous-year papers open separately; previous-paper options and answer-review state are shown correctly; long lists are paginated; question source/exam metadata are visible; each section has an independent honest empty state; old login, dashboard, timed session, resume and results flows remain intact.

### Phase 6.57 — Syllabus coverage, mastery and revision

**Deliver:** Track study progress by topic and subtopic using the existing learner-session/results/analytics model. Show not started / studying / revision needed / covered states based on explicit criteria, not merely on visiting a screen. Give revision priority to weak topics and past mistakes using existing adaptive services.

**Exit tests:** coverage progress persists for the authenticated learner; only submitted-test outcomes affect mastery; browsing one-liners does not falsely mark MCQs mastered; weak-topic recommendations map back to the canonical topic; learner data remains isolated.

### Phase 6.58 — Real-data completion and end-to-end proof

**Deliver:** Demonstrate the complete chain for a selected first exam profile: official syllabus → seeded topic map → accessible official paper → extracted questions → matched/verified official answer key → topic-linked verified historical question → source-linked one-liner → visible mobile topic page → topic test → saved result/weak-topic revision.

**Critical prerequisite:** The 20 October 2026 operational checkpoint reports that no registered official source currently passes both TCP and certificate-validated TLS from the research runtime. RSSB/RPSC endpoints time out; the legacy RSSB host fails verified TLS. Restore an approved official HTTPS path or authorized runtime/network configuration. Do not weaken TLS, bypass robots/terms/host policies or manufacture questions to inflate counts.

**Exit tests:** nonzero real source-backed counts from the live readiness/content endpoints; inspect source and answer-key URLs; end-to-end tests run against real persisted records; verify no fake history or fabricated readiness; capture a mobile test-flow result. A CI run with zero selected papers is not success evidence.

## 4. Current content and completion boundary

- Migration `0019_phase6_53_topic_one_liners.sql` stores short topic-linked direct Q&A, with source evidence, language, importance, deduplication and review state. Only reviewed `VERIFIED` items appear in the learner-facing One-Liner Q&A list.
- Migration `0020_phase6_53_starter_topic_catalogue.sql` makes the subject/topic browser navigable across 14 starter subject categories; it does not seed invented answers or mark a topic as exam-complete.
- The previous-paper tab reads only official-paper + matched official-answer-key verified history and displays options, answer and source provenance separately.
- The generation flow creates new four-option practice MCQs from reviewed one-liner Q&A and verified previous-paper answer facts; it does not add generated items to official history.
- The actual learner-ready content bank is **not populated/completed by migrations alone**. One-liner source entries need to be added/reviewed through the protected authoring flow; previous-year history requires successful official paper discovery and answer-key reconciliation. Migration application, server-secret configuration and fresh CI verification remain deployment gates.

## 4. Completion definition

A topic is shown as **covered** only when:
- its selected exam profile has an authoritative syllabus/topic checklist;
- every required subtopic has an explicit coverage state;
- the verified previous-question count and accepted one-liner count are shown separately;
- unresolved sources, missing papers or unverified facts remain visible;
- the learner has completed the defined revision checks if learner mastery is also shown.

“Complete preparation” is a coverage goal, not a claim that a finite database contains every question ever asked. The app should tell the learner exactly what is verified, what is still missing, and when a source was last checked.

## 5. Cross-cutting quality and safety gates

- Keep manual/source-backed one-liner Q&A, historical exam questions, and generated practice MCQs as distinct content types with explicit source/provenance and separate UI options.
- No answer-key guess is marked official/verified. Preserve correct answers from the paired, verified key.
- Keep all data access bounded, paginated and authenticated, with learner identity bound to the verified Firebase UID on protected learner routes.
- Use deterministic fixtures in CI; live AI providers must not be required for unit tests.
- Add migration up/down or migration-chain checks as required by project conventions, API contract tests, repository integration tests and Flutter tests for every completed phase.
- Maintain the master checkpoint with branch/commit, tests run, CI evidence, live-data caveats and the next exact phase. Do not restart completed Phases 1–6.52.

## 6. Immediate implementation order (checkpoint updated 2026-10-22)

1. Continue Phase 6.56 mobile topic search and independent paged One-Liner/Previous-Year views; validate Flutter widget tests and release APK CI before merge.
2. Keep Phase 6.55 merged code at MERGED_CODE_DATA_PENDING until migrations are safely applied, distinct author/reviewer secrets are configured, and source-backed candidate review is recorded.
3. Build candidate Q&A topic-by-topic from [the permanent coverage policy](QUESTION_BANK_CONTENT_COVERAGE.md) and [per-concept ledger](QUESTION_BANK_CONTENT_COVERAGE.csv); prioritize concepts with no candidates. Update evidence/status counts only after confirming the actual database/review audit.
4. Implement Phase 6.57 only from its planned existing learner-session/results/mastery requirements after Phase 6.56 acceptance.
5. Keep Phase 6.58 blocked until approved official HTTPS/TLS access is restored, persisted official paper + matched answer-key data exists, migrations/secrets are verified and a real-data mobile end-to-end test passes.

Read [PROJECT_CONTINUITY_CHECKPOINT.md](PROJECT_CONTINUITY_CHECKPOINT.md) before work in every new chat; do not restart Phases 6.53–6.55.

This document records the plan and constraints; it does not claim phases 6.53–6.58 or nationwide topic coverage have already been implemented.
