# Phase 2.6 — Mumbai Regional Official-Source Probe

## Why this step exists

The official research workflow and the deployed Render service both resolve the registered RSSB/RPSC hostnames in DNS, but their outbound TCP connections to port 443 fail before a TLS handshake can start. This is not yet evidence that a site blocks the crawler specifically; it only shows that those two cloud execution environments could not establish a connection during the recorded probes.

The existing Supabase project uses the Mumbai `ap-south-1` database region. Supabase Edge Functions support explicit regional invocation through the `x-region` request header. This phase adds a diagnostic-only function invoked in `ap-south-1` to check whether a different execution region can obtain an HTTP response from each official host.

## Strict scope

The function requests exactly:

- `https://rssb.rajasthan.gov.in/robots.txt`
- `https://rpsc.rajasthan.gov.in/robots.txt`

It accepts only `all`, `RSSB_OFFICIAL`, or `RPSC_OFFICIAL`; accepts no URLs; follows no redirects; times out each request; cancels response bodies without reading or storing their content; writes no database rows; and never downloads a question paper or answer key. HTTP responses such as 403 or 429 are reported as responses, not as permission to crawl. A connectivity result is not an authorization or a robots/terms determination for any archive path.

The Edge Function remains JWT-protected. The GitHub workflow deploys only this function when its source/config changes, then invokes it with `x-region: ap-south-1` and reports the actual `SB_REGION` value. Unit tests use injected fake fetch functions and do not make Internet requests.

## Deployment requirement

Automated deployment requires a Supabase Management API access token. The repository does not assume this token exists, and its value must never be committed or shared in chat. Set a GitHub Actions repository secret named `SUPABASE_ACCESS_TOKEN` in **Settings → Secrets and variables → Actions**. The existing `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` secrets are also required to invoke the JWT-protected diagnostic. If any are missing, the workflow records that deployment was skipped instead of claiming a regional probe passed.

## Acceptance criteria

1. Deno type-check and unit tests pass without network access.
2. The function executes in `ap-south-1`, confirmed by its `SB_REGION` output.
3. Per-source results show HTTP response status or a safe timeout/network error class, with no raw IPs, secret values, or exception messages.
4. A status of 403/429 or a redirect is not bypassed. No redirect is followed.
5. Zero paper candidates remain zero until a separate, compliant paper-discovery process actually persists candidates.
6. If Mumbai also cannot obtain an HTTP response, stop trying alternate egress/proxy techniques and pursue official-site owner support or a clearly licensed source.

## Next step after probe

- **Reachable from Mumbai:** design a separate, tightly scoped regional discovery/download handoff that preserves the existing Python downloader, private storage, hashing, OCR, answer-key pairing, and verification pipeline. Do not place answers into the verified pool at discovery time.
- **Still unreachable:** use the returned error/status for a network/source-owner escalation. Do not loosen TLS, ignore robots, or scrape secondary content that disallows automated extraction.
