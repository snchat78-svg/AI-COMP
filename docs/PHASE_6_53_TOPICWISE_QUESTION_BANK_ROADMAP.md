# Phase 6.53–6.58 — Topic-wise Question Bank and Complete Preparation

**Strict sequencing rule:** this is a dependency chain, not a menu of parallel phases. Finish and record each phase's exit gates before starting the next numbered phase. A merged PR or green CI is not proof that official content/live data is ready. A phase blocked by an external prerequisite stays open/blocked; never manufacture evidence, silently skip it, or mark it complete to advance. The canonical status is always in [PHASE_REGISTRY.md](PHASE_REGISTRY.md).

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
- Next after PR #45 CI is green: verify exact official source via approved HTTPS, extract all units/subtopics with page locators, reconcile the concept catalogue, independently review mappings, then perform controlled live migration and real mobile E2E. Phase 6.56 remains IN_PROGRESS; Phase 6.57 must not start early.\n### 2026-10-23 — PR #45 merged; source verification is next\n\n- PR #44 merged at 44a1da0ef6c5afd79e81e7367ea57fac15dbfc7c; 517 tests passed/14 warnings and API container build passed on tested head 4189742e9981f8f0d288e1260bd79b0a3b4d4918.\n- PR #45 merged at 9694e01c11528157b8a1107fcf78c4c3a1e01ef9; tested head 7b746257cbf06bc6c9d2a5f96a907ab637834adf passed 527 tests/14 warnings and API container build (run 39906458179).\n- Syllabus inventory now has separate hierarchical UNIT/TOPIC/SUBTOPIC rows with reviewer metadata; the DB rejects a complete inventory if any row is missing or unverified.\n- Direct candidate PDF access remains unavailable through this research runtime and outbound DNS resolution failed. Secondary transcription is not official evidence; no profile or VERIFIED inventory was seeded.\n- Next within Phase 6.56: protected official-source fetch using normal TLS validation, host allowlist, time/size limits, PDF validation and server-computed SHA-256; then reviewer inspection, complete inventory reconciliation, mapping reviews, controlled migration and real mobile E2E. Phase 6.57 remains PLANNED.

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