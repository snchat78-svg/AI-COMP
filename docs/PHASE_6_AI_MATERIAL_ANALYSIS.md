# Phase 6 — AI Material Analysis

## Phase 6.1 — Material ingestion

Phase 6.1 consumes Photo/PDF/Notes input, stores content by SHA-256, extracts text,
and provides OCR fallback through the existing document-processing contract.

User material is study input only. It is not official evidence and cannot create
ExamAppearance records.

## Phase 6.2 — Content understanding, concepts and important facts

Phase 6.2 defines the provider-neutral material-analysis contract:

NormalizedMaterial
-> Content Understanding
-> Proposed Concepts
-> Source-grounded Important Facts

The pipeline requires each concept/fact evidence_text to be an exact substring of
the normalized material. This is a deterministic anti-hallucination boundary.

A StaticMaterialAnalysisProvider is retained for deterministic tests and local
development.

## Phase 6.3 — Real LLM provider and structured output

Phase 6.3 connects the provider contract to Google's Gen AI SDK.

### Production provider

GeminiMaterialAnalysisProvider uses:

- environment variable GEMINI_API_KEY by default;
- model gemini-3.8-flash by default;
- high Gemini thinking level by default;
- JSON structured output validated by a closed Pydantic schema;
- one model request per material, reused for understanding/concepts/facts;
- deterministic IDs generated locally for extracted concepts/facts.

The provider deliberately does not place an API key in source code, prompts,
tests, or Git history.

### Accuracy and fail-closed rules

The provider:

1. does not truncate oversized material;
2. rejects oversized material before an API call;
3. asks the model to use only the supplied material;
4. requires exact source-substring evidence for every concept/fact;
5. rejects malformed structured responses;
6. rejects unexpected schema fields;
7. validates confidence and importance scores in the range 0..1;
8. deduplicates identical extracted concept/fact pairs;
9. never creates ExamAppearance records or historical claims.

A failed or invalid LLM response raises GeminiMaterialAnalysisError. The system
does not silently fall back to invented content.

### Dependency and runtime setup

The project pins google-genai==2.28.0 for reproducible CI and declares Pydantic
as a runtime dependency.

For local execution, provide the API key through the environment:

GEMINI_API_KEY=<secret>

Do not commit .env files or API keys.

### Structured response boundary

The SDK is asked for:

- application/json;
- the _GeminiMaterialAnalysis Pydantic schema;
- Gemini high thinking.

The application validates the returned structure again before converting it into
the Phase 6.2 domain objects. This preserves the architecture:

MaterialAnalysisProvider
-> structured LLM adapter
-> deterministic domain validation
-> later verified-database matching

The provider is therefore an implementation detail; future providers can implement
the same MaterialAnalysisProvider protocol without changing the domain layer.

### CI policy

CI runs only deterministic provider tests and does not require a live Gemini API
key. A live integration test is intentionally kept outside normal CI so builds do
not become dependent on external quota, network availability, or secret exposure.

## Historical-data separation

Nothing in Phase 6.1–6.3 promotes user material into previous-exam history.

Historical exam appearances remain governed by the Phase 4/5 verification gate:
actual official/trusted source evidence must be persisted separately.

## Next

Phase 6.4 should connect extracted concepts/facts to the verified master question
database and separate:

- exact previous-question detection;
- rephrased previous-question detection;
- same-concept matches;
- related-topic matches;

before any AI question generation is allowed.
