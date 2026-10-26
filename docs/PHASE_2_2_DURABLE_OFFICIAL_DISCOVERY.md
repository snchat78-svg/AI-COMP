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
- Fail fast on permanent TLS protocol/certificate errors instead of retrying them; retain bounded retries for transient network errors. Certificate validation remains enabled, and this hardening does not restore host reachability.
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

## Latest hardening and current acceptance gate (24 October 2026)

PR [#52](https://github.com/snchat78-svg/AI-COMP/pull/52) was merged at `5baf6601c7addbecdf849fbcbaa16e966f6b386f`. It adds a fail-fast rule for permanent TLS protocol/certificate errors while preserving the existing bounded retry behavior for transient network errors. Exact tested head `36c3db3d91d9bb69d8ccfdb7f9d1e5c3df3f1861` passed [workflow 40066852069](https://github.com/snchat78-svg/AI-COMP/actions/runs/40066852069): 545 tests passed with 14 warnings, and the API container build passed.

**Operational status remains BLOCKED:** later scheduled official-source-research [run #15](https://github.com/snchat78-svg/AI-COMP/actions/runs/40067718339) again failed closed and persisted **0 candidates** after the TLS retry fix. DNS was OK for all three hosts; `RSSB_OFFICIAL` TCP timed out, `RSSB_LEGACY_OFFICIAL` TCP connected but certificate-validated TLS failed with `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`, and RPSC IPv4/IPv6 TCP probes failed. The transport improvement reduces pointless retrying; it does not fix outbound connectivity or satisfy Phase 2.2 acceptance. Keep TLS validation, same-host restrictions, robots and terms checks enabled. Do not begin Phase 2.3 data processing until real candidates have persisted.

## Exit checks

- Python tests cover idempotent registry persistence and live discovery persistence.
- The production database schema is reused; no destructive migration is introduced.
- Existing test engine, login, history and preparation code remains in place.

## Latest Render-side connectivity evidence — 26 October 2026

After the fixed diagnostic endpoint was updated to accept only the exact ChatGPT link tracking parameter, Render deployment for main commit `f49511a3ebca0a875c4ba8bae30f8ed66964e0a5` completed successfully. [Source-health workflow run #11](https://github.com/snchat78-svg/AI-COMP/actions/runs/40274447472) obtained a valid response from the deployed API and then failed its intended gate because no registered official host passed both TCP and certificate-validated TLS:

- `RSSB_OFFICIAL`: DNS OK, IPv4 TCP FAIL (`TimeoutError`), TLS NOT_REACHED, no IPv6 records.
- `RSSB_LEGACY_OFFICIAL`: DNS OK, IPv4 TCP PASS, TLS FAIL (`SSLError`); previous measured detail was `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`. Standard TLS must remain enabled.
- `RPSC_OFFICIAL`: DNS OK, IPv4 TCP FAIL (`TimeoutError`), IPv6 TCP FAIL (`OSError`), TLS NOT_REACHED.

Therefore the failed run is not a diagnostic-route or source-code regression; it confirms Phase 2.2's live connectivity acceptance is still blocked. Current RSSB and RPSC hosts do not complete a TCP connection from the deployed source-health runtime, while the legacy RSSB host cannot complete a standard validated TLS handshake. Do not disable TLS, switch to an unofficial mirror, or treat a zero-candidate workflow as success. Continue only after a verified official HTTPS route becomes reachable and persists nonzero real candidates.
