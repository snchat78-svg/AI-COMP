# Phase 2.2 — Durable Official-Source Discovery

## Why this increment exists

The repository already contains the Phase 1 source/exam domain contracts, safe live discovery adapters, document hashing/storage components and PostgreSQL research persistence. However, the seed registry was in-memory only and no scheduled entry point persisted live-discovery candidates. As a result, having these modules did not guarantee that the configured database contained sources or newly discovered candidates.

## Implemented

- Idempotently upsert the existing Rajasthan seed registry into the existing PostgreSQL tables: `conducting_bodies`, `exams`, `paper_categories`, and `sources`.
- Add an explicit research CLI: `python -m ai_comp.research.research_cli`.
- Enforce a bounded per-source discovery limit (1–100), source-registry selection, robots.txt/access requirements, official-domain filtering and candidate URL policy.
- Persist likely question-paper / answer-key URLs to `paper_candidates`.
- Give live-discovered candidates deterministic IDs from source ID + URL so a changed sitemap order cannot overwrite another candidate.
- Record discovery timestamps.
- Add a daily GitHub Actions workflow at 06:45 IST plus manual dispatch and a per-run summary.
- Continue when one registered source is inaccessible; report that source as blocked/failed rather than disabling discovery for the other source.
- Add unit tests for registry upserts, safe URL filtering, candidate persistence and unknown-source rejection.

## Important trust boundary

A discovered URL is only a **candidate**. This workflow does not mark it as a verified paper, answer key, question or exam appearance. It does not claim that a question appeared in any exam without source-backed exam metadata and verification.

The workflow does not yet populate the practice-test pool. The next incremental work is durable paper fetching/content storage, PDF text extraction and Hindi+English OCR where needed, structured question extraction, official answer-key pairing, and verified ingestion into the canonical question bank. Keep those stages separate so generated answers are never confused with official keys.

## Operations

- Required GitHub Actions secret: `AI_COMP_DATABASE_URL` (existing Session Pooler connection string).
- Manual run: Actions → **official-source-research** → Run workflow.
- Daily runs do not apply migrations or change service environment.
- If `robots.txt` is missing, inaccessible, or disallows traversal, discovery fails closed and the run summary explains the source-level outcome.
- Storage of raw PDF bytes across ephemeral runners is intentionally not claimed by this increment; object storage integration is a follow-up before long-lived processing is enabled.

## Exit checks

- Python tests cover idempotent registry persistence and live discovery persistence.
- The production database schema is reused; no destructive migration is introduced.
- Existing test engine, login, history and preparation code remains in place.
