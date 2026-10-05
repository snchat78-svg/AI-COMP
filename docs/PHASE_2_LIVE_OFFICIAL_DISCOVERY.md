# Phase 2 — Live Official Source Discovery Orchestrator

Pipeline:
Source Registry -> robots.txt -> sitemap/sitemap-index -> RSS/Atom -> official archive pages -> policy/robots/domain filtering -> PaperCandidate.

Safety:
- research, robots and terms/access policy must all be enabled.
- missing robots.txt fails closed.
- HTTP(S) and the registered host are required.
- SourceRecord.allowed_paths remains authoritative.
- sitemap traversal is bounded by CrawlPolicy.max_depth.
- candidate discovery is bounded by max_documents.
- network access is injected through HttpTransport for deterministic tests.
- external-domain links are never followed.
- configured discovery seeds are only fallbacks; robots Sitemap declarations are also honored.

Implemented in this increment:
- live robots.txt retrieval and parsing
- sitemap declarations
- sitemap.xml and sitemap-index traversal
- RSS/Atom link extraction
- official archive HTML link extraction
- bounded, policy-gated candidate generation
- injectable transport and deterministic tests

Deferred:
- scheduled crawling
- retry/backoff persistence
- automatic fetch/storage execution after candidate discovery
- PDF/OCR extraction
- question extraction and answer-key pairing