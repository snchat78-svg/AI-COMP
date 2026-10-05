# Phase 2 Research Pipeline

The Phase 1 Source Registry remains the single authority for research targets.

Source Registry
-> robots.txt/access gate
-> official-source discovery adapters
-> sitemap/RSS/archive candidates
-> policy/domain filtering
-> PaperFetcher
-> SHA-256 content identity
-> content-addressed DocumentStorage

Implemented in this increment:
- robots/access decision contract
- sitemap XML parsing
- RSS/Atom-style link parsing
- explicit archive-link adapter
- candidate filtering
- SHA-256 identity
- content-addressed local storage
- tests

Deferred:
- live network orchestration
- automatic sitemap/RSS retrieval
- scheduled crawling
- PDF/OCR extraction
- question parsing

Live network access must remain behind the Source Registry and access-policy gates.
