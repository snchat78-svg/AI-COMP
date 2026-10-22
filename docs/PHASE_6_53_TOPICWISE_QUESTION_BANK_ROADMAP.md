# Phase 6.53–6.58 — Topic-wise Question Bank and Complete Preparation

**Status:** Roadmap recorded; implementation phases 6.53–6.58 are not yet complete.  
**Base checkpoint:** Phase 6.52 is merged on `main` (commit `ff21194`, checkpoint commit `f7490fb`).  
**Primary outcome:** A learner can choose an exam profile → subject → topic/subtopic and see source-backed previous-exam questions, important one-liners, practice and revision material for that topic.

## 1. User experience contract

The question bank must be navigable without starting a test first:

1. **Choose exam profile** (start with Rajasthan government exams and allow more profiles later). The syllabus selected for one exam must not silently be treated as the syllabus for every other exam.
2. **Choose a subject**: Rajasthan History, Rajasthan Geography, Rajasthan Polity/Administration, Rajasthan Art & Culture, Rajasthan Economy, Indian History/Geography/Polity, General Science, Hindi, English, Mathematics, Reasoning, Computer and other syllabus-backed subjects.
3. **Choose a topic, then a subtopic**. Examples: Rajasthan Geography → Rivers → Luni River; Hindi → Grammar → Sandhi; Mathematics → Percentage → Successive Percentage; Reasoning → Series → Number Series.
4. The topic page provides distinct sections/tabs:
   - **Previous Exam Questions** — source-verified historic question, exam/body, year/date, shift, question number when available, verified answer/explanation, and original paper/official answer-key provenance.
   - **Important One-Liners** — short revision facts/rules/formulas, linked to the exact topic/subtopic and supported by a trusted source.
   - **Practice** — accepted generated MCQs clearly labelled as practice, never represented as a question that appeared in an exam.
   - **Topic Test / Revision** — reuse the current test session, results, weak-topic and adaptive revision infrastructure.
5. Show a topic coverage summary: subtopics in syllabus, covered subtopics, verified historic questions, accepted one-liners, practice-question count, and any unresolved source/verification gap. Provide search and filters for exam, year, content type and subtopic.

## 2. Existing foundations to reuse — do not rebuild

- `concepts` already stores `concept_id, label, subject, topic, subtopic`; `question_concepts` provides question-to-concept links through `PostgresConceptRepository`.
- Phase 2.2–2.4 already provides source registry, paper research/processing, extracted questions, answer-key resolution, provenance, matching and exam appearances.
- Phase 6.52 already reads verified official history into the bounded practice pool, keeps historical and generated items separate, records provenance in test snapshots, and exposes authenticated `GET /api/v1/learners/{learner_id}/question-bank/readiness`.
- Existing generated-question quality gates and preparation/test/results/revision services must stay the source of truth.

Before adding tables, APIs, services or mobile models, search the repository and existing migrations. Extend `concepts`, `question_concepts`, current history repositories, existing fact/material models and current session contracts wherever adequate. Add a migration only for a real missing persisted concept (for example, a provenance-bearing topic fact or explicit syllabus coverage state). Do not create a duplicate question table, a second test engine, a parallel learner progress store, or a second concept taxonomy without documented proof it is necessary.

## 3. Phase sequence and exit criteria

### Phase 6.53 — Syllabus-backed subject/topic taxonomy

**Deliver:** Canonical subject → topic → subtopic catalogue for the first supported Rajasthan exam profiles, with stable IDs, labels, parent/child relationship, exam applicability and syllabus/source provenance. Map existing `ConceptRecord` rows and linked questions into it; report unmapped, ambiguous and orphaned records.

**Coverage to seed:** Rajasthan History, Geography, Polity/Administration, Art & Culture, Economy; Indian History, Geography and Polity where in the selected syllabus; General Science (Physics/Chemistry/Biology/Environment); Hindi; English; Maths; Reasoning; Computer and other explicitly supported syllabus sections.

**Rules:** Use official exam notifications/syllabi for exam applicability. A generic subject label is not proof that every exam tests that subject. Seed/upsert must be idempotent; IDs must be stable; translated/alternate labels may be search aliases but cannot create duplicate topics.

**Exit tests:** taxonomy parent/child and exam-profile validation; deterministic/idempotent seed tests; old concepts/questions remain readable; coverage report identifies unknown/unmapped items.

### Phase 6.54 — Topic-wise Previous Exam Question API

**Deliver:** An authenticated, paginated topic-content API/query that returns eligible historic questions for a selected canonical topic/subtopic, with exam/year/shift/source filters and topic-level counts.

**Eligibility:** Only historical appearances backed by the existing official-paper and matched official answer-key gates enter the verified-history section. Use existing `exam_appearances`, `appearance_sources`, verification and resolved-answer records. Preserve question identity vs. repeated real exam appearances, and deduplicate copied text without erasing distinct exam appearances. Never infer a repeat count from how many websites copied the question.

**Exit tests:** correct topic and subtopic filtering; multiple exam appearances retained with one canonical question identity; source URLs and answer-key status preserved; pagination bounded; learner/auth scope enforced; unverified, secondary-source-only, malformed and unresolved-answer records do not appear as verified historic questions.

