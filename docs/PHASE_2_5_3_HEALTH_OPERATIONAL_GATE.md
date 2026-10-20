# Phase 2.5.3 — Make Official-Source Health Operationally Honest

## Why

After Phase 2.5.1 added `RSSB_LEGACY_OFFICIAL` and Phase 2.5.2 made the Render health workflow wait for the updated registry, the live report became current. It showed:

| Official source | DNS | IPv4 TCP | IPv4 TLS | IPv6 TCP | IPv6 TLS |
|---|---|---|---|---|---|
| `RSSB_OFFICIAL` | OK | FAIL | NOT_REACHED | NO_RECORDS | NO_RECORDS |
| `RSSB_LEGACY_OFFICIAL` | OK | PASS | FAIL | NO_RECORDS | NO_RECORDS |
| `RPSC_OFFICIAL` | OK | FAIL | NOT_REACHED | FAIL | NOT_REACHED |

Research run [39408528273](https://github.com/snchat78-svg/AI-COMP/actions/runs/39408528273) subsequently reported:
- `RSSB_OFFICIAL`: outbound request timeout.
- `RSSB_LEGACY_OFFICIAL`: `UNSAFE_LEGACY_RENEGOTIATION_DISABLED` during TLS handshake.
- `RPSC_OFFICIAL`: `Network is unreachable`.
- `paper_candidates_persisted = 0`.

The source-health workflow had previously returned green whenever it could retrieve a valid report, even when every source failed to complete a certificate-validated TLS handshake. That correctly proved the diagnostic endpoint was responding, but it did not give an operationally useful pass/fail signal.

## Change

The existing `render-official-source-health` workflow now requires at least one registered official source to pass both TCP connect and certificate-validated TLS on the same address family. It still writes the DNS/TCP/TLS report to the Actions summary and job log before evaluating this gate.

- If at least one official HTTPS path is reachable, the connectivity check passes and the per-source report remains available.
- If no source passes both checks, the job fails visibly after publishing the report.
- The check does not depend on a paper candidate count; the separate discovery workflow must still persist actual candidates before ingestion is considered successful.
- The stale-registry guard from Phase 2.5.2 remains: the response must include `RSSB_LEGACY_OFFICIAL` before the workflow evaluates connectivity.

## Security boundaries

Do **not** enable unsafe legacy TLS renegotiation, disable certificate verification, use an arbitrary proxy, ignore robots.txt, allow cross-host redirects, or turn a failed official host into a verified history source. The current TLS exception is an actual blocker. Resolve it through an official endpoint that supports secure TLS or an authorized hosting/network change.

This workflow change does not download papers, change verification state, modify the database, or fabricate questions. It only makes the existing operational signal match the stated pass/fail condition.

## Validation and resume point

1. Require CI tests and Docker build to pass.
2. After merge and Render auto-deploy, inspect `render-official-source-health`. Expect it to fail until an official source supports validated HTTPS from the runtime.
3. Continue research only after the official source-health result includes at least one `TCP=PASS` + `TLS=PASS` source and the research workflow persists nonzero candidates.
4. Then run the existing paper-processing and answer-key-verification workflows in order; verify the resulting source-backed appearances and eligible test-pool count.

**Resume here:** find/establish an approved official HTTPS source endpoint reachable by the research runtime. Phases 1–2.4 have code foundations already and must not be reimplemented while this operational blocker remains.
