# Phase 2.3 — Durable Paper Processing and Extraction

## Purpose

Turn the URLs discovered by Phase 2.2 into content-addressed original documents and source-observed question/answer-key candidates, without promoting them to verified exam history.

## Implemented

- Preserve visible link labels from official archive pages as candidate titles (for example, exam name/year text supplied by the archive).
- Exclude common archive/listing pages from the candidate downloader; the source discovery stage still traverses them to find document links.
- Re-check candidate URLs against the registered source host, allowed paths, and current robots.txt before fetching.
- Block cross-host redirects and non-HTTP(S) redirects.
- Bound paper downloads to 25 MiB and robots.txt to 1 MiB.
- Upload bytes to a private Supabase Storage bucket using a SHA-256-addressed key.
- Confirm that an existing bucket is private before writing to it.
- Persist document metadata and normalized text to PostgreSQL.
- Extract English/Hindi MCQ candidates and answer-key entries separately, preserving source-observed text and question numbering.
- Add a Tesseract OCR adapter for scanned PDFs/images, using Hindi + English models.
- Record candidates as FETCHED, FAILED, or REJECTED; do not infer an answer or an exam appearance from a filename.

## Required GitHub repository secrets

The already configured secret AI_COMP_DATABASE_URL plus these two new secrets are required by the scheduled processor:

- SUPABASE_URL: the HTTPS Project URL shown in Supabase Project Settings.
- SUPABASE_SERVICE_ROLE_KEY: the server-only legacy service-role JWT key for Storage API access. Do not use the public/anon key, do not add this key to Flutter, and never paste it into chat or logs.

The worker creates a private bucket named ai-comp-papers if it does not exist. An existing bucket must be verifiably private. Original content is stored under papers/<first-two-hash-chars>/<sha256> and the database stores a private supabase:// object locator.

## Operations

- Workflow: Actions → official-paper-processing → Run workflow.
- Defaults: source all, limit 10; keep batches small at first. Use retry_failed only after reviewing the prior run.
- The workflow also runs daily at 02:15 UTC (07:45 India time). If required secrets are missing, it records a skip summary instead of printing or attempting to use missing credentials.
- Discovery remains in the separate official-source-research workflow and does not require object-storage credentials.

## Trust boundary (non-negotiable)

This stage stores extracted QuestionCandidate and AnswerKeyEntry rows. It intentionally does not:

- mark extracted answers VERIFIED;
- pair separate papers and answer keys based only on similar filenames;
- create exam_appearances;
- claim year/shift/question number beyond what a future metadata-verification step can establish;
- copy historical questions into the AI-generated question table;
- make the current practice-test verified pool non-empty by lowering its verification rules.

Therefore this phase alone does not fix “No verified questions are available yet.” The next phase must pair official paper metadata and answer keys, reconcile question numbers/options, persist explicit source verification, and expose verified historical questions through a distinct test-pool source without mislabelling them as AI-generated.

## Latest live processing evidence (24 October 2026)

The scheduled [official-paper-processing run #10](https://github.com/snchat78-svg/AI-COMP/actions/runs/40073489696) exited successfully but reported `processed=0`, `question_candidates=0`, and `failed=0`. This was a clean empty-queue run, not successful ingestion of a document. Do not mark Phase 2.3 data acceptance complete until Phase 2.2 persists real candidates and a subsequent processing run demonstrates fetched document bytes, SHA-256 identity, private storage and extraction counters.

## Test coverage

Unit tests exercise private-bucket behavior, SHA-256 idempotency, candidate download policy boundaries, duplicate document skipping, text extraction, question/answer separation, and the absence of false historical-appearance writes. Full repository CI remains the release gate.