### Phase 6.55 — Source-backed Important One-Liner Bank

**Deliver:** Short facts, definitions, rules, dates and formulas mapped to topics/subtopics and tagged with importance, language, source, verification state and last-checked date where relevant. Reuse the repository's existing fact/material extraction models where fit; introduce separate persisted records only where a reusable, source-cited topic-fact store does not exist.

**Trust rules:** Every factual one-liner needs traceable supporting source evidence. For Rajasthan exam facts, prioritize relevant official government/department publications and the official syllabus; use authoritative textbooks/standard references only under the configured source policy. Current/volatile facts (office holders, budgets, rankings, laws/rules) need an as-of date and refresh policy. AI may summarize or propose facts but cannot self-certify them as verified. Keep disputed/out-of-date facts out of the verified set and send them for review.

**Exit tests:** source citation required for verified status; duplicate/near-duplicate fact checks; topic mapping; dates and formulas rendered faithfully; Hindi/English text preserved; unverified content visibly separated; no fact can be promoted solely because a model generated it.

### Phase 6.56 — Mobile Subject → Topic → Study page

**Deliver:** A question-bank entry point in the Flutter dashboard. Navigation: exam profile → subjects → expandable topic/subtopic list → topic page. Each topic page offers Previous Exam Questions, Important One-Liners, Practice and Topic Test/Revision. Provide loading, empty, unavailable and partially populated states.

**Exit tests:** Flutter analyze and widget tests; tap-through navigation and filters; long lists are paginated; question source/exam metadata are visible; empty pool says no verified items are available yet instead of fabricating data; old login, dashboard, timed session, resume and results flows remain intact.

### Phase 6.57 — Syllabus coverage, mastery and revision

**Deliver:** Track study progress by topic and subtopic using the existing learner-session/results/analytics model. Show not started / studying / revision needed / covered states based on explicit criteria, not merely on visiting a screen. Give revision priority to weak topics and past mistakes using existing adaptive services.

**Exit tests:** coverage progress persists for the authenticated learner; only submitted-test outcomes affect mastery; browsing one-liners does not falsely mark MCQs mastered; weak-topic recommendations map back to the canonical topic; learner data remains isolated.

### Phase 6.58 — Real-data completion and end-to-end proof

**Deliver:** Demonstrate the complete chain for a selected first exam profile: official syllabus → seeded topic map → accessible official paper → extracted questions → matched/verified official answer key → topic-linked verified historical question → source-linked one-liner → visible mobile topic page → topic test → saved result/weak-topic revision.

**Critical prerequisite:** The 20 October 2026 operational checkpoint reports that no registered official source currently passes both TCP and certificate-validated TLS from the research runtime. RSSB/RPSC endpoints time out; the legacy RSSB host fails verified TLS. Restore an approved official HTTPS path or authorized runtime/network configuration. Do not weaken TLS, bypass robots/terms/host policies or manufacture questions to inflate counts.

**Exit tests:** nonzero real source-backed counts from the live readiness/content endpoints; inspect source and answer-key URLs; end-to-end tests run against real persisted records; verify no fake history or fabricated readiness; capture a mobile test-flow result. A CI run with zero selected papers is not success evidence.

## 4. Completion definition

A topic is shown as **covered** only when:
- its selected exam profile has an authoritative syllabus/topic checklist;
- every required subtopic has an explicit coverage state;
- the verified previous-question count and accepted one-liner count are shown separately;
- unresolved sources, missing papers or unverified facts remain visible;
- the learner has completed the defined revision checks if learner mastery is also shown.

“Complete preparation” is a coverage goal, not a claim that a finite database contains every question ever asked. The app should tell the learner exactly what is verified, what is still missing, and when a source was last checked.

## 5. Cross-cutting quality and safety gates

- Keep historical exam questions, generated practice questions and study facts as different content types with explicit source/provenance.
- No answer-key guess is marked official/verified. Preserve correct answers from the paired, verified key.
- Keep all data access bounded, paginated and authenticated, with learner identity bound to the verified Firebase UID on protected learner routes.
- Use deterministic fixtures in CI; live AI providers must not be required for unit tests.
- Add migration up/down or migration-chain checks as required by project conventions, API contract tests, repository integration tests and Flutter tests for every completed phase.
- Maintain the master checkpoint with branch/commit, tests run, CI evidence, live-data caveats and the next exact phase. Do not restart completed Phases 1–6.52.

## 6. Immediate implementation order

1. Close or explicitly work around the approved official HTTPS reachability blocker without weakening security, and verify current database migration/readiness state.
2. Implement Phase 6.53 taxonomy and a coverage audit report.
3. Implement Phase 6.54 historic topic question reads.
4. Implement Phase 6.55 verified one-liners.
5. Add the Flutter browsing journey in Phase 6.56.
6. Add progress/coverage integration in Phase 6.57.
7. Complete Phase 6.58 real-data end-to-end validation.

This document records the plan and constraints; it does not claim phases 6.53–6.58 or nationwide topic coverage have already been implemented.
