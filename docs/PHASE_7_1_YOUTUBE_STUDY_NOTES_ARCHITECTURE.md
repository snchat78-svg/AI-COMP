# Phase 7.1 — YouTube Study Notes Architecture Freeze

## Goal

Add a YouTube-linked study-notes capability inside the existing AI-COMP product without destabilizing its exam research, question identity/history, test sessions, scoring, authentication, adaptive preparation, or current database migration workflow.

This phase freezes the architecture and delivery boundaries before feature code. It does not claim that transcript extraction, visual analysis, AI generation, PDF export, or deployment already exists.

## Existing architecture verified

- Flutter Android client: `apps/mobile/`.
- Python 3.11+ package and FastAPI API: `src/ai_comp/`.
- Existing API app factory and route composition: `src/ai_comp/api/app.py`.
- PostgreSQL-backed persistence and explicit migration CLI already exist.
- Firebase Authentication is used by the mobile app; protected API routes must continue to fail closed without trusted identity wiring.
- Render Free deployment preparation exists in Phase 6.46, but the documentation explicitly does not claim that cloud resources are deployed.
- The project already has OCR-related optional dependencies (`Pillow`, `pytesseract`, `PyMuPDF`); avoid adding duplicate OCR pipelines without checking current implementations.
- Existing package dependencies include `google-genai`; this feature must not make a paid/credentialed model provider mandatory.

## Architecture decision

Use an asynchronous, bounded, transcript-first pipeline behind the existing FastAPI backend. Reuse the existing Flutter app, authenticated API conventions, PostgreSQL connection/migration pattern, and deployment configuration. Add isolated study-notes modules and routes; do not overload exam-question, paper-ingestion, scoring, or adaptive-learning services.

### Flow

1. Flutter submits a YouTube URL, requested note language (`hi`, `en`, or bilingual), and optional learner-provided screenshots/transcript.
2. API authenticates the learner, validates the URL/video ID, enforces duration/size/rate limits, and creates a job owned by that learner.
3. Transcript provider attempts to read captions only through a permitted and supported path. It records source language, timestamps, and retrieval limitations.
4. Visual evidence is handled separately: OCR/key-frame analysis is enabled only for learner-provided images/video or content the user is authorized to process through a permitted method. Do not bypass YouTube access controls, download restrictions, login/age gates, DRM, or private content.
5. A bounded chunking/normalization stage combines transcript segments and timestamped visual evidence.
6. A provider interface produces structured notes. Default no-key mode must work with deterministic, extractive notes and templates; an optional locally hosted open-source model can improve synthesis when available. Do not silently depend on a paid API or assume free cloud CPU can host a useful large model.
7. Persist job status, source provenance, notes, language, timestamps, and safe error codes in PostgreSQL; expose only records owned by the authenticated learner.
8. Flutter renders the notes and timestamps. PDF export is a separate bounded output operation.

## Free-first implementation choices

- **Transcript:** prefer accessible captions and user-supplied transcript. Public transcript extraction is not guaranteed for every video and must remain compliant with applicable platform terms and access controls.
- **Visual text:** reuse existing OCR dependencies after inspecting their current call sites. Start with user-supplied screenshots/key frames; automatic frame extraction from a YouTube URL is not a guaranteed baseline.
- **Notes:** deterministic structured notes, topic headings, key points, timestamps, and revision prompts must work without an external AI key. Optional model adapters may be added only behind an explicit provider interface.
- **Storage:** use the existing PostgreSQL DSN and migration CLI. No new database vendor is required for the first version.
- **Hosting:** target the existing Render Free readiness path. Jobs must be short, bounded, resumable by status, and return a clear retryable state if the service sleeps or restarts. Do not promise continuous background processing on a sleeping free instance.
- **PDF:** generate on demand from saved notes; avoid storing generated binary files unless existing storage policy supports it.

## MVP scope and explicit non-goals

### Included in the staged roadmap

- URL parsing and safe video-ID validation.
- Caption/transcript retrieval with explicit unavailable/disabled-caption errors.
- Hindi, English, and bilingual output contracts.
- Structured, timestamped transcript notes without a mandatory AI API.
- Learner-supplied visual evidence with OCR and evidence references.
- Optional visual/model provider interfaces for later, independently tested additions.
- Persisted job status and notes ownership.
- PDF export and Flutter UI after backend contracts stabilize.
- Unit, API, migration, security, and Flutter tests.

