# Phase 1 — Source & Exam Registry

Foundation contract for the AI Competitive Exam Intelligence Platform.

## Scope
- Exam and conducting-body registry
- Official/trusted source registry
- Source priority and verification policy
- Paper category metadata
- Crawl/research policy contracts

## Non-goals
Phase 1 does not crawl the web, download papers, run OCR, call an LLM, or perform semantic matching.

## Reliability levels
- OFFICIAL: conducting-body source
- SECONDARY: trusted external source
- UNVERIFIED: source requiring verification

Historical exam claims must be backed by source records. AI memory is never evidence.

## Design principle
The registry is source-agnostic and extensible so Rajasthan can be implemented first and national exams added later without changing the domain contract.
