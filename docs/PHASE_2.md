# Phase 2 — Paper Research Engine

## Goal
Turn Phase 1's source registry into a controlled paper-research pipeline.

Flow:

Source Registry
-> policy validation
-> candidate discovery
-> fetch
-> SHA-256 content identity
-> duplicate detection
-> storage metadata

## Safety contract
- Only HTTP(S) URLs are accepted.
- Candidate URLs must stay on the registered source domain.
- Registered source path restrictions are enforced.
- Research must be enabled by policy.
- robots/terms flags remain mandatory safety gates.

## Current implementation
- Paper candidate model
- Document model
- Controlled discovery
- URL policy validation
- Content-hash based fetch/storage
- Duplicate detection
- Unit tests

## Deferred
- Real site crawling
- robots.txt retrieval/interpretation
- sitemap/RSS discovery
- PDF/OCR extraction
- answer-key pairing
- question extraction

These are later Phase 2 increments and must be implemented without bypassing the source registry.
