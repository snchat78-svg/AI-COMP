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


## Official RPSC archive route correction — 26 October 2026

Review of the live official RPSC site found that its own navigation links **Question Papers** to `https://rpsc.rajasthan.gov.in/quespapers` and **Answer Keys** to `https://rpsc.rajasthan.gov.in/answerkeys`. The corresponding public pages currently show titled paper/key entries (for example, the Question Papers page lists multiple 2025 recruitment paper entries and the Answer Keys page lists dated 2026 entries).

The discovery implementation had been seeding the non-current `viewcommon?Slice=QP` and `viewcommon?Slice=AK` routes instead. This increment replaces those seeds with the official `/quespapers` and `/answerkeys` routes and adds deterministic mocked regression coverage for both page traversal, retained paper titles and same-host PDF links. Source links:
- Official RPSC question papers: https://rpsc.rajasthan.gov.in/quespapers
- Official RPSC answer keys: https://rpsc.rajasthan.gov.in/answerkeys

This is a discovery-path correction, not proof of live source ingestion. The measured GitHub Actions/Render connectivity gate still has RSSB/RPSC TCP failures and legacy RSSB TLS failure. The crawler must still obey the registered source's `robots.txt`, allowlisted same-host redirects and URL policy; do not relax TLS or use mirrors. Keep Phase 2.2 BLOCKED until the scheduled workflow successfully reaches an official source and persists nonzero real candidates.


## Live source recheck after RPSC archive-route fix — 26 October 2026

PR [#64](https://github.com/snchat78-svg/AI-COMP/pull/64) merged as `9984f3892a62740840b93db276ae13ec77ca8001`. Exact-head CI run [40279750490](https://github.com/snchat78-svg/AI-COMP/actions/runs/40279750490) passed the pytest suite and API container build. The change corrects the RPSC discovery seeds to the current official [Question Papers](https://rpsc.rajasthan.gov.in/quespapers) and [Answer Keys](https://rpsc.rajasthan.gov.in/answerkeys) routes.

The merge automatically triggered [official-source-research run #18](https://github.com/snchat78-svg/AI-COMP/actions/runs/40279924824) on that exact main commit. It failed closed and persisted **0 paper candidates**:
- `RSSB_OFFICIAL`: DNS OK; IPv4 TCP timeout; TLS not reached.
- `RSSB_LEGACY_OFFICIAL`: TCP connects, but certificate-validated TLS fails with `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`.
- `RPSC_OFFICIAL`: IPv4 TCP timeout and IPv6 network-unreachable error; TLS not reached.
- All three crawl results were `BLOCKED_OR_FAILED`; total persisted candidates: **0**.

The RPSC route correction is therefore an implemented and CI-tested code fix, but it does not resolve the separate egress/TLS blocker. Keep Phase 2.2 **BLOCKED** and Phase 6.56 **IN_PROGRESS**. Do not weaken TLS, use an unofficial mirror as official evidence, rerun empty-queue downstream processing as if complete, or advance phases. The next acceptance gate remains successful, robots-compliant retrieval from at least one registered official HTTPS source and nonzero persisted real paper candidates, followed by existing paper processing, answer-key matching, independent review and mobile E2E.


## Cross-runtime diagnosis: fixed HTTPS control next (27 October 2026)

The Render Dashboard identifies its shared outbound ranges as `74.220.48.0/24` and `74.220.56.0/24`. The fresh Render probe from [job #121586949254](https://github.com/snchat78-svg/AI-COMP/actions/runs/40274447472) continued to report current RSSB/RPSC TCP timeouts and a standard-TLS failure on the legacy host. This is consistent with a path-specific problem but does not prove that those CIDRs are blocked.

A controlled incremental diagnostic is being added to the existing source-health function/workflow: probe fixed `example.com:443` connectivity as a separate control result, then compare it with the official sources from the same Render runtime. The control is not part of the official source registry, is never used for paper discovery, and cannot satisfy the official-source gate. It performs only DNS/TCP/certificate-validated TLS; it does not retrieve control-page or paper content. Its URL is fixed in code, not a request parameter.

After exact-head CI passes and the automatic post-deploy report is available, use the comparison only to classify general egress versus official-host-specific failure. Even if general egress passes, request authorized confirmation before concluding the official CIDRs are filtered. Phase 2.2 remains BLOCKED and no paper-processing or answer-key phase should be treated as complete until nonzero real official candidates and downstream evidence exist.
