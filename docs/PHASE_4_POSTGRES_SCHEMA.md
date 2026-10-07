# Phase 4 — PostgreSQL Persistence Foundation

## Purpose

Phase 4 now has a database-backed persistence boundary without coupling domain objects to PostgreSQL.

The database layer is split into small adapters:

- registry
- research/document
- paper
- question
- answer-key entries
- answer resolutions
- concepts
- matches
- exam appearances/history
- embeddings

The in-memory repositories remain available for fast deterministic unit tests.

## Migration chain

Migrations live under `database/migrations/` and are applied in numeric order:

- `0001_phase4_core.sql`
- `0002_phase4_answer_keys.sql`
- `0003_phase4_answer_resolution.sql`
- `0004_phase4_match_pair_integrity.sql`

`MigrationRunner` records version, filename and SHA-256 checksum in `schema_migrations`. A migration that was previously applied with different content is rejected instead of silently changing the database schema.

## Stored lineage

The persisted lineage is:

`PaperCandidate → PaperRecord → FetchedDocument → NormalizedDocument → QuestionCandidate → Match/Concept → ExamAppearance`

Answer-key text is stored separately from resolved answers:

`AnswerKeyEntry → AnswerKeyResolver → AnswerResolution`

This preserves the distinction between:

- what the source document literally contained
- what option that source key maps to
- whether that source itself is authoritative

The resolver is deterministic. It does not invent an answer when the key cannot be mapped to an extracted option.

## Historical integrity

`exam_appearances` represents a real exam occurrence.

The database enforces a canonical occurrence identity using:

- exam ID
- year
- shift
- question number

Copies discovered on additional websites are stored as provenance in `appearance_sources` rather than as additional historical appearances.

Verification remains mandatory on a historical appearance through `verification_id`.

Therefore the historical count cannot legitimately mean "number of websites containing the question".

## Matching persistence

`question_matches` stores the relationship type and confidence.

`match_evidence` stores the deterministic or model-produced evidence entries.

The application still keeps the semantic decision logic outside the database. PostgreSQL stores the decision and its evidence; it does not decide whether two questions are equivalent.

## Question persistence

Questions and options are separate tables so option order is preserved.

A deterministic `duplicate_key` is stored for copied-question detection.

The duplicate key is indexed but not unique: different real exam occurrences may contain the same question text.

## Concept persistence

Explicit concept records are stored in `concepts`, with many-to-many question links in `question_concepts`.

Concept resolution therefore remains explicit and auditable instead of being inferred from arbitrary database keywords.

## Embedding persistence

`embedding_models` stores provider/model/version/dimension metadata.

`question_embeddings` stores the vector separately from the model metadata.

The repository validates vector dimensions before writing and provides nearest-neighbor search using pgvector cosine distance.

No provider or model is hard-coded into the matching engine.

An approximate HNSW index is intentionally deferred until the production embedding dimension/model is frozen. The current repository therefore works correctly with a sequential vector scan during the foundation stage.

## Repository contracts

The database protocols remain application-facing contracts:

- `RegistryRepository`
- `ResearchRepository`
- `PaperRepository`
- `QuestionRepository`
- `AnswerKeyRepository`
- `AnswerResolutionRepository`
- `ConceptRepository`
- `MatchRepository`
- `AppearanceRepository`
- `EmbeddingRepository`

`PostgresUnitOfWork` groups the adapters behind one connection transaction. Repository-level transaction blocks become savepoints when an outer transaction is already active, allowing a higher-level operation to remain atomic.

PostgreSQL implementations can be replaced by another persistence implementation without changing the domain matching rules.

## CI

The test workflow installs the test and PostgreSQL extras and starts an isolated pgvector PostgreSQL service.

The integration test exercises the full Phase 4 persistence chain:

`registry → research/document → question → answer-key → answer-resolution → concept → match → appearance deduplication → history → embedding read/search`

The normal unit suite remains runnable without a local database because the integration test skips when `AI_COMP_DATABASE_URL` is not configured.

## Current Phase 4 boundary

Phase 4 is not yet claiming:

- a complete live nationwide question database
- a production embedding provider
- automatic historical equivalence from embeddings alone
- complete official answer verification for every paper
- all-government-exam coverage

Those require the next ingestion, verification and scale layers.

## Next step

After Phase 4 persistence is green in CI, freeze these contracts and move to the next bounded layer: production ingestion orchestration and the master-question persistence flow. No Phase 5 test-generation logic should bypass verified historical evidence.
