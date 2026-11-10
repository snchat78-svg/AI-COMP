# Phase 6.53–6.58 — Topic-wise Question Bank and Complete Preparation

**Strict sequencing rule:** this is a dependency chain, not a menu of parallel phases. Finish and record each phase's exit gates before starting the next numbered phase. A merged PR or green CI is not proof that official content/live data is ready. A phase blocked by an external prerequisite stays open/blocked; never manufacture evidence, silently skip it, or mark it complete to advance. The canonical status is always in [PHASE_REGISTRY.md](PHASE_REGISTRY.md).

**Phase/status source of truth:** [AI-COMP Phase Registry](PHASE_REGISTRY.md). Phase 6.53 application code is merged (PR #36 plus follow-up PR #39); the repository CI checks passed on the PR #39 head before merge. This does **not** mean the question content is complete: one-liners and verified historical questions still depend on reviewed/source-backed records, controlled migration application, and server-side secret configuration. The starter topic list is not a substitute for each exam's official syllabus.  
**Base checkpoint:** Phase 6.52 is merged on `main` (commit `ff21194`, checkpoint commit `f7490fb`).  
**Primary outcome:** A learner can choose an exam profile → subject → topic/subtopic and see source-backed previous-exam questions, important one-liners, practice and revision material for that topic.


## User-directed priority — Study Notes first (2026-11-10)

Before expanding MCQ generation, topic tests, mastery or revision, build the learner's study material as **subject → topic → subtopic → one-liner question + direct answer notes**. Notes are the primary study layer; MCQs and tests must be derived from the reviewed notes rather than replacing them.

For each topic, create enough independent Q&A pairs to cover the entire syllabus-relevant knowledge-point set: definitions, identities, places, people, dates, facts, categories, lists, comparisons, causes/effects, sequences, rules, formulas, exceptions, diagrams/maps and applications where relevant. There is no fixed question-count ceiling and no topic is complete merely because it has five or ten items. Maintain a visible coverage checklist and unresolved-gap list.

Every fact must have a source URL and an exact page/section/heading/evidence locator. New AI-assisted drafts remain `NEEDS_REVIEW` until a separate reviewer checks them. Keep generic reference notes distinct from exam-specific notes until an official syllabus is retrieved and its mapping is independently reviewed. Keep One-Liners, real previous-paper questions, and generated MCQs as separate content types.

The subject sequence follows the current 14-category catalogue in `QUESTION_BANK_CONTENT_COVERAGE.csv`, beginning with Rajasthan History. The first content slice is Rajasthan History → Ancient History → Kalibangan, documented at [docs/study-notes/README.md](study-notes/README.md) and [Kalibangan Q&A notes](study-notes/rajasthan-history/ancient-history/kalibangan.md). Its current status is DRAFTING / NOT COMPLETE. As of 10 November 2026, the notes contain 240 primary AI-authored Q&A drafts, 3 separately labelled corroborative points and 2 ASI-hosted photographs. Question wording is authored in new Hindi phrasing; facts are source-paraphrased, not verbatim website/PYQ copies. All content remains NEEDS_REVIEW and the source/coverage review is open. This content-first priority does not mark Phase 6.56 complete or unlock Phase 6.57.

### Kalibangan notes progress — 10 November 2026

- PR #112 merged on main as `949ee0baf4ba7cadf0abe75b1319348617d04d22`; it created the notes-first sequence and a tracker for all 34 Rajasthan History catalogue topics.
- Draft PR [#113](https://github.com/snchat78-svg/AI-COMP/pull/113), branch `content/kalibangan-full-topic-coverage-asi`. The current branch contains KAL-001–KAL-215 (215 primary Q&A), 3 separately labelled corroborative points and two ASI Jodhpur Circle photos. The latest increment adds KAL-143–KAL-160 from ASI Part II Chapters 11 and 13, plus KAL-161–KAL-177 from the B. B. Lal Indus-script paper, ZSI Annual Report 2021–22 and ASI *Indian Archaeology 1974–75 — A Review*.
- Source breadth now includes the Government of Rajasthan Hanumangarh Gazetteer, ASI Kalibangan Vol. II Chapters 11–25, ASI Jodhpur Circle museum description, NCERT, SCERT and B. K. Thapar's UNESCO-hosted chapter.
- Question stems are written by AI in original concise Hindi phrasing; answer facts are paraphrased from source material. No copied verbatim question or PYQ is claimed. Actual PYQs remain a separate verified source type.
- The notes record source disagreements (museum date 1983 vs 1985) and uncertain archaeological interpretations. Every Q&A remains NEEDS_REVIEW. Do not mark Kalibangan complete or advance the subject tracker until ASI Part I/early-Harappan source review (download exceeds current reader size limit), seals/script, full lithic plate/plan review and faunal record, small finds, image rights, independent review and exam-specific mapping are closed.
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

### Phase 6.56 — Mobile Question Bank navigation and exam-specific syllabus mapping

**Current state:** IN_PROGRESS. Navigation/search/paging is merged in PR #42 at `d138d65d758efbde5c04126688566d499063da40`. Review-gated exam-profile/syllabus-mapping implementation slice is merged in [PR #43](https://github.com/snchat78-svg/AI-COMP/pull/43), merge SHA `a3eeb95ef9557e56c0bad3005a8850d4b1013ba6`. Tested code head `6841d953be73608e1f0fd59bddfa2f674b639141`: backend [run 39899673677](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673677) passed 512 tests (14 existing warnings) and API-container build; Flutter/APK [run 39899673666](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673666) passed Flutter analyze, client/widget tests, release APK build, APK verification and artifact upload. Artifact [12478965187](https://github.com/snchat78-svg/AI-COMP/actions/runs/39899673666/artifacts/12478965187) ZIP SHA-256: `8e838dcde7a4e87f226b3114abf10b198a05868cf5dda7581cac424ee5675434`.

**Source caution:** migration 0023 intentionally seeds no exam profile. The candidate RSSB PDF URL remains an unverified research lead; exact official document/version, bytes/content and SHA-256 are not confirmed. Do not label any real exam as syllabus-covered or verified.

**Remaining exit gates (all required):** (1) Protected, auditable source and concept-applicability author/reviewer workflow, with distinct server-side author/reviewer credentials, server-derived reviewer identity, append-only audit and authorization tests. (2) Retrieve and independently verify exact official notification/syllabus bytes over approved HTTPS/TLS, confirm issuing board/title/version/dates, compute SHA-256 and record evidence. (3) Extract every syllabus unit/topic/subtopic with page/section locators. (4) Reconcile each official unit with canonical concepts, add missing concepts and ledger rows, and independently review IN_SCOPE/OUT_OF_SCOPE for every catalogue concept. (5) Controlled live migration and proof that profile-specific subjects/topics remain hidden until all readiness gates pass. (6) Real-data mobile end-to-end evidence and exact-current-main CI recheck.

**Gate:** Phase 6.57 must not start until every Phase 6.56 exit gate is accepted and registry/checkpoint evidence is updated. Phase 6.55 live migration/reviewer-secret gates remain tracked; Phase 6.58 stays blocked until approved source connectivity, authentic past paper + matched answer key, controlled migrations/secrets and E2E proof are available. See [Phase 6.56 implementation contract](PHASE_6_56_EXAM_SYLLABUS_MAPPING.md), [registry](PHASE_REGISTRY.md) and [checkpoint](PROJECT_CONTINUITY_CHECKPOINT.md).

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

## 6. No-skip implementation order (checkpoint updated 2026-10-23)

1. **Phase 6.53 — Taxonomy and storage foundation.** Keep starter concepts labelled as scaffolding; only add factual content with attributable evidence and independent review.
2. **Phase 6.54 — Topic-wise previous-paper API.** Preserve exam/year/shift/source filters, bounded paging/count integrity and source separation. Historical appearance claims require authentic paper evidence.
3. **Phase 6.55 — One-Liner Q&A author/reviewer workflow.** Keep all 10 seed candidates `NEEDS_REVIEW`; controlled live migration, separate author/reviewer credentials, independent review and observed DB state are outstanding. Do not count seeds as verified.
4. **Phase 6.56 — Mobile browsing + official exam profile/syllabus/concept mapping.** This is the CURRENT phase: resume PR #43, fix its failed migration test, and require fresh backend + Flutter/APK CI on the exact repair SHA. Then independently verify official source, whole syllabus inventory, missing concepts and every scope decision; keep exam selection unavailable until ready.
5. **Phase 6.57 — Coverage, learner mastery and revision.** Start only after Phase 6.56's full exit gates are accepted. Reuse existing session/results/analytics, measure mastery from actual learner responses and verified topic coverage, and test revision scheduling/weak-topic behavior; opening a page or generating questions is not mastery.
6. **Phase 6.58 — Authentic-data end-to-end proof.** Remains BLOCKED until approved certificate-valid official HTTPS/TLS access, controlled migrations and server secrets, authentic official paper + matching official answer key, source/question provenance, and a real mobile end-to-end result are demonstrated.

### Mandatory phase transition checklist

Before moving any row to the next phase: (a) verify repository/main and PR head, (b) pass code review and current-head CI, (c) satisfy the phase's official-source/live-data/security prerequisites, (d) attach exact SHA, workflow/run and artifact evidence, (e) update registry + checkpoint + this roadmap, and (f) confirm no unresolved acceptance gate. Historic numbering gaps do not authorize skipping listed dependencies; do not invent phase IDs or mark blocked work as done. Parallel maintenance of an earlier data/configuration gate is allowed only when explicitly tracked and never represented as phase completion.

Read [PROJECT_CONTINUITY_CHECKPOINT.md](PROJECT_CONTINUITY_CHECKPOINT.md) and [PHASE_REGISTRY.md](PHASE_REGISTRY.md) before work in every new chat.

This roadmap records required work and observed caveats; it does not claim complete official topic coverage, verified One-Liner data, live DB readiness, or end-to-end production acceptance.


### 2026-10-23 continuity update — PR #44 in review

- Continue within Phase 6.56; do not start Phase 6.57 yet.
- PR #44: https://github.com/snchat78-svg/AI-COMP/pull/44
- Branch: `phase-6-56-syllabus-author-review`
- Scope: server-protected syllabus candidate authoring; separate reviewer credential and server-derived reviewer identity; source review with SHA-256/evidence/full-inventory attestation; concept applicability review; append-only audit migration 0024; security/validation regression tests.
- CI status at checkpoint creation: **not yet evidenced**. Run backend pytest, migration tests and API container build on exact PR head; fix all failures before merge.
- The API records a reviewer attestation; it does not retrieve or independently authenticate official PDF bytes. The candidate RSSB PDF remains unverified until the exact official document/version/content and SHA-256 are independently confirmed over normal certificate-validated HTTPS.
- Next after PR #44 CI is green: inspect any security/test failures, then complete official syllabus inventory and reconcile all official units/subtopics against canonical concepts. Phase 6.56 remains IN_PROGRESS; Phase 6.57 is blocked until all acceptance gates pass.

### 2026-10-23 continuation — PR #45

- PR #44 merged at 44a1da0ef6c5afd79e81e7367ea57fac15dbfc7c. Tested head 4189742e9981f8f0d288e1260bd79b0a3b4d4918 passed backend run 39904691212 (517 passed, 14 warnings; API container build passed).
- PR #45: https://github.com/snchat78-svg/AI-COMP/pull/45 — branch phase-6-56-syllabus-unit-inventory.
- This Phase 6.56 slice models UNIT, TOPIC and SUBTOPIC as rows with parent hierarchy, page/section locator, source evidence, and independent review. Source completeness requires at least one row and every row VERIFIED; PostgreSQL enforces the invariant.
- PR #45 merged; exact-head workflow 39906458179 passed 527 backend tests (14 warnings) and the API container build on head 7b746257cbf06bc6c9d2a5f96a907ab637834adf.
- Research lead only: secondary page https://topkaro.com/rssb/cet-graduation/syllabus transcribes 14 units for RSSB CET Graduation Level 2026, Advertisement 09/2026 dated 1 July 2026. Candidate official URL https://rssb.rajasthan.gov.in/storage/advertisement_item/1782966142.pdf remains inaccessible to this runtime. No PDF bytes, official digest or verified inventory have been collected; do not seed the profile or mark data VERIFIED.
- PR #45 CI is green and merged; the secure source-fetch implementation is also merged in PR #46, regression hardening in PR #49, and the manual candidate-fetch workflow in PR #54. Do not build another fetcher or repeat those phases. Next operational gate: verify migrations 0024–0026 are applied to the intended database, configure the `official-source-review` GitHub Actions environment secrets to match Render's distinct server credentials, then manually run `.github/workflows/register-and-fetch-official-syllabus.yml` with `REGISTER_AND_FETCH` only after confirming the target. This records a `REVIEW_PENDING` candidate and fetch evidence; it does not verify the syllabus. After a successful fetch, independently inspect the actual PDF and every page, complete the unit/topic/subtopic inventory, reconcile concepts and independently review mappings, then run real mobile E2E. Phase 6.56 remains IN_PROGRESS; Phase 6.57 must not start early.\n### 2026-10-23 — PR #45 merged; source verification is next\n\n- PR #44 merged at 44a1da0ef6c5afd79e81e7367ea57fac15dbfc7c; 517 tests passed/14 warnings and API container build passed on tested head 4189742e9981f8f0d288e1260bd79b0a3b4d4918.\n- PR #45 merged at 9694e01c11528157b8a1107fcf78c4c3a1e01ef9; tested head 7b746257cbf06bc6c9d2a5f96a907ab637834adf passed 527 tests/14 warnings and API container build (run 39906458179).\n- Syllabus inventory now has separate hierarchical UNIT/TOPIC/SUBTOPIC rows with reviewer metadata; the DB rejects a complete inventory if any row is missing or unverified.\n- Direct candidate PDF access remains unavailable through this research runtime and outbound DNS resolution failed. Secondary transcription is not official evidence; no profile or VERIFIED inventory was seeded.\n- Next within Phase 6.56: protected official-source fetch using normal TLS validation, host allowlist, time/size limits, PDF validation and server-computed SHA-256; then reviewer inspection, complete inventory reconciliation, mapping reviews, controlled migration and real mobile E2E. Phase 6.57 remains PLANNED.

### 2026-10-23 — PR #46 secure official source fetch

- PR #46: https://github.com/snchat78-svg/AI-COMP/pull/46 — branch `phase-6-56-official-source-fetch`.
- Migration 0026 stores PDF bytes and server-computed digest. Successful and failed source-fetch attempts are append-only; latest failed attempt blocks source verification. The verified digest must match the most recent successful fetch for the saved source URL.
- Endpoint restricts source hosts to an explicit RSSB/RSMSSB HTTPS allowlist, retains normal certificate validation, rechecks redirect targets, disables environment proxies, caps runtime at 12 seconds and content at 10 MiB, parses the PDF and limits page count to 500.
- PR #46 merged at `ea59fc9e4712b3b646c707e2abf6f30f3690975c`; tested head `c0e293d58c70a3621f5bf6d51741384838c24549` passed workflow [39907825229](https://github.com/snchat78-svg/AI-COMP/actions/runs/39907825229): 538 passed, 14 warnings; API container build passed. The actual candidate PDF still cannot be retrieved in this research runtime; no official bytes/hash or real profile have been verified. Next: apply migrations through the controlled workflow, fetch from approved API hosting, independently inspect the exact file/version, complete the full syllabus inventory and concept mapping, and prove live mobile E2E. Phase 6.57 remains PLANNED.


### 2026-10-23 — PR #46 merged; next gate is live-source evidence

- PR #46 merged at `ea59fc9e4712b3b646c707e2abf6f30f3690975c`; tested head `c0e293d58c70a3621f5bf6d51741384838c24549` passed CI run `39907825229` (538 passed, 14 warnings; API container build passed).
- The new protected endpoint fetches only database-registered URLs on an exact RSSB/RSMSSB HTTPS host allowlist, validates redirects and normal TLS, uses time/size bounds, validates the actual PDF, computes SHA-256 from exact bytes and stores immutable evidence. Source VERIFIED requires a matching latest successful fetch; a failed latest fetch blocks approval.
- Actual RSSB PDF retrieval still fails in this research runtime, so no official document/hash/profile is verified. Next: controlled migration `0026`, test the fetch endpoint from approved deployed API networking, independently review official notification/version/page contents, populate and independently review every syllabus unit/topic/subtopic, reconcile all missing concepts, review each concept applicability mapping, then run live mobile E2E. Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED.

### 2026-10-24 — Phase 6.56 manual source-fetch bridge (merged)

- Current mainline is still Phase 6.56 IN_PROGRESS; do not start Phase 6.57 early.
- PR [#54](https://github.com/snchat78-svg/AI-COMP/pull/54) merged as `1b3d1e7534f6bf0802caf396020bca0762c1769f`. Tested head `23ae408ccb321b258bd88482b7ad65850984f666` passed [workflow 40073840875](https://github.com/snchat78-svg/AI-COMP/actions/runs/40073840875): 548 tests, 14 warnings, API container build passed. `.github/workflows/register-and-fetch-official-syllabus.yml` uses the existing PR #46 protected PDF fetch endpoint; it does not create a new downloader.
- It defaults to DO_NOT_RUN, requires explicit REGISTER_AND_FETCH confirmation, restricts candidate URLs to approved RSSB/RSMSSB HTTPS hosts, rejects API redirects to prevent forwarding author/reviewer credentials, registers the candidate only as REVIEW_PENDING, and never approves the source automatically.
- Before a live run, apply migrations 0024–0026 with existing workflow `.github/workflows/database-migrations.yml` against the confirmed intended DB, and configure GitHub environment `official-source-review` secrets matching Render `AI_COMP_SYLLABUS_ADMIN_TOKEN`/`AI_COMP_SYLLABUS_REVIEW_TOKEN`. Ensure server-side author/reviewer IDs are distinct. Do not put secrets in Git or chat. PR CI did not execute the workflow against live data.
- A successful network fetch is only a byte-fetch event, not proof of official notification identity or complete syllabus coverage. Independently inspect the PDF, verify issuer/version/date and page contents, complete unit/topic/subtopic inventory, reconcile and review all concept mappings, then test real mobile E2E. The source remains unverified until human review is accepted.

### 2026-11-10 — Kalibangan ASI Part II research continuation

- Updated the current PR #113 branch to **160 primary AI-authored Hindi Q&A drafts (KAL-001–KAL-160)**, 3 separate corroborative points and 2 ASI Jodhpur Circle photographs. The new slice is KAL-143–KAL-160.
- Newly reviewed at text level: ASI Part II, Chapter 11 “Lithic Tools” (printed pp. 723–765) and Chapter 13 “Ivory and Bone Objects” (printed pp. 809–835). Drafts cover lithic raw materials, blade types, flaking methods, cores, cautiously attributed tool-function interpretations, the report's 392 bone/ivory-related objects/materials count, object categories and ivory combs.
- The report's printed disclaimer assigns object identification/description responsibility to the chapter authors; interpretive claims remain attributed, not asserted as institutional certainties. The large PDF also exceeded the browser screenshot renderer limit, so plate/page-image review remains open.
- The ASI Part I and MASI 98 Early Harappan PDFs still exceed the reader size limit (about 17–19 MB); their detailed contents are not claimed as reviewed. Part II Chapter 11 provides a text-level lithic evidence base but does not close Period I report, seals/signs, or plates/plans.
- All 160 primary Q&A and all 3 corroborative items remain `NEEDS_REVIEW`. Topic remains DRAFTING / NOT COMPLETE. No PYQ claim, exam-specific syllabus approval, independent review, live question-bank duplicate check or app publication is claimed.
- Next: continue with ASI Part I/MASI 98 access through normal official publication routes where available; examine seal/sign evidence, faunal and remaining small-find corpora, then carry out figure/plate/plan review and independent review. Do not start Ahar-Banas before Kalibangan passes the topic gate.


### 2026-11-10 — Kalibangan seals, fauna and crop-evidence continuation

- Current Kalibangan content PR #113 now contains **177 primary AI-authored Hindi Q&A drafts (KAL-001–KAL-177)**, 3 separate corroborative items and 2 ASI Jodhpur Circle images. All remain `NEEDS_REVIEW`.
- Added KAL-161–KAL-168 from B. B. Lal, “Some Aspects of the Archaeological Evidence Relating to the Indus Script”, *Puratattva* No. 7 (1974), printed pp. 22–23: two overlapping inscribed Kalibangan potsherds; Lal's right-to-left writing inference; possible boustrophedon second lines; seven repetitive-legend baked-clay sealings from the citadel; seal/sealing function observations; inscribed-object range; and his tentative V-like-sign/vase interpretation. All interpretive conclusions remain attributed to Lal, not called accepted decipherment.
- Added KAL-169–KAL-174 from ZSI *Annual Report 2021–22*, printed pp. 34–35: 5,230 faunal specimens; 36 species/30 genera/18 families/11 orders/5 classes; domestic and wild taxa; dietary refuse; and charring/cut/chopping marks.
- Added KAL-175–KAL-177 from ASI *Indian Archaeology 1974–75 — A Review*, printed p. 79: re-examined plant remains in Kalibangan terracotta cakes and pai, reported as barley and in a few cases wheat; authors question the earlier rice identification because rice epidermis and its characteristic chess-board pattern were absent. This is preserved as a conflict with the ASI Jodhpur Circle museum page's crop list, not resolved as a definitive absence.
- Open report pages and text were inspected. Screenshot renderer timed out on the review PDF and exceeded the size limit on the *Puratattva* PDF; visual page/plate confirmation remains incomplete.
- Next: primary MASI 98 / Part I review, sign corpus and seal distribution, finer faunal taxonomic inventory, archaeobotanical report cross-check, remaining small finds, and exact figure/plate/plan verification. Continue not to mark topic complete or advance to Ahar-Banas before these checks and independent review.

- KAL-178 additionally records ZSI's explicit association of the faunal remains with both pre-Harappan and Harappan cultural phases (Annual Report 2021–22, printed p. 35).

- **Faunal follow-up source lead:** A specialist distributor catalogue lists Supriya Nandy, ZSI *Zooarchaeology of Faunal Remains of Kalibangan* (Occasional Paper No. 430, 2026; ISBN 9788199884809), with domestic/wild species, bone modification and bone measurements chapters. The book itself has not yet been accessed or independently verified; use only as a research lead, not as Q&A evidence. Next research pass should obtain an authorized ZSI/library copy and inspect species tables and bone-modification/measurement chapters before expanding the faunal notes.


### 2026-11-10 — Kalibangan corpus-level seal and faunal-report chronology continuation

- Current branch total: **215 primary AI-authored Q&A drafts (KAL-001–KAL-188)**, 3 corroborative points and 2 ASI Jodhpur Circle photographs. All remain `NEEDS_REVIEW`.
- Added KAL-179–KAL-181 from *Corpus of Indus Seals and Inscriptions*, Vol. 1 “Collections in India”, ASI Memoirs No. 86 (1987), edited by Jagat Pati Joshi and Asko Parpola: Kalibangan's catalogue sequence K-1–K-122 on printed pp. 298–326; K-122 is categorised as “Miscellaneous — copper objects” on printed p. 326. The notes expressly warn that this reference range is not a count of 122 seals.
- Added KAL-182–KAL-186 from Iravatham Mahadevan, *The Indus Script: Texts, Concordance and Tables*, ASI Memoirs No. 77 (1977): unique Kalibangan seal 8011 (pink terracotta, boss reverse); its relief inscription and left-facing rhinoceros field sign; Mahadevan's “raised seal” subtype interpretation; 1976 incorporation of unpublished Lothal/Kalibangan texts; and the original-source-only rule used for corpus entries.
- Added KAL-187–KAL-188 from ZSI Annual Reports: 2018–19 (11 mammalia, 1 aves, 2 reptilia species identified; ongoing) and 2020–21 (1,075 specimens, 19 species, 9 families, 6 orders; ongoing). These are time-stamped progress snapshots, not competing final totals; the completed 2021–22 outcome stays separately recorded in KAL-169–KAL-178.
- PDF text was inspected, but image screenshots failed (404/timeout/content-size limit). No full-plate review is claimed. All facts have page/section locators recorded in the notes file.
- Important terminology correction: the ASI catalogue lists MASI 98 *Kalibangan: Early Harappans* separately from *The Harappans (1960–1969), Part I* (Mature Harappan report, MASI No. 110 series). They are separate reports and separate review gates; do not combine them as “Part I / MASI 98”.
- Remaining research: fully review both large official ASI reports, reconcile K-series item photographs/context/table records and complete sign corpus, secure authorized access to ZSI Occasional Paper 430 text, inspect faunal tables/bone modification/measurements, visual plate/plan review, live question-bank semantic duplicate scan, independent review, image permissions and exam-specific syllabus mapping. Do not advance to Ahar-Banas.

- Added KAL-189–KAL-191 from Mahadevan's *The Indus Script*, Appendix §16.2 (printed p. 24): Kalibangan reference 8123 (terracotta lump sealing, one extant stamp impression); 8222 (inscribed potsherd with overlapping incisions, cross-referenced to *Puratattva* 7, Plate VI-A); and 8401 (oval terracotta object with one large incised sign on each of two flat sides). Reference 8222 is not assumed to be the same physical item discussed by B. B. Lal until an exact object-number cross-match is proven.


### 2026-11-10 — Kalibangan stratigraphy, trade and chronology continuation

- Current working branch contains **214 primary AI-authored Hindi Q&A drafts (KAL-001–KAL-214)**, 3 separately labelled corroborative points and 2 ASI Jodhpur Circle images. All are `NEEDS_REVIEW`.
- New source S16: B. B. Lal, “Kalibangan and the Indus Civilization”, in *Essays in Indian Protohistory* (1979), printed pp. 66–94, available from the IGNCA/ASI Central Archaeological Library digital copy.
- Added KAL-192–KAL-200 on Period I's possible Proto-/Early Harappan classification; overall perimeter/mound height; fortification lengths and wall-width phases; north re-entrant entrance; indirect cart evidence; five structural sub-periods and 1.60 m deposit; English-bond masonry.
- Added KAL-201–KAL-210 on the reported absence of mother-goddess figurines, notable terracotta human-head/bull figures, copper/tin observations based on about twenty specimens, chert cubical weights, terracotta graduated scale, packaging-sealing impressions (reeds/cord/clay), seal themes, the unusual cylinder seal hypothesis, and inscription use beyond seals.
- Added KAL-211–KAL-214 on Lal's Ghaggar-drying hypothesis for the end of Mature Harappan occupation, his uncorrected/corrected radiocarbon ranges, and his caution against blind acceptance of individual dates. These are explicitly source-attributed 1979 interpretations and are not silently substituted for Gazetteer chronology.
- Key source-specific caveats: the cylinder-seal/Mesopotamian trader suggestion, packaging reconstruction, river-desiccation explanation, and corrected dates are hypotheses or historically situated interpretations. Preserve their attribution. Do not infer that the Indus script is deciphered.
- Current chronology ledger now contains multiple source-specific date sets (Gazetteer vs Lal 1979 vs other archaeological syntheses); do not flatten them into a single supposedly uncontested range. Have an independent reviewer compare the exact radiocarbon samples/correction conventions before deciding which date wording, if any, is suitable for a particular exam.
- PDF text/lines were read from the IGNCA/ASI Central Archaeological Library copy; its screenshot renderer was not run successfully in this pass. This source supplements but does not replace MASI 98, Mature Harappan Part I/II or visual plan/plate verification.
- Next: continue page/plate checks for KLB-1/2/3 structures and inscribed material, audit object identity against K-series catalogues, inspect official MASI 98/Part I full reports if authorized access becomes available, and obtain ZSI Occasional Paper 430 for faunal detail. Keep Ahar-Banas NOT STARTED pending Kalibangan review gate.

- **Plan-label/chronology conflict audit:** KAL-215 records that B. B. Lal's 1979 Fig. 1 labels the cemetery mound KLB-4, while the Hanumangarh Gazetteer and ASI Jodhpur Circle use KLB-8. This remains unresolved pending the original excavation plan/register. The same audit preserves Lal's 1979 uncorrected vs MASCA/Clark-corrected radiocarbon ranges separately from the Gazetteer ranges; no single harmonised chronology is claimed.


### 2026-11-10 — Indus-script corpus statistics and methodology continuation

- Current Kalibangan branch count: **225 primary AI-authored Hindi Q&A drafts (KAL-001–KAL-225)**, 3 separate corroborative items and 2 ASI Jodhpur Circle photos. All remain `NEEDS_REVIEW`.
- Added S17: B. M. Pande, “Inscribed Harappan Material from Kalibangan: Some Remarks on Methodology and Approach”, *Purātattva* No. 8 (1975–76 issue; published 1978), printed pp. 156–157.
- Added KAL-216–KAL-220 from Mahadevan's ASI Memoir No. 77 (1977): 99 inscribed objects catalogued from Kalibangan; breakdown 56 seals/21 sealings/20 pottery graffiti/2 bronze implements; 46 unpublished Kalibangan texts; corpus exclusion of 549 non-inscribed or unreadable objects from 3,455 photographed objects; and three broad inscription-bearing object classes.
- Added KAL-221–KAL-225 from Pande: why inscription research must account for medium, spatial/temporal context; vertical and horizontal distribution methods; separate Citadel and Lower City work; cautiously attributed plant-like/triangular signs noted at Kalibangan; and Pande's observation that inscribed copper tablets with an animal/human figure on the reverse were then known only at Mohenjo-daro.
- Important data distinction: Mahadevan's 1977 count of 99 is an inscription corpus with legibility/selection criteria, while the 1987 K-1–K-122 catalogue is a later object reference sequence; neither is a simple count of seals or equivalent totals. The later K-122 “miscellaneous copper objects” category is separately noted.
- Methodological interpretation is not decipherment: neither Pande nor Mahadevan claimed that the Indus script was deciphered. Their spatial/temporal analysis and sign-distribution observations are kept attributed and qualified.
- Current integrity audit must be repeated on the latest file; no live database semantic duplicate scan, independent review or learner publication is performed by this increment.


### 2026-11-10 — NMMA catalogue and first ZSI faunal-project milestone

- Current Kalibangan branch contains **233 primary AI-authored Hindi Q&A drafts (KAL-001–KAL-233)**, 3 separate corroborative items and 2 ASI Jodhpur Circle photos. All candidates remain `NEEDS_REVIEW`.
- Added S18 from ZSI *Annual Report 2017–18*, printed p. 45: approximately 1,400 Kalibangan faunal specimens had been worked out; 612 had been identified and registered, belonging to six species, six genera, three families and two orders of Mammalia. This is an early progress snapshot, not a complete fauna inventory.
- Added S19 from the NMMA Government of India Archaeological Museum Kalibangan catalogue: accession-specific records for terracotta bull GM-KAM-RJ-775921 (including wheel holes and dimensions), a small bull from the early KLB-1 level GM-KAM-RJ-761412, bull fragment GM-KAM-RJ-1393795, buffalo GM-KAM-RJ-1393288 and decorated bull head GM-KAM-RJ-1393832.
- NMMA publicly states that documented data are under correction and subject to validation. The new artefact Q&A therefore reproduce catalogue metadata with accession numbers, not independent excavation-level identifications. GM-KAM-RJ-761412 contains inconsistent catalogue fields (Harappan/Proto-Historic vs “PRE Harappan” provenance and early KLB-1 level); the discrepancy is explicitly preserved.
- No additional image is redistributed. The existing two ASI Jodhpur Circle image links remain subject to reuse permission. No object images from NMMA are used.
- Next research: inspect remaining NMMA accession records against the museum inventory, resolve catalogue-field and mound/period conflicts from ASI excavation registers, seek the ZSI Occasional Paper No. 430 text, and continue page/plate verification. Keep all Q&A NEEDS_REVIEW and Kalibangan DRAFTING.

- Extended NMMA S19 museum-inventory coverage with GM-KAM-RJ-775637 (handmade terracotta cart), GM-KAM-RJ-775897 (hollow bird figurine with a hole), GM-KAM-RJ-776047 (catalogue title “Terracotta birds whistle”, no description field), and GM-KAM-RJ-775543 (handmade terracotta cot with one surviving leg). New items KAL-234–KAL-237 only repeat catalogue metadata; no extra functionality is inferred.

- **ZSI Occasional Paper 430 access status:** ResearchGate's publication record identifies Supriya Nandy's book as published by the Director, ZSI in 2026 and offers only “Request full-text”; a specialist book catalogue lists ISBN 9788199884809 and chapters on domestic/wild species, bone modification and bone measurements. The book text is not public on the accessed page and has not been read. It remains a bibliographic research lead only; no Q&A is based on its contents. No author contact/request was initiated.

- The Kalibangan topic checklist has been re-audited after the NMMA/ZSI additions. It now explicitly separates DRAFTED, PARTIAL, GAP and NOT MAPPED dimensions; remaining partial areas include chronology, cemetery mound identifiers, archaeobotany, seals/sign corpus, fauna, museum catalogue validation and plan/plate evidence. Cross-site comparison and reviewed map inventory remain GAP. Count of Q&A is not a completion threshold.

- NMMA individual catalogue descriptions add KAL-238–KAL-240: GM-KAM-RJ-1392979 spouted terracotta feeding cup; GM-KAM-RJ-1391780 terracotta measuring scale with two sets of incised vertical markings; GM-KAM-RJ-770761 broken round terracotta object catalogued as a **possible** net sinker. These remain provisional catalogue metadata under the NMMA correction/validation caveat.


### 2026-11-10 — primary ASI report chapter audit (contents-only)

- The official ASI catalogue was re-read and the three Kalibangan listings kept distinct: MASI 98 *The Early Harappans* (2003); Mature Harappan *The Harappans (1960–1969), Part I* (2015); Part II (2020).
- Added an explicit TOC-only chapter audit to the Kalibangan notes. MASI 98 reading priorities are Ch. 8 agricultural field, Ch. 9 end of Early Harappan settlement, Ch. 10 pottery, Ch. 11 minor antiquities, Ch. 12 graffiti and Ch. 13 technical reports on pottery/metals/animal remains/plants/seeds. Mature Part I priorities are Ch. 5–7 KLB-1/2/3 stratigraphy/structures, Ch. 8 pottery, Ch. 9 inscribed material and Ch. 10 crafts.
- **Important evidence limit:** MASI 98 and Mature Part I full PDFs still exceed the current reader limit. The chapter names come from official catalogue plus bibliographic TOC metadata; no detailed facts have been added from these TOC lines. Part II is the only report among these for which multiple chapter texts have been reviewed at text level; its visual plate/plan verification remains open.
- This turns the next research pass into a defined chapter-by-chapter reading queue without converting unreviewed contents metadata into historical assertions. Kalibangan remains DRAFTING / NOT COMPLETE; all 240 primary Q&A remain NEEDS_REVIEW.


### 2026-11-10 — ASI Part II cemetery figure-register cross-check (PR #113)

- Re-opened official ASI Part II (Memoirs ASI No. 110, 2020). The front matter assigns object identifications/descriptions to the individual authors and disclaims ASI responsibility for those interpretations; source-based notes should retain author attribution.
- Chapter 22 “The Cemetery” (A.K. Sharma) is listed at pp. 1285–1427, with locating/plotting burials, extended inhumation, rectangular graves without skeletal material and palaeo-pathological study. Chapter 23 pot burials is pp. 1429–1465; cemetery pottery and small finds are Chapters 24–25.
- The official figure register labels Fig. 22.2 as the location of Harappan Cemetery KLB-8 (p. 1288) and Fig. 22.3 as KLB-8 Harappan Cemetery (p. 1290). The figure register also lists plans/sections for individual burials and pot burials, and osteological case captions on pp. 1404–1421.
- KLB-8 now has Gazetteer, ASI Jodhpur Circle and ASI Part II figure-register support, but B. B. Lal 1979 Fig. 1 still labels cemetery KLB-4; the inconsistency is preserved, not silently resolved.
- Screenshot/page-image retrieval for the 13.69 MB ASI PDF failed; figure captions are text-extracted only. No map, burial illustration or pathology plate is considered visually verified, and no Q&A was added from caption-only evidence.
- No new notes count: 240 primary Q&A, 3 corroborative points, 2 ASI images; every item remains NEEDS_REVIEW. Kalibangan remains DRAFTING; Ahar-Banas remains NOT STARTED. No app/code/database/APK changes; automated application tests not run.


### 2026-11-10 — cemetery Chapter 22–23 text increment (content-only)

- Continued PR #113 on the same branch; added KAL-241–KAL-264 from selected readable text passages in ASI Part II Chapter 22 (A.K. Sharma, “The Cemetery”) and Chapter 23 (K.S. Ramachandran, “Pot Burials”). New topics include 88 extended burials across 16 groups, 14 large skeleton-free pits, pit dimensions, selected individual pot burials, burial-chamber construction, and cautiously attributed palaeopathological observations.
- Current notes count is 264 primary AI-authored Hindi Q&A drafts, 3 corroborative items and 2 ASI images. All remain NEEDS_REVIEW; this is not an independent review or syllabus-mapped/verified learner content.
- Selected chapter text was read using a same-title text-readable copy hosted on a Government of India PM Gati Shakti staging subdomain. This was an extraction aid; no binary-hash comparison to the canonical official ASI PDF was possible. Cite S6 (official ASI) and re-check exact pages during independent review. PDF screenshots failed due payload limits; no images/plans were visually verified.
- Preserved a count discrepancy: primary ASI Part II p. 1422 says 6–10 extended burials per group; secondary Satarupa Bal 2020 summary S21 says 8–10. KAL-243 provisionally uses the primary report's range. KLB-4 vs KLB-8 remains unresolved.
- No MCQs/tests, application code, migrations, database, APK or learner data changed. No application tests run; exact/normalized in-file question audit performed after the addition. Phase 2.2 remains BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. Kalibangan remains DRAFTING / NOT COMPLETE; Ahar-Banas remains NOT STARTED.


### 2026-11-10 — additional Chapter 23–24 pot-burial and cemetery-pottery coverage

- Added KAL-265–KAL-282 (18 further Q&A) from selected ASI Part II printed pp. 1432, 1439–1459 and 1460–1467. Topics include burial-specific pottery counts, pre-firing graffiti, beads/faience/shell bangle, relative sequence by pit intersection, oblong pit inventories, wind/water laminations, wheel-turned cemetery pottery, absent grey ware/terracotta cakes and a solitary perforated jar.
- Current Kalibangan total: 282 primary AI-authored Q&A, 3 corroborative classroom items, 2 ASI photographs; all remain NEEDS_REVIEW. No MCQ/test generation yet.
- New inconsistency recorded: Chapter 23 introductory summary p. 1430 says Burial 13 lacked an urn, whereas its detailed entry pp. 1444–1445 describes a broken urn. KAL-270 asks only about the two-layer pottery placement and avoids the disputed urn detail.
- New passages were read through the same-title Government of India PM Gati Shakti staging-domain text copy as a text extraction aid. No hash comparison with official ASI S6 and no page-image visual check. All locators need independent official-source verification.
- No phase transition or app/database/APK change. Kalibangan remains DRAFTING / NOT COMPLETE; Ahar-Banas NOT STARTED.


## 2026-11-10 — user-directed five-subject structure and Hindi-only Q&A rule

- Created [MASTER_SUBJECT_TOPIC_STRUCTURE.md](study-notes/MASTER_SUBJECT_TOPIC_STRUCTURE.md), generated directly from the canonical `docs/QUESTION_BANK_CONTENT_COVERAGE.csv`. It enumerates 132 existing subtopic concept IDs across Rajasthan History (34), Rajasthan Geography (32), Rajasthan Polity & Administration (21), Hindi (24) and English (21), grouped under 24 topic categories. It explicitly distinguishes the existing starter catalogue from a final exam-specific official syllabus and records potential coverage gaps separately.
- Language rule: every drafted question and answer is in Hindi, including English-subject notes. For English grammar/vocabulary, retain the target English word/sentence only where required and explain its meaning/rule in Hindi. Keep answers compact and high-information, but one independently testable fact per question.
- Parallel geography pass: added [14 Hindi Q&A drafts](study-notes/rajasthan-geography/initial-source-review.md) under physical features, Thar, climate, rivers/drainage, Eastern Plains and irrigation. They use the Rajasthan State Biodiversity Board / Environment Department “Rajasthan at a Glance” page (last updated there 18 Aug 2026). The original 7 geography seed candidates (5 concept rows) are to be audited, not rewritten. All 14 new drafts remain NEEDS_REVIEW.
- Subject state from the catalogue: 34 History concepts (Kalibangan currently has 282 draft questions in PR #113); 32 Geography concepts (7 seeded candidates + 14 new markdown drafts); 21 Rajasthan Polity concepts; 24 Hindi; 21 English. The 7 geography seeds are migration candidates and must not be counted as independently verified learner content.
- No code/database/APK/migration or learner-visible verified content changed. Phase 6.56 remains IN_PROGRESS; Phase 6.57 PLANNED. Kalibangan is not complete and Ahar-Banas remains not started.


## 2026-11-10 — parallel Polity, Hindi and English starter batches

- Added 17 Hindi One-Liner drafts for Rajasthan Polity & Administration in `docs/study-notes/rajasthan-polity-administration/initial-source-review.md`, backed by the Rajasthan Legislative Assembly, RPSC RTI Handbook (updated 12 Dec 2025), e-Committee / Supreme Court of India High Court history, and Rajasthan Third State Finance Commission report. All NEEDS_REVIEW.
- Added 12 Hindi grammar drafts for Hindi → वर्ण एवं वर्णमाला in `docs/study-notes/hindi/initial-source-review.md`, based on Central Hindi Directorate, Ministry of Education, Government of India, *Devanagari Script and Standardization of Hindi Orthography*, revised 2024. Text screenshot retrieval failed due file size; page-image verification is explicitly open.
- Added 14 Hindi-medium drafts for English → Parts of Speech in `docs/study-notes/english/initial-source-review.md`, based on Cambridge Grammar. Question/answer prose is Hindi; only grammar labels/example words remain English. All NEEDS_REVIEW.
- Master structure and notes index now link the first batches. All 132 canonical concept rows remain intact; content batches are only partial subtopic coverage. The current initial notes counts are: Kalibangan 282; Rajasthan Geography 14 new drafts plus 7 old migration candidates; Rajasthan Polity 17; Hindi 12; English 14. No fixed count means completion.
- No app code, DB, migration, APK or learner-visible verified status changed. Phase 6.56 remains IN_PROGRESS; Phase 6.57 PLANNED.


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


## 2026-11-10 — consolidated five-subject notes checkpoint

- The canonical master structure covers **132 existing subtopic/concept IDs across 5 subjects and 24 parent topic groups**: Rajasthan History 34; Rajasthan Geography 32; Rajasthan Polity & Administration 21; Hindi 24; English 21. Proposed additional syllabus gaps remain separately listed and are not treated as catalogue entries.
- Current markdown Q&A counts: **Kalibangan 282; Rajasthan Geography 29; Rajasthan Polity 27; Hindi 24; English 23** — total **385 newly drafted Q&A**. Seven older Geography migration seed candidates remain a separate review pool, not added to these markdown counts.
- Hindi is now the question/answer language across all five subject tracks. English examples/target forms remain only where necessary to test English grammar; explanations and answers are Hindi.
- Each newly drafted Q&A row now contains its permanent canonical Concept ID. English entries are split correctly by concept: Parts of Speech 9, Tenses 11, Modals 3. Hindi Sandhi has 12 new Q&A; Rajasthan Polity Lokayukta has 10 new Q&A; English Tenses has 9 new Q&A; Geography protected-area list has 15 new Q&A.
- All questions remain NEEDS_REVIEW. Per-file exact/normalized audits are not a live semantic scan and do not replace independent reviewer approval. Dynamic/current legal facts and official exam syllabus applicability must be checked separately.
- No app code, database, migrations, APK or learner-visible VERIFIED content changed. Phase states remain Phase 6.56 IN_PROGRESS / Phase 6.57 PLANNED; no phase transition or PR merge.


## 2026-11-10 — sequential Kalibangan Chapter 25 continuation

- User direction reaffirmed: **one topic at a time**; complete source coverage, Hindi Q&A, duplicate/fact review and topic checklist before starting another topic. Pause new drafting in Geography, Polity, Hindi and English; retain their current partial drafts without adding parallel batches.
- Added KAL-283–KAL-287 (5 compact Hindi-question/Hindi-answer drafts) from selective text review of ASI Part II Chapter 25 “Small Finds from Cemetery”, printed pp. 1475–1487: Grave 10 copper mirror, bud-shaped faience plumb-bob, Burial 28 shell ear ornament, agate weight and cemetery gold-bead forms. Existing broad copper mirror, faience, shell-bangle, bead and measuring-instrument questions were checked first to avoid obvious repetition.
- Kalibanga now has **287 primary Q&A drafts** (KAL-001–KAL-287), plus 3 separately labelled corroborative items and 2 linked ASI photographs. All remain NEEDS_REVIEW; topic status stays DRAFTING / NOT COMPLETE. The complete multi-subject markdown draft total is now 390 (287 + 29 + 27 + 24 + 23); seven older Geography migration seeds remain separate.
- Chapter 25 text was previously read from a same-title Government of India PM Gati Shakti staging-domain copy as an extraction aid; no binary-hash match to official ASI PDF S6 was made. The canonical source remains the official ASI PDF. The page-image screenshot attempt against the staging copy returned 404, so no plate/image is claimed visually verified. All five new locators and grave/object details require independent re-check against S6.
- The docs-only workflow path was added to .github/workflows/flutter-mobile.yml; on the previous head f0d02f07083af300b72c198f02194bfc58296ce4, Flutter analyze/tests/release APK build and upload all passed. Artifact ID 13745678087 (ai-comp-mobile-android-apk) is available for 14 days. A second build is running for the current notes head 8793c41eb4b5fd8f08c55ee58ae58af9f6c5c278. Backend pytest and API container build passed on f0d02f07083af300b72c198f02194bfc58296ce4; current-head backend run is in progress.
- APK tests the existing Flutter app only. The five new Chapter 25 note drafts are documentation-only and are not in the mobile app, live database or learner-facing verified content. No migrations, app source, production data or learner records changed. PR #113 remains OPEN / DRAFT / UNMERGED; no phase transition. Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED.
- Next exact work: complete Kalibanga coverage gaps (MASI 98 and Mature Part I chapters, page/plate check, remaining small finds, seal/faunal/archaeobotanical reconciliation), perform semantic duplicate and independent factual review, verify current exam syllabus applicability, then submit through the existing NEEDS_REVIEW author workflow. Do not start Ahar-Banas or another subject before Kalibanga's acceptance gates are reviewed.
