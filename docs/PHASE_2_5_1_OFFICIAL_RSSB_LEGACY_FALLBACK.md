# Phase 2.5.1 — Official RSSB Legacy-Host Discovery Fallback

## Why this increment exists

The 20 October 2026 Render source-health workflow showed DNS success but IPv4 TCP timeouts for the current RSSB and RPSC hosts; TLS was not reached. The official-source research run persisted zero paper candidates. The subsequent scheduled paper-processing and answer-key verification jobs completed with zero selected records, which is an empty-queue result—not a successful populated question bank.

Officially indexed pages on the Rajasthan Staff Selection Board's legacy domain, `https://rsmssb.rajasthan.gov.in/`, still expose separate Question Papers and Answer Key archive listings. Examples reviewed on 20 October 2026:

- [Official Question Papers archive listing](https://rsmssb.rajasthan.gov.in/show_archived?menuName=Xj4lCb9vGxpQnfLs%2FxlZ2g%3D%3D&theme=Default)
- [Official Answer Key archive listing](https://rsmssb.rajasthan.gov.in/show_archived?menuName=AGDAnN3xlANlxQ9BZvzaeg%3D%3D&theme=Red)

The exact archive query identifiers can change and the public browser returned an error when opening those indexed deep links directly. For that reason, this increment does **not** hard-code those opaque query identifiers as mandatory fetch URLs. It registers the separate official host and starts from its current navigation instead. A live fetch and current robots response are still required before any candidate can be persisted.

## Implemented in this increment

- Add `RSSB_LEGACY_OFFICIAL` as a separate `OFFICIAL_WEBSITE` source for the same canonical `RSSB` conducting body.
- Limit candidate URLs for this host to the official board's `/page`, `/show_archived`, `/link_to_external_file/`, and `/Static/` paths.
- Let the existing controlled crawler follow the homepage's Question Papers and Answer Key navigation links instead of depending on hard-coded archive menu IDs.
- Include the new registry entry in the existing fixed-host DNS/TCP/certificate-validated TLS report.
- Trigger the deployed Render source-health workflow when the seed registry changes.
- Add unit tests for source registration, robots-respecting archive traversal, title preservation, allow-listed paths, and diagnostic reporting.

No new database schema is introduced. Existing idempotent registry synchronization will add the source row to PostgreSQL during the next official-source research run.

## Trust and access boundaries

- This is an official-host fallback, not a third-party secondary source.
- The crawler must receive an accessible `robots.txt`, respect its rules, keep same-host redirect checks enabled, and apply the source allow-list. Missing/unavailable robots or a disallowed path must fail closed; do not bypass those restrictions.
- Source registration, an HTTP 200 response, a file hash, or OCR output does not by itself establish an exam appearance or an answer.
- Only explicit exam/year/shift metadata and the existing official answer-key verification rules can create supported history. Ambiguous matches remain in review.
- This change does not repair general outbound network restrictions. The new domain must pass the deployed health probe and the live discovery step before this fallback can be considered operational.
- No learner must upload previous papers manually; this increment continues the automatic research pipeline.

## Validation and exact next operation

CI must pass the full Python/PostgreSQL suite, Docker image build, and Flutter analyze/tests/APK build triggered by the documentation checkpoint already merged on main as appropriate.

After this increment merges:

1. Read `render-official-source-health` and confirm a row for `RSSB_LEGACY_OFFICIAL`, including DNS, TCP and TLS outcomes.
2. Inspect `official-source-research`: require a successful source outcome and a nonzero `paper_candidates_persisted` count before proceeding. If robots is unavailable or the host connection still fails, record the blocker—do not pretend discovery succeeded.
3. If candidates persist, run the existing paper-processing and official-answer-key-verification workflows in order. Compare fetched/extracted/paired/appearance counts; a green workflow with zero rows does not finish this phase.
4. Confirm the eligible learner question pool contains actual accepted, answer-verified, non-duplicate questions before testing from the APK.

This is a targeted Phase 2.5 follow-up, not a restart of Phase 1 or a replacement for Phases 2.2–2.4.
