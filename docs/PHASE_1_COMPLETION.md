# Phase 1 Completion Contract

Phase 1 establishes the stable foundation for source/exam research.

## Completed
- Conducting body and exam domain models.
- Paper category model.
- Source registry with official/secondary/unverified priority.
- Crawl safety policy contract.
- Source verification/evidence model.
- Database-neutral registry snapshot.
- Repository protocol for future PostgreSQL persistence.
- Rajasthan seed registry for RSSB/RPSC foundation.
- Regression tests for registry validation, verification rules and persistence contracts.

## Historical evidence rule
A historical exam claim is considered verified only when its supporting verification record has status `VERIFIED`. Secondary and unverified records remain distinguishable and cannot be silently promoted.

## Explicitly deferred to later phases
- Web crawling/discovery
- Paper downloading
- File hashing and document deduplication
- PDF/OCR extraction
- Question extraction
- Answer-key pairing
- Exact/semantic/concept matching
- LLM integration

## Phase 1 exit condition
The domain and persistence contracts are stable enough that Phase 2 can implement paper research without changing the core source/exam semantics.