### Not promised in the first version

- Every YouTube video is processable.
- All visible content can be recovered from a URL alone.
- Perfect OCR of handwriting, equations, diagrams, or low-resolution frames.
- Unlimited video duration, unlimited requests, or always-on free hosting.
- AI-quality abstractive summaries without a model provider.
- Bypassing captions restrictions, private/age-gated access, or platform controls.

## Security and reliability requirements

- Accept HTTPS YouTube URLs only from an explicit allowlist of YouTube hostnames; reject arbitrary URLs, IP literals, local hosts, redirects to other hosts, and unsupported URL shapes.
- Never fetch an arbitrary user-provided URL. Resolve a validated video ID through a narrowly scoped provider.
- Require authenticated learner identity for create/read/delete operations.
- Enforce ownership in every database read and mutation.
- Bound transcript bytes, duration, chunk size, processing time, number of screenshots, image bytes, and per-user job creation.
- Do not log full transcripts, uploaded image bytes, access tokens, database URLs, or provider secrets.
- Return stable error codes for unavailable captions, unsupported URL, limits, transient provider failure, and processing failure.
- Keep schema changes in a new numbered migration and use the existing explicit migration CLI; never migrate at API startup.
- Preserve existing routes, response contracts, migrations, and exam behavior.

## Delivery phases

1. **7.1 Architecture freeze (this document):** repository/hosting review, boundaries, risks, and acceptance plan.
2. **7.2 Backend contracts and URL validation:** typed request/response models, safe URL parser, provider protocols, unit tests; no database writes yet.
3. **7.3 Transcript acquisition and normalization:** provider adapter, timestamped segment model, fixtures, failure-state tests.
4. **7.4 Notes builder:** deterministic bilingual structured notes, chunk boundaries, provenance/timestamps, fixture-based quality checks.
5. **7.5 Persistence and API:** migration, ownership checks, job/status/read routes, integration tests with disposable PostgreSQL.
6. **7.6 Visual evidence/OCR:** learner-uploaded frames/screenshots, bounded OCR, evidence links, image-size and failure tests.
7. **7.7 Flutter integration:** URL form, language selector, progress/error state, notes reader, timestamps, unit/widget tests.
8. **7.8 PDF export and end-to-end hardening:** export, long-input tests, security regression suite, CI and deployment readiness checks.
9. **7.9 Optional local/open model adapter:** only if memory/CPU budget and free hosting constraints support it; never required for the no-key baseline.

Each phase must be a separate branch/PR, must run the narrow tests plus relevant existing regression tests, and must not merge or deploy automatically merely because the branch exists.

## Acceptance and test matrix

- URL tests: valid watch, short, and youtu.be URLs; malformed URL; non-YouTube host; deceptive hostname; localhost/private IP; encoded URL tricks; unsupported playlist-only URL.
- Transcript tests: captions present, captions absent, disabled/unavailable, multilingual captions, empty transcript, malformed timestamps, duplicate segments, long transcript chunking, transient provider error.
- Notes tests: Hindi, English, bilingual; empty input; large input; deterministic output; timestamp/provenance retained; no invented visual evidence.
- Visual tests: accepted image types, oversized images, invalid image, OCR empty result, OCR exception, text/diagram evidence linked to supplied frame.
- API/security tests: unauthenticated request rejected; learner A cannot read learner B's job/notes; rate/size/duration limits; no secret/transcript leakage in errors/logs.
- Database tests: migration up/down policy consistent with repository conventions, uniqueness/idempotency where applicable, PostgreSQL integration tests on disposable CI database.
- Flutter tests: form validation, language selection, loading/retry/error states, notes rendering, timestamps, export action, auth-required behavior.
- Regression gates: existing Python suite, PostgreSQL integration tests, `flutter analyze`, `flutter test`, and `flutter build apk --release` when affected.

## Phase 7.1 completion criteria

- Existing architecture and hosting claims were checked against repository documentation and code.
- Boundaries, no-key fallback, content-access constraints, phase breakdown, and test matrix are written down.
- No existing exam feature or production configuration is changed.
- Implementation starts only in the next phase after this architecture contract is reviewed.
