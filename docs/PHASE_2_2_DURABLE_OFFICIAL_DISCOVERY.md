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


## Fixed HTTPS control after deployment — 27 October 2026

PR [#68](https://github.com/snchat78-svg/AI-COMP/pull/68) is merged at `7564cf4b2dcf251098da6e6662fbe159b5993932`; [exact-head CI run #609](https://github.com/snchat78-svg/AI-COMP/actions/runs/40449133149) passed 552 tests (14 warnings) and the API container build. Render deploy `dep-dbg2dlg473hc73fac31g` is LIVE, and its app log records the source-health endpoint returning `200 OK` at `2026-10-27T04:22:16Z`.

**Live-control result is not yet captured:** available logs do not include the response body, and the tool environment could not resolve the deployed host directly. Do not infer that `example.com` passed from HTTP 200. Read the JSON at [the deployed source-health endpoint](https://ai-comp-api.onrender.com/diagnostics/official-source-health) and inspect the separate `network_control` object as well as all official host rows. The control uses only DNS/TCP/certificate-validated TLS; it fetches no page content and is never considered a source candidate. The required official-source gate still checks only the official `results` collection.

A successful general control with continuing official-host failures would narrow the diagnostic but not prove explicit CIDR filtering; ask an authorized official/network contact to verify the observed Render ranges. Keep Phase 2.2 blocked and Phase 6.56 in progress until an official TLS route is reachable and real candidate/document acceptance proceeds.


## Render general-control result and cross-runtime check — 27 October 2026

The source-health rerun [workflow run #12, attempt 2](https://github.com/snchat78-svg/AI-COMP/actions/runs/40449304879/job/122025472235) returned the report with the fixed `network_control` result (the response was marked cached, so the exact original probe timestamp is unavailable). Fixed control `example.com`: DNS OK, IPv4 TCP PASS, certificate-validated IPv4 TLS PASS; IPv6 TCP FAIL (`OSError`), TLS not reached. In the same report, RSSB current host still timed out at TCP, legacy RSSB connected at TCP but failed TLS validation, and RPSC timed out at IPv4 TCP with an IPv6 TCP failure.

This narrows the observed issue: Render general IPv4 HTTPS to a fixed control works in the returned report while the official hosts fail, but it does not prove an explicit block of the shared Render egress CIDRs. The existing source-health workflow correctly remains failed at the official-source gate and fetched no paper bytes.

PR [#70](https://github.com/snchat78-svg/AI-COMP/pull/70) adds a second read-only diagnostic from a GitHub-hosted runner, comparing the same fixed control with the official host probes from another runtime. It also changes the Render workflow to require the `network_control` response schema before accepting a report, avoiding false acceptance of an older cached payload. That comparison performs only DNS/TCP/certificate-validated TLS and writes no database records. Use results to guide diagnosis, not as proof of a CIDR block. Phase 2.2 remains BLOCKED and Phase 6.56 remains IN_PROGRESS until official-source fetch succeeds and the full data/review/mobile gates are accepted.


## Cross-runtime diagnostic result — 27 October 2026

PR #70 is merged. Read-only GitHub-hosted comparison [run #1](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333663) succeeded; Render source-health [run #13](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333727) returned a fresh report then failed the expected official-source TCP/TLS gate. CI #613 and #614 passed 552 tests (14 warnings) and API-container build.

Both runtimes had the same result: fixed `example.com` DNS OK / IPv4 TCP PASS / certificate-validated IPv4 TLS PASS (IPv6 TCP fail); current RSSB official host DNS OK but IPv4 TCP timeout; legacy RSSB TCP connects but certificate-validated TLS fails with `SSLError`; RPSC IPv4 TCP times out and IPv6 TCP fails. This pattern suggests the issue is specific to paths/destinations rather than a general IPv4 HTTPS outage, but does not prove explicit blocking of Render shared outbound CIDRs.

No pages or paper content were fetched and no database was read or changed by these diagnostic workflows. Next: seek authorized confirmation whether the official hosts filter connections from the listed ranges, or evaluate an approved alternative runtime/egress route with cost and security review. Do not weaken TLS or repeat the pending candidate fetch until an approved route is shown to work. Phase 2.2 remains BLOCKED; Phase 6.56 remains IN_PROGRESS until official document/content acceptance, full syllabus mapping review and mobile E2E pass.


## External blocker escalation — 27 October 2026

GitHub-hosted comparison [run #1](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333663) and Render source-health [run #13](https://github.com/snchat78-svg/AI-COMP/actions/runs/40455333727) agree: general IPv4 HTTPS to fixed `example.com:443` succeeds, but current RSSB/RPSC official host TCP connections time out and legacy RSSB's standard validated TLS handshake fails. The Render Dashboard lists shared egress ranges `74.220.48.0/24` and `74.220.56.0/24`. This narrows the problem to destination/path-specific connectivity; it does not prove these ranges are explicitly blocked.

The next dependency is external rather than another retry/code rewrite. See [Issue #74](https://github.com/snchat78-svg/AI-COMP/issues/74). An authorized operator should ask the official RSSB IT/network contact to confirm egress filtering and provide a supported official HTTPS endpoint or an approved access route. A public contact listed by the official board is `itcell.rssb@rajasthan.gov.in`; verify it against the board's current official contact page before use.

Do not add an unverified source domain, use a proxy or unofficial mirror, weaken TLS, purchase dedicated egress or migrate regions without evidence and separate explicit approval. Keep the existing candidate pending until a validated route works. Phase 2.2 remains BLOCKED and Phase 6.56 remains IN_PROGRESS; no paper or syllabus has been verified from these diagnostics.


## No-contact alternate official-government route search — 27 October 2026

The user has instructed that no call or email be made. None has been made. Continue only with public route research and read-only connectivity measurements.

The cross-runtime test already established that the general `example.com:443` control passes IPv4 TCP and standard certificate-validated TLS from Render and GitHub-hosted automation, whereas the registered RSSB/RPSC hosts fail with timeouts and the legacy RSSB host fails standard TLS. This does not prove the government servers explicitly block cloud CIDRs.

The next diagnostic tests two fixed public Rajasthan government portal hosts—`recruitment.rajasthan.gov.in` and `landrevenue.rajasthan.gov.in`—because the unified recruitment portal is referenced by Board documents and a Board-signed notice is indexed on the Land Revenue government host. These are only candidate route leads, not paper-source approvals. Probes perform DNS/TCP/certificate-validated TLS only; no page/PDF bytes are fetched. The hosts are excluded from the source registry and cannot create paper candidates.

If a route connects, verify robots/terms and then prove that its own public official pages publish the exact paper/syllabus bytes before using it. Preserve original source provenance and SHA-256. If no relevant public official alternate exists, retain the operational block; do not use an unofficial mirror, a proxy, unsafe TLS compatibility, or an unauthorized contact.


## Jan Soochna public RSSB Question Papers service route — 27 October 2026

The Render-side probe in [run #14](https://github.com/snchat78-svg/AI-COMP/actions/runs/40462219593) showed general IPv4 HTTPS control PASS and the Rajasthan Recruitment and Land Revenue portal controls PASS, while all currently registered RSSB/RPSC hosts remain blocked at TCP or standard TLS. This does not prove a firewall policy but indicates that some Rajasthan government hosts are reachable from the same service.

Public Jan Soochna listings include a named `Question Papers of RSSB` service and a separate `Answer Key of RSSB` service ([services listing](https://jansoochna.rajasthan.gov.in/Services), [scheme listing](https://jansoochna.rajasthan.gov.in/Scheme)). This is a promising public lead, not an approved source or evidence that PDFs are directly hosted there.

A fixed Jan Soochna connectivity control is now included in the read-only route probe. If it passes, examine only public service navigation and inspect the resolved URLs. If URLs lead back to the inaccessible RSSB host, do not attempt to proxy or route around that restriction; record that the public portal does not provide an independent accessible content path. If a PDF is directly hosted on the government portal, verify title, issuing board, notification/exam identity, source access policy, SHA-256 and complete file before adding a candidate.


## Jan Soochna public RSSB service index — guarded inspection (27 October 2026)

The post-PR #77 Render report [workflow #15](https://github.com/snchat78-svg/AI-COMP/actions/runs/40462990677) shows Jan Soochna IPv4 TCP and normal certificate-validated TLS PASS from Render. Current RSSB and RPSC connections remain blocked at TCP; legacy RSSB still fails certificate-validated TLS. Thus the portal is reachable but no official paper file has been demonstrated or fetched.

The next increment adds a read-only probe of Jan Soochna's public RSSB service listing:
- It must fetch a valid `robots.txt` first and stops if unavailable or if `/Services` or `/Scheme` is disallowed.
- It fetches only those fixed pages, using bounded response size/time and standard certificate validation.
- It parses the visible public anchor labels for RSSB Question Papers and Answer Key services.
- It never follows service-page links, never requests an RSSB PDF and never creates paper candidates or source registry entries.
- A same-host URL may be inspected in a later, separate step only if the public service page is allowed; an external target hostname is reported but not followed.

If the service points to the blocked RSSB host, do not proxy or circumvent the access restriction. If it links to a directly hosted public government PDF, verify the exact recruitment/exam/year/notification provenance, access rules, full document bytes and SHA-256 before considering the existing protected ingestion workflow. The official-source acceptance gate remains unchanged.


## Jan Soochna route endpoint rollout retry — 27 October 2026

The robots-gated probe was added by PR #78, whose exact-head CI passed. The follow-up Render workflow run [#16](https://github.com/snchat78-svg/AI-COMP/actions/runs/40463899245) confirmed the updated source-health endpoint but received HTTP 404 when immediately querying the new Jan Soochna endpoint during the same Render rollout. Treat this as a deployment race: it did not reach the `robots.txt` check and produced no public service-page finding.

The follow-up workflow fix retries the fixed Jan Soochna diagnostic endpoint for a bounded window until its response schema is available, without changing its content access policy. After deployment, use the robots result as the first gate; if robots unavailable/disallows the route, stop. Otherwise record the RSSB service/answer-key links, but do not follow external URLs or download paper bytes here. The original paper-source gate remains blocked until approved official PDFs are fetched and independently reviewed.


## Public Jan Soochna service detail investigation — 27 October 2026

The post-PR #79 Render diagnostic workflow [run #17](https://github.com/snchat78-svg/AI-COMP/actions/runs/40464311120) finally completed the previously interrupted Jan Soochna check:
- `robots.txt` was readable.
- `/Services` and `/Scheme` were both permitted for the chosen user-agent and returned HTTP 200.
- Both pages include a same-host RSSB question-paper service link (one uses `/Services/GetMoreData?q=...`, one uses `/Services?q=...`).
- The probe stopped at those index links and fetched no exam document. The overall workflow failed at the still-correct official-source gate: current RSSB and RPSC time out, and the legacy RSSB endpoint fails standard certificate-validated TLS.

The detail-inspection increment now checks `robots.txt` for each exact observed same-host link before requesting it. Redirects are not followed, avoiding an unexamined redirect to a robots-disallowed path or another host. Only bounded `text/html`, `application/xhtml+xml`, `application/json` or `text/plain` responses are read. A non-approved MIME type such as `application/pdf` is rejected before reading any response body bytes. Links in a public service-detail response are listed as metadata; they are not followed and no PDF is downloaded.

If a candidate PDF URL appears, the next separate acceptance gate is to verify that it is directly on the government host, reachable through the already validated access policy and actual source bytes can be fetched by the established protected fetch workflow. Until then no candidate is registered, no SHA-256 is asserted, and no paper is declared official. Do not proxy, bypass TLS, or contact the Board.

## robots.txt rule precedence regression and exact-head validation — 27 October 2026

Initial PR #80 code head `f30b154fa8de64e09c737c9dcea8c21d87ec2ead` failed [CI run #629](https://github.com/snchat78-svg/AI-COMP/actions/runs/40464857614): 564 passed, one failed. The failing test proved Python's standard first-match rule evaluation could incorrectly allow a service URL because broad `Allow: /Services` preceded narrower `Disallow: /Services/GetMoreData`.

The implementation now resolves the most-specific matching rule before requesting each service URL, with `Allow` winning only when matching specificity ties. Updated code head `164536a1f84319a60e39b3305895108f97f03e5b` passed [CI run #630](https://github.com/snchat78-svg/AI-COMP/actions/runs/40469616564): 565 tests passed, 14 warnings, API container build passed. That run validates the code fix; the docs follow-up adds a new commit and must receive its own exact-head CI before merge.

After merge/deploy, review the new Render endpoint's per-service result. The diagnostic must continue to fetch only robots-permitted same-host text/HTML/JSON; never follow redirects; never read PDF/binary bodies; and never fetch links it reports. No official PDF, SHA-256, persisted paper candidate or verified answer key is claimed. Phase 2.2 remains BLOCKED until approved official document bytes can be fetched and reviewed through existing gates.

## Jan Soochna service redirects are not followed — 27 October 2026

The strict-schema Render workflow run [#40470532495](https://github.com/snchat78-svg/AI-COMP/actions/runs/40470532495) captured the service detail inspection instead of accepting the prior index-only schema. Both same-host links surfaced on the robots-permitted public index returned `REDIRECT_NOT_FOLLOWED`: `/Services/GetMoreData` and `/Services`. No PDF or answer-key bytes were fetched. The same diagnostic confirms that current registered RSSB/RPSC connections still fail TCP, while legacy RSSB fails standard certificate-validated TLS.

PR [#82](https://github.com/snchat78-svg/AI-COMP/pull/82) is merged at `ee305969d43bcddd95a0a35074ccb56a7dbb3d84`; exact-head CI [#40470902066](https://github.com/snchat78-svg/AI-COMP/actions/runs/40470902066) passed 567 tests, 14 warnings and API container build.

Post-deploy Render run [#40471070621, attempt 2](https://github.com/snchat78-svg/AI-COMP/actions/runs/40471070621) reports same-host targets:
- `/Services/GetMoreData` → `/Services/ClickablePDF`.
- `/Services` → `/Services/GetMoreData`.
Neither redirect was followed; no paper/answer-key bytes were fetched. Current RSSB and RPSC TCP connections still time out, and legacy RSSB fails standard certificate-validated TLS.

Open PR [#83](https://github.com/snchat78-svg/AI-COMP/pull/83) adds one bounded target inspection after re-checking robots for the exact target URL. It requires the target to remain HTTPS on `jansoochna.rajasthan.gov.in`; it does not follow a further redirect. It reads only bounded text/HTML/JSON/plain-text responses, rejects PDF/binary before body read, and emits document-like links as metadata only. Exact-head CI and post-deploy target results are pending.

Do not register candidate papers, fetch PDF bodies, claim SHA-256, or change the official source registry in this diagnostic. Any later document-ingestion step must use the existing protected fetch/review workflow and establish issuing-board provenance.

Phase 2.2 remains BLOCKED; Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED; Phase 6.58 remains BLOCKED.

## Second Location header is observed but not followed — 27 October 2026

After PR #83 deployed, Render source-health [run #40471826496, attempt 2](https://github.com/snchat78-svg/AI-COMP/actions/runs/40471826496) reported:
- `/Services/GetMoreData` → `/Services/ClickablePDF`; the robots-permitted target request returns another HTTP 302.
- `/Services` → `/Services/GetMoreData`; the robots-permitted target request returns another HTTP 302.
Both targets remain on `jansoochna.rajasthan.gov.in`. No PDF/answer-key bytes were read; the diagnostic stopped before following a second redirect.

PR [#84](https://github.com/snchat78-svg/AI-COMP/pull/84) will expose only the next redirect's scheme, hostname and path from the returned `Location` header. Query and fragment are omitted; no further request is made. This narrows the route without downloading a paper or bypassing the registered official-source TLS gate. Exact-head CI and post-deploy report remain pending.

The official source gate remains blocked: current registered RSSB/RPSC connections time out at TCP and legacy RSSB fails certificate-validated TLS. Phase 2.2 BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED.

## Cookie-session hypothesis for the public service redirect loop — 27 October 2026

After PR #84 deployment, live Render source-health [#40472474696, attempt 2](https://github.com/snchat78-svg/AI-COMP/actions/runs/40472474696) confirms:
- `/Services/GetMoreData` → `/Services/ClickablePDF` → `/Services`
- `/Services` → `/Services/GetMoreData` → `/Services/ClickablePDF`
Only the first target request is made after exact robots permission; its second `Location` header is recorded but not followed. No PDF or answer-key bytes were read.

Open PR [#85](https://github.com/snchat78-svg/AI-COMP/pull/85) changes only transport state handling for this diagnostic: one in-memory CookieJar and one opener per probe run, never persisted or reported. This tests whether cookies returned by the public portal change the loop. Auto-redirect remains disabled; fixed-host HTTPS validation, exact target robots checks, bounded time/body, no-third-request and PDF/binary pre-read rejection remain in force. This is a hypothesis, not an assertion that cookies are required.

After exact-head CI and deployment:
- If the loop remains, stop this route path and do not keep probing it.
- If the route returns an allowed text/HTML/JSON response, document-like links remain metadata only and are not fetched.
- If it returns a PDF/binary MIME type, record only the type and do not read body bytes.
- Do not persist candidates or change the registered official-source inventory until official document provenance and the existing protected fetch/review gates pass.

Phase 2.2 remains BLOCKED; Phase 6.56 remains IN_PROGRESS; Phase 6.57 remains PLANNED; Phase 6.58 remains BLOCKED.


## PR #85 cookie-session experiment — deployment confirmed, result not captured (27 October 2026)

PR #85 is merged/deployed at main commit `1946891bcbd97cf456af430b12b62dcb0580fc25`. Its test head `c3226b0f195c367fc9f6e5d3de8a73cdcd5467e0` passed [CI #40473032296](https://github.com/snchat78-svg/AI-COMP/actions/runs/40473032296): 571 tests, 14 warnings and API container build. Render logs confirm the Jan Soochna diagnostic endpoint returned HTTP 200 after deployment, but the logs do not include its JSON body and this workspace could not resolve the service hostname for a direct read. Therefore the cookie-session hypothesis outcome is **UNKNOWN**. HTTP 200 only means the diagnostic route responded; it does not prove the redirect loop changed.

**Next:** inspect the post-deploy `render-official-source-health` workflow summary for `service_link_inspections`. The last captured report before PR #85 showed the same-host loop `/Services/GetMoreData → /Services/ClickablePDF → /Services` and the reverse starting from `/Services`; no paper/answer-key bytes were fetched. If that loop remains, stop probing Jan Soochna service routes. Phase 2.2 remains BLOCKED until a directly accessible, approved official HTTPS route passes normal TLS and yields full source bytes that pass provenance, hash and review gates. No call/email, proxy, TLS bypass, or candidate registration is authorized.


## PR-triggered report confirms Jan Soochna route is blocked at robots fetch — 27 October 2026

PR [#87](https://github.com/snchat78-svg/AI-COMP/pull/87) merged at `69d5e9eb98ae0fd42de9d9d4864153be38875f37`; exact-head tests [run #40501903542](https://github.com/snchat78-svg/AI-COMP/actions/runs/40501903542) passed. The PR-triggered report-only workflow [run #40501903388](https://github.com/snchat78-svg/AI-COMP/actions/runs/40501903388) published fresh safe metadata. The official-source acceptance step was skipped only for this PR run; it still applies to main pushes and manual runs.

Registered hosts still fail normal access: current RSSB and RPSC hosts time out at TCP, and the RSSB legacy host fails validated TLS. A fixed general HTTPS control and the Rajasthan recruitment, Land Revenue, and Jan Soochna host connectivity controls pass IPv4 TCP/TLS, but these tests do not make those hosts accepted exam-paper sources.

The Jan Soochna service endpoint returned HTTP 200, but the report was `ROBOTS_UNAVAILABLE` and `robots.status=HTTP_ERROR`; `service_link_inspections` was absent, so the probe did not inspect service links. Stop using this route unless the robots endpoint becomes publicly readable through an ordinary, explicitly permitted path; do not retry redirects or access restricted pages. No paper/answer-key bytes, content hashes or new candidates were created.

**Next action:** investigate a different directly hosted official source only when its public documentation, normal TLS, robots/terms and provenance can be verified. Phase 2.2 remains BLOCKED; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. No calls/email, proxies or TLS weakening.


## Cross-runtime connectivity proof and blocked-route contract fix (27 October 2026)

PR [#89](https://github.com/snchat78-svg/AI-COMP/pull/89) merged at 3b050227321bb29001c83c85f911537b4b0165d7. Both exact-head [tests run #40502982570](https://github.com/snchat78-svg/AI-COMP/actions/runs/40502982570) and [dual-runtime diagnostic run #40502982762](https://github.com/snchat78-svg/AI-COMP/actions/runs/40502982762) passed. GitHub-hosted runner and Render show the same official-host failures. DNS resolved only one IPv4 record for each registered official host; no alternate IPv4 address was available for another attempt. The legacy RSSB hostname accepts TCP but fails normal certificate-validated TLS. example.com:443 IPv4 TCP/TLS and some public government connectivity controls pass, so this is not a blanket HTTPS outage. These results do not identify whether a firewall, host configuration or upstream routing is the cause; no source-control override is justified.

PR #90 keeps the Jan Soochna diagnostic response shape stable when it stops at the robots gate and lets the workflow recognize that known fail-closed status without repeating the same cached request. This is reporting/test consistency only; it does not change robots permission, follow redirects or retrieve documents.

Phase 2.2 remains BLOCKED. Continue only with another directly accessible, approved official HTTPS document route. No paper/answer-key bytes or new candidates have been accepted.


## Accessible official recruitment portal route check — 27 October 2026

The current RSSB/RPSC route remains blocked in both GitHub-hosted and Render probes. Search-indexed official results identify the Rajasthan Recruitment Portal at `recruitment.rajasthan.gov.in` as the state recruitment portal and it has public recruitment index pages; this is a route lead, not proof that it is an official exam-paper archive. A new diagnostic-only probe checks that portal's `robots.txt` first and inspects only three fixed public index paths if the robots rules explicitly allow them. It lists only metadata for links labelled as question papers or answer keys. It never follows document links, downloads PDFs, changes the source registry, writes to PostgreSQL or promotes a candidate.

Acceptance for this investigation is a live Render report showing whether robots permits the public indexes and whether the indexes expose direct, official paper/answer-key document links. Even if a link is found, the target must be verified against the responsible body's official provenance and then fetched through the existing protected, certificate-validated workflow before registering a paper candidate. A generic recruitment advertisement or portal-wide document is not a past paper. Phase 2.2 remains BLOCKED until a compliant route yields nonzero real candidates.

No proxy, manual DNS override, robots bypass, TLS weakening, emails or phone calls.

## Post-merge live result for the Recruitment Portal route — 27 October 2026

PR [#91](https://github.com/snchat78-svg/AI-COMP/pull/91) merged at `0a2d5aef0daa084fbbb5e6f2a281fd38661510f9`; exact-head test and API container build passed [run #40519631423](https://github.com/snchat78-svg/AI-COMP/actions/runs/40519631423). After deployment, main source-health [run #40519877289](https://github.com/snchat78-svg/AI-COMP/actions/runs/40519877289) reached `/diagnostics/recruitment-portal-paper-route` and reported:

- `status=ROBOTS_UNAVAILABLE`; robots status `HTTP_ERROR`.
- `pages_inspected=0`; no fixed index path was requested.
- No paper/answer-key bytes fetched, no database/source registry changes, and `candidate_promotions=0`.
- The existing official-source acceptance gate still failed: `RSSB_OFFICIAL` TCP timeout; `RSSB_LEGACY_OFFICIAL` TCP passes but validated TLS fails; `RPSC_OFFICIAL` TCP/network failures. Main research [run #40519877291](https://github.com/snchat78-svg/AI-COMP/actions/runs/40519877291) persisted `0` paper candidates.

This public route must remain closed at the robots gate until robots.txt is accessible under normal public access; do not retry the index pages or follow possible links. This is a route lead that failed the access/robots gate, not an accepted paper source. Phase 2.2 remains BLOCKED. The next investigation must use a separately documented official paper endpoint with valid TLS and clear robots/terms permission. No TLS weakening, proxy, DNS override, emails or calls.


## Officially listed legacy www-hostname diagnostic — 28 October 2026

The registered sources continue to fail normal network checks from both GitHub-hosted Actions and Render. The latest official-source research run [#40646313134](https://github.com/snchat78-svg/AI-COMP/actions/runs/40646313134) persisted 0 paper candidates: current RSSB and RPSC fail TCP, while the legacy RSSB hostname fails certificate-validated TLS. The general HTTPS control passes, so the evidence does not support treating this as a blanket HTTPS outage.

A government-hosted Rajasthan tender PDF explicitly lists `www.rsmssb.rajasthan.gov.in` as a departmental website alongside `https://rssb.rajasthan.gov.in/` ([official government PDF](https://rsmssb.rajasthan.gov.in/link_to_external_file/e%20bid15052024.pdf)). This change adds the documented `www` hostname only to the fixed diagnostic-control list. It checks DNS, TCP and standard certificate-validated TLS from GitHub Actions and, after deployment, from Render. It does not request a webpage or PDF, add the alias to the exam-source registry, admit candidates, or let this control satisfy the official-source gate.

The new check is a route diagnostic, not a claim that the access restriction has been solved. If the alias passes, a separate review must confirm redirects, public robots/terms, source identity and a directly fetchable paper before using the existing protected fetch/review flow. If it fails too, record that evidence and do not try proxy, alternate DNS, unsafe TLS or access-control bypasses. Phase 2.2 remains BLOCKED until real official document bytes and provenance pass the existing gates; Phase 6.56 remains IN_PROGRESS, Phase 6.57 PLANNED and Phase 6.58 BLOCKED.


## Post-deployment results for the legacy www-hostname test — 28 October 2026

PR [#93](https://github.com/snchat78-svg/AI-COMP/pull/93) merged at `2bac4cb16dd31e96d4861752b29a0c77bc442f47`; exact-head tests [#40688149278](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688149278) and PR diagnostic [#40688149274](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688149274) passed. Render deployed the commit to `live`. The cross-runtime check [#40688511687](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688511687) reports `www.rsmssb.rajasthan.gov.in` DNS `ERROR` with 0 returned address records from both the GitHub runner and Render; therefore this documented historical hostname does not provide a usable route in either tested runtime. No page/PDF was fetched from that alias.

Main source-health [#40688511772](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688511772) and official-source research [#40688511742](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688511742) both failed the unchanged official-source gate. Registered current RSSB and RPSC hosts still fail normal TCP connectivity; the registered legacy RSSB host still fails standard certificate-validated TLS; main research persisted **0 paper candidates**. The existing paper-processing and answer-key jobs being green with empty queues does not complete those stages.

## Next route decision: expose robots.txt HTTP response codes — 28 October 2026

The fixed Jan Soochna and recruitment-portal route diagnostics previously summarised a robots response as `HTTP_ERROR` without printing the exact HTTP status retained in the diagnostic JSON. The workflow now surfaces the status for both routes. For Jan Soochna only, the robots.txt request also prefers plain text while allowing ordinary HTTP content negotiation (`Accept: text/plain, */*;q=0.8`); the response must still have `Content-Type: text/plain` before parsing. This tests whether the restrictive Accept header caused the observed 406; it does not change robots rules, request index pages when robots is unavailable, or change the fail-closed policy.

Decision rule: inspect the exact response before any further route action. A 5xx or network/TLS failure remains unreachable and stays blocked. A 4xx is an RFC 9309 “unavailable” robots response, for which the standard says a crawler *may* access resources ([RFC 9309 §2.3.1.3–2.3.1.4](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.3.1.3)); it does not automatically authorize this application to change its stricter fail-closed policy or override an HTTP access-denial response. Any policy revision must be separately reviewed and explicitly documented before index pages are inspected. No redirects/proxies/TLS weakening, DNS override, calls or email.

Status remains **Phase 2.2 BLOCKED**, **Phase 6.56 IN_PROGRESS**, **Phase 6.57 PLANNED**, **Phase 6.58 BLOCKED** until actual paper bytes and provenance pass existing acceptance gates.


## Narrow handling for an explicitly absent Recruitment Portal robots.txt — 28 October 2026

After the exact-status diagnostic, the latest confirmed pre-change response for https://recruitment.rajasthan.gov.in/robots.txt was HTTP 404. RFC 9309 §2.3.1.3 defines a 4xx robots response as “unavailable” and permits a crawler to access resources; this project uses only the narrowest practical case: HTTP 404 only, indicating no robots file is published. This is a policy change to the diagnostic—not a network/TLS/access-denial bypass.

PR #95 adds a bounded probe of only the three existing fixed public HTML index paths (/ , /recruitmentservlet, /departmentrecservlet) when and only when that robots endpoint returns 404. Any network/TLS error, redirect, non-404 non-200 response (including 403, 406, 429, or 5xx), or invalid MIME on a 200 robots response remains fail-closed. The probe does not authenticate, follow redirects, follow paper/document links, read PDF bytes, edit the source registry, write to the database or promote candidates. Found links are metadata only and still require provenance checks plus the existing protected fetch/review workflow.

The Jan Soochna endpoint still reports ROBOTS_UNAVAILABLE after the Accept-negotiation change in the first post-deploy rerun; that rerun's old workflow summary did not emit the exact HTTP status, so the hypothesis is not yet proven. Keep that route closed until its exact response is captured. The official-source health gate still fails and 0 candidates are proven. This PR must pass exact-head tests and the post-merge live diagnostic before any claim of progress beyond this investigation.

Status: Phase 2.2 BLOCKED pending a permitted route that yields real source-backed paper candidates; Phase 6.56 IN_PROGRESS; Phase 6.57 PLANNED; Phase 6.58 BLOCKED. No email or phone call, proxy, DNS override, unsafe TLS or unofficial mirror.


## Post-merge results for the narrow Recruitment Portal robots-404 route — 28 October 2026

PR [#95](https://github.com/snchat78-svg/AI-COMP/pull/95) merged at `da19f524f71594c969ba5eced28bc5f4e8968660`. Exact-head tests and API container build passed in [run #40694558174](https://github.com/snchat78-svg/AI-COMP/actions/runs/40694558174). Render deployed the merge as `dep-dbgvb2ijnfac739pguu0` (build and deployment succeeded).

Post-deployment source-health rerun [#40688511772](https://github.com/snchat78-svg/AI-COMP/actions/runs/40688511772) tested the fixed Recruitment Portal route with the new code and reported:

- `robots.txt`: `NOT_PUBLISHED_HTTP_404`, using the explicitly scoped RFC 9309 4xx-unavailable behavior.
- Pages inspected: **3** (`/`, `/recruitmentservlet`, `/departmentrecservlet`); all were `READ_ONLY_PUBLIC_HTML`.
- Relevant question-paper/answer-key links found: **0**.
- Paper/answer-key bytes fetched: **false**; source registry/database modified: **false**; candidate promotions: **0**.

This route probe is now exhausted for this fixed path set; do not repeat it without a specific new official evidence lead. It did not resolve Phase 2.2. In the post-deploy rerun of PR workflow [#40695933968](https://github.com/snchat78-svg/AI-COMP/actions/runs/40695933968), after PR #96 had reached Render, Jan Soochna `/robots.txt` returned HTTP **200** with Content-Type **`text/html`**. The strict probe reports `ROBOTS_UNAVAILABLE` / `FETCH_ERROR` / `content_type_not_allowed` and does not inspect `/Services` or `/Scheme`. The result is now precise: the endpoint is returning an HTML document, not a plain-text robots file. Do not parse the HTML as robots.txt or weaken the MIME gate.

The registered RSSB/RPSC official hosts remain TCP/TLS blocked while the general HTTPS control works. No official paper bytes/provenance/hash were obtained and the persisted candidate count remains 0. Continue to keep Phase 2.2 **BLOCKED**, Phase 6.56 **IN_PROGRESS**, Phase 6.57 **PLANNED**, and Phase 6.58 **BLOCKED**. No contact attempts, proxies, DNS overrides, unsafe TLS or unofficial mirrors.


## Current source-route findings after PR #96 deployment — 28 October 2026

PR [#96](https://github.com/snchat78-svg/AI-COMP/pull/96) merged as `9284de26048a1299b68273c1d97112cbbef40ada`; Render deployment `dep-dbgvf9qvcj2c73dtra60` is live. Exact-head pytest and API container build succeeded in [run #40695933838](https://github.com/snchat78-svg/AI-COMP/actions/runs/40695933838). The post-deploy live diagnostic rerun is [#40695933968](https://github.com/snchat78-svg/AI-COMP/actions/runs/40695933968).

Current fixed-host outcomes:
- `RSSB_OFFICIAL` (`rssb.rajasthan.gov.in`): DNS OK, IPv4 TCP timeout; TLS was not reached.
- `RSSB_LEGACY_OFFICIAL` (`rsmssb.rajasthan.gov.in`): DNS OK, TCP passes, certificate-validated TLS fails with `SSLError`; no TLS weakening is allowed.
- `RPSC_OFFICIAL` (`rpsc.rajasthan.gov.in`): IPv4 TCP timeout and IPv6 TCP failure; TLS was not reached.
- Fixed general control `example.com`: IPv4 TCP and certificate-validated TLS pass, showing the runner's general HTTPS path is working; this is not proof of why the official hosts fail.

An online metadata search surfaced official-domain paper leads such as RSSB Question Booklet PDFs under `https://rssb.rajasthan.gov.in/storage/questionpaper_item/1755761309.pdf` and `https://rssb.rajasthan.gov.in/storage/questionpaper_item/1730895562.pdf`, RPSC static question-paper PDFs under `https://rpsc.rajasthan.gov.in/Static/PreviousQuestionPaper/`, and the legacy RSSB public archive page `https://rsmssb.rajasthan.gov.in/show_archived?menuName=Xj4lCb9vGxpQnfLs%2FxlZ2g%3D%3D`. These are **source leads only** from public search indexing: the application has not fetched, hashed, provenance-checked or registered them. The RSSB/RPSC host-level TCP/TLS failures above currently prevent using those URLs in the existing ingestion pipeline.

Current conclusion: Recruitment Portal public indexes are readable but expose 0 question-paper/answer-key links; Jan Soochna robots path returns HTML not plain text; direct RSSB/RPSC paths fail normal validated connectivity. Phase 2.2 remains **BLOCKED** with 0 persisted official paper candidates. Next task is to identify a directly linked, official alternative host/endpoint with normal TLS and reachable bytes, not to ingest search snippets, bypass robots, use an unofficial mirror or override DNS/TLS. No email or phone call has been made.


## Official RBSE examination-paper archive lead — 30 October 2026

A public search surfaced the Rajasthan Board examination-paper index at [RBSE Examination Papers 2025](https://rajeduboard.rajasthan.gov.in/books/PAPERS-2025/index.htm). Its indexed page lists 2025 Secondary and Senior Secondary papers, including Senior Secondary Geography, Physics, Chemistry and Biology. This is a **school-board paper/content lead**, not an RSSB/RPSC recruitment-exam source; do not mix its exam identity or question appearances into the RSSB/RPSC history.

The Senior Secondary Geography link resolves in the index to `https://rajeduboard.rajasthan.gov.in/books/PAPERS-2025/SRS/SS-14.pdf`, but an attempted online fetch timed out. The same inspection could not retrieve `robots.txt`. Therefore no paper bytes, response headers, PDF metadata, SHA-256, reuse terms or source provenance were verified; no candidate was registered or promoted.

This increment adds only the fixed `RAJASTHAN_BOARD_QUESTION_PAPERS_CONTROL` to the separate `government_portal_controls` diagnostics lane. It probes DNS, TCP and certificate-validated TLS for the RBSE host from the GitHub runner and, after deployment, Render. It does not fetch the index, request `robots.txt`, download a paper, write the database, modify the official source registry, or satisfy the official-source gate.

Decision gate:
- If standard DNS/TCP/validated TLS fails, stop this route; do not retry by changing DNS, proxying, or weakening TLS.
- If connectivity passes, the next increment must inspect the fixed index and `robots.txt` under the published access rules, then verify source identity, terms/reuse conditions, the complete PDF bytes and digest before any registration.
- Even after a successful RBSE document fetch, keep its exam body/profile distinct from RSSB and RPSC. It can contribute to an explicitly supported school-board content track only after product-scope and syllabus mapping review.

Phase 2.2 remains **BLOCKED**; this is an online route investigation, not source ingestion or phase completion. Phase 6.56 remains **IN_PROGRESS**, Phase 6.57 **PLANNED**, and Phase 6.58 **BLOCKED**. No call, email, proxy, DNS override, unsafe TLS, or unofficial mirror is used.


## RBSE host connectivity confirmed; robots-first public-index probe — 30 October 2026

PR [#100](https://github.com/snchat78-svg/AI-COMP/pull/100) merged as `d6a26219aad6462c87ff01ecf2a06bee2f1c8195`; Render deployment `dep-dbi3k5ivcj2c73c4ieg0` is live. Exact-head backend tests and API container build passed in [PR run #41014567464](https://github.com/snchat78-svg/AI-COMP/actions/runs/41014567464). The PR source-health diagnostic [#41014567529](https://github.com/snchat78-svg/AI-COMP/actions/runs/41014567529) passed.

The new fixed control `RAJASTHAN_BOARD_QUESTION_PAPERS_CONTROL` reports DNS OK, IPv4 TCP PASS and certificate-validated TLS PASS from the GitHub-hosted runner and the deployed Render runtime (main cross-runtime run [#41014716960](https://github.com/snchat78-svg/AI-COMP/actions/runs/41014716960); post-deploy Render source-health run [#41014717223](https://github.com/snchat78-svg/AI-COMP/actions/runs/41014717223)). This confirms connectivity only. It does not yet show robots permission or an application-fetched page/PDF. The browser's direct `/robots.txt` request was inaccessible in the available web reader, so no assumption is made about its HTTP status or rules.

The next small increment adds `probe_rbse_archive_route` and a fixed read-only API diagnostic:
- Request only `https://rajeduboard.rajasthan.gov.in/robots.txt` first, using standard certificate-validated HTTPS and a bounded response size.
- Accept a 200 robots response only as `text/plain`; parse and honor the most-specific matching AI-COMP rule. A network/TLS error, malformed media type, 403/429/5xx, or any other non-200/non-404 response remains fail-closed.
- Only an explicit robots HTTP 404 (file not published) permits inspection of the single fixed path `/books/PAPERS-2025/index.htm`, under the narrowly scoped RFC 9309 unavailable policy. No other index paths are requested.
- Never follow redirects or any PDF links. For the fixed HTML page, report only bounded link metadata (label, host, path, same-host flag, query-present flag); query values and document bytes are not exposed.
- Keep RBSE separate from RSSB/RPSC; do not change the official source registry, DB, or candidate counts.

Even if the index yields links, a later controlled step must fetch the actual paper through the existing protected workflow, calculate SHA-256, verify source provenance and reuse conditions, and keep the RBSE board identity distinct. Phase 2.2 remains **BLOCKED** until approved bytes and provenance produce real persisted candidates. Phase 6.56 remains **IN_PROGRESS**, Phase 6.57 **PLANNED**, and Phase 6.58 **BLOCKED**. No calls/emails, proxy, DNS override, unsafe TLS, or mirror.


## RBSE robots decision for each linked PDF and reuse-rights hold — 30 October 2026

The post-deploy Render run [#41015710994](https://github.com/snchat78-svg/AI-COMP/actions/runs/41015710994), step “Query fixed RBSE 2025 paper archive route diagnostic”, returned the final successful report:
- robots: HTTP 200, `text/plain`, status `READ`;
- exact fixed index `/books/PAPERS-2025/index.htm`: robots allowed, HTTP 200 and `READ_ONLY_PUBLIC_HTML`;
- the parser found 200 PDF link records within its configured maximum of 200;
- no PDF bytes fetched, no source registry or database change, and zero candidate promotions.

This proves permission to inspect the index only. It is not blanket permission to fetch its PDF children. The official RBSE website main page currently exposes a “Legal Disclaimer” saying the site information is provided for informational purposes and is not binding on the Board; this is not a reproduction or redistribution licence. The index itself did not surface a paper-specific reuse licence. No verified RBSE copyright/reuse permission for republishing examination-paper PDFs in AI-COMP has been established. Therefore **do not fetch, store, display, mirror, extract or redistribute PDF contents in the app yet**. Continue to retain only the official link metadata and source attribution pending a clear applicable licence/permission. Do not contact the Board; the user has explicitly ruled out calls and email.

This increment adds per-PDF robots evaluation to the route probe:
- With a valid HTTP 200 `text/plain` robots file, evaluate every discovered same-host PDF URL using the same most-specific Allow/Disallow logic. Report `PDF_ROBOTS_ALLOWED_NOT_FETCHED` only when that exact PDF path is allowed; report `PDF_BLOCKED_BY_ROBOTS` when disallowed.
- If robots is absent with exact HTTP 404, the documented exception still permits only the single fixed HTML index. Each PDF link is `PDF_ROBOTS_NOT_EVALUATED`; no PDF access is authorized by this exception.
- External/out-of-scope links remain un-followed. No PDF request is made under any outcome.

Next gate: inspect the actual final per-PDF robots decisions from the live Render report, then determine whether a paper-specific reuse licence or compatible public reproduction policy exists. If reuse permission remains unverified, do not download/republish papers; continue with permitted metadata and separately authored one-liner content. Phase 2.2 remains **BLOCKED** because no approved paper bytes/provenance/hash and no persisted official candidates exist. RBSE remains a school-board content track distinct from RSSB/RPSC competitive-exam history. Phase 6.56 **IN_PROGRESS**, Phase 6.57 **PLANNED**, Phase 6.58 **BLOCKED**.


## Per-PDF robots results confirmed on the new Render deployment — 30 October 2026

PR [#102](https://github.com/snchat78-svg/AI-COMP/pull/102) is merged as `bf7586f907861796f796744bc5a3ef5a365773a9`. Exact-head PR test run [#41016548039](https://github.com/snchat78-svg/AI-COMP/actions/runs/41016548039) passed the full backend suite (597 tests) and API container build. The Render deployment `dep-dbi3tj2vcj2c73c4r3fg` is live.

The post-deploy source-health workflow [#41016698624, attempt 2](https://github.com/snchat78-svg/AI-COMP/actions/runs/41016698624) re-ran after Render became live. Its RBSE route step succeeded and the final report showed:
- robots HTTP 200 / `text/plain`, parsed; fixed index path allowed;
- one fixed HTML index, HTTP 200;
- the first 20 PDF-link records printed in the workflow summary each have `robots_allowed=True` and `PDF_ROBOTS_ALLOWED_NOT_FETCHED`. The API report remains capped at 200 link records; the GitHub workflow summary deliberately prints the first 20 only. Do not infer that the entire catalogue has been audited from those 20 lines.
- no PDF bytes fetched, no database/source-registry change, zero candidate promotions.

The overall source-health workflow is still red at its independent existing gate requiring at least one *registered competitive-exam source* to complete TCP+validated TLS. RBSE passing its own route check does not satisfy that RSSB/RPSC gate. The official source-research workflow [#41016698619](https://github.com/snchat78-svg/AI-COMP/actions/runs/41016698619) still fails closed with 0 persisted candidates because RSSB/RPSC source retrieval remains unavailable.

**Next decision:** robots permission is now known for the first 20 same-host PDF links, but a paper-specific reuse licence/permission is still not verified. The official Board main page's informational Legal Disclaimer does not grant reproduction rights. Keep all PDF bytes un-fetched and unpublished. The product may retain attributable official links/metadata as an external-reference lane only after the app's external-link policy is defined; do not treat links as stored/verified paper candidates or question-history evidence.

Phase 2.2 remains **BLOCKED**; Phase 6.56 **IN_PROGRESS**, Phase 6.57 **PLANNED**, and Phase 6.58 **BLOCKED**. RBSE remains a distinct school-board source, never RSSB/RPSC competitive-exam history.
