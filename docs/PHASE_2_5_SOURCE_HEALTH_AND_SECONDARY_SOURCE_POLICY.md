# Phase 2.5 — Official Source Health and Secondary Source Admission

## Purpose

The live official-source research runs on 18–20 October 2026 failed before discovery could persist candidates. The observable failures were an RSSB request timeout and an RPSC `Network is unreachable` error. A green processing or verification workflow with zero selected records is not evidence of a populated question bank.

The `source_health` preflight reports DNS availability and certificate-validated TLS connectivity separately for IPv4 and IPv6. It connects only to registered official source hosts, performs no page fetch, does not bypass TLS verification, and does not alter the crawler's robots, terms, redirect, or host checks. It is diagnostic only; the research CLI still decides whether discovery succeeded.

## Secondary source admission rule

A secondary source must not be added to automated ingestion merely because its page is public or appears in a search result. Before enabling a source for automated retrieval, record and review all of the following:

1. A stable canonical source identity and a known publisher/editor.
2. A current `robots.txt` decision for the exact paths to be requested.
3. Terms of use that permit the intended automated access.
4. Sufficient reuse/storage/extraction rights for the intended use, or explicit permission/licence from the rights holder.
5. Public, non-login URLs with no paywall, CAPTCHA, signed-session dependency, or technical access-control bypass.
6. Source provenance on every candidate; secondary data must never satisfy the official-source verification gate.

A robot rule permitting a URL is not itself a copyright licence or a grant to reproduce content. If terms or rights are unclear, keep the source disabled and request permission instead of guessing.

## Source review for Rajasthan previous-paper discovery

| Candidate | Public evidence reviewed | Automated ingestion decision |
| --- | --- | --- |
| Testbook | `https://testbook.com/terms-of-service` and `https://testbook.com/acceptable-use-policy` prohibit scraping, robots/data-mining or similar automated extraction of service content. | **Do not crawl or download** for AI-COMP without express written permission. |
| Adda247 | `https://www.adda247.com/robots.txt` publishes path rules. Its Terms of Use at `https://www.adda247.com/term-conditions.html` restrict unauthorised copying, downloading, modification, distribution and other uses of platform content. | Robots alone does not authorise content reuse. **Do not ingest papers** unless permission/licensing for this use is confirmed. |
| PreviousPrashna | `https://previousprashna.com/about` describes itself as an independent tool using papers published by RPSC/RSSB. The current terms/robots could not be reliably confirmed during review; its terms route returned HTTP 403 to the research browser. | **Keep disabled** until current robots, terms and reuse permission are reviewed. |

Official RSSB/RPSC remains the first choice. A secondary fallback can be added later when a source satisfies the admission checklist. When enabled, fetched secondary documents may be retained as secondary evidence and extracted as question candidates, but they must remain `SECONDARY / LIKELY`; they cannot create verified exam appearances or imply an official answer key.

## Acceptance criteria

- The preflight reports DNS status, IPv4/IPv6 address counts, and per-family TLS result without logging raw IP addresses or secret values.
- TLS verification remains enabled.
- Source health diagnostics do not change the discovery or verification trust boundary.
- A fully blocked official-source run remains a failed research run.
- No third-party secondary source is activated before access and reuse rights are clear.
- After official source connectivity is restored, validate: discovery candidates persisted → paper processing extracted candidates → answer-key reconciliation → source-backed history records. Zero-record runs must not be described as end-to-end success.
