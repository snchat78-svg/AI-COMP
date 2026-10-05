# Phase 4 — PostgreSQL Persistence Foundation

## Purpose

This migration is the first persistence layer for the Phase 4 matching/history model. It does not replace the existing domain objects or in-memory repositories.

Migration: database/migrations/0001_phase4_core.sql

## Stored layers

The schema preserves the current pipeline boundaries:

- Registry: conducting bodies, exams, paper categories, sources, source verifications.
- Research: paper candidates, papers, fetched documents, normalized documents.
- Extraction: questions and ordered options.
- Matching: concepts, question concepts, question matches, match evidence.
- History: canonical exam appearances and source provenance.
- Semantic search: embedding models and question embeddings.

## Historical integrity

`exam_appearances` represents a real exam occurrence.

A unique database identity is enforced by:

- exam ID
- year
- shift (with NULL treated as empty)
- question number

Copied versions from additional websites belong in `appearance_sources`. This prevents source-copy count from becoming exam-appearance count.

`verification_id` is mandatory on an appearance, keeping historical evidence attached to the source-verification model established in Phase 1.

## Embedding readiness

The schema enables `pgvector` and stores embeddings independently from matching logic.

The application does not hard-code a provider, model, or dimension. `embedding_models` identifies provider/model/version and `question_embeddings` stores the vector for that model.

An approximate HNSW index is intentionally not created yet because production indexing depends on the selected embedding dimensions/model. pgvector supports vector columns and HNSW/IVFFlat indexes; the later adapter can add a dimension-specific index once the embedding model contract is frozen. citeturn454096search1turn454096search3

## Why the application contracts stay DB-neutral

The existing `AppearanceRepository` and registry protocols remain unchanged. PostgreSQL is an infrastructure implementation, not a new domain dependency.

This keeps tests deterministic and allows the same domain services to work with `InMemoryAppearanceRepository` during unit tests.

## Next implementation step

Add PostgreSQL repository adapters behind the existing repository contracts, with parameterized SQL, transaction boundaries, idempotent writes, and read-back mapping into the existing dataclasses.

Do not connect live production credentials or external embedding providers at this stage.