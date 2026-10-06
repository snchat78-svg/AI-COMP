# Phase 6 — AI Material Analysis

## Phase 6.1 — Material intake and normalized material foundation

Phase 6 reuses the Phase 2 document-processing foundation instead of creating a second OCR/PDF pipeline.

User input:

Photo / PDF / Notes
-> SHA-256 content identity
-> content-addressed storage
-> format detection
-> direct text extraction or OCR
-> existing text normalization
-> NormalizedMaterial

### Supported material types

- user text notes;
- uploaded PDF;
- uploaded image/photo.

The material contract is separate from official research papers. User material is study input only; it is not historical exam evidence.

### Content identity and duplicate handling

material_id is derived from the SHA-256 of the bytes. The same bytes uploaded under different filenames resolve to one logical material identity and one stored object.

The filename remains presentation metadata and is never part of content identity.

### OCR boundary

Photo/image input uses the existing injectable OCRAdapter.

This keeps OCR provider selection independent from the material domain. OCR output is treated as extracted text and is not automatically considered a verified fact.

### Phase 6 pipeline boundary

6.1 intentionally stops after normalized text.

Next layers are independent:

NormalizedMaterial
-> Content Understanding
-> Concept Extraction
-> Important Facts
-> Verified Exam DB Matching
-> Existing Question Detection
-> AI Question Generation
-> Duplicate / Quality Control
-> Difficulty / Importance
-> Test Engine

This separation prevents AI-generated content from being confused with historical evidence.

### Non-negotiable rules preserved

1. User uploads cannot create ExamAppearance.
2. User material cannot upgrade an unverified claim into verified historical evidence.
3. AI-generated questions remain separate from observed previous-exam questions.
4. Historical claims continue to depend on the verified exam database and source records.
5. Matching will consult the existing question/master database rather than embedding historical claims inside the material model.

## Current status

Phase 6.1 implementation:

- MaterialInput
- NormalizedMaterial
- MaterialStorage
- MaterialProcessor
- note, PDF/image-compatible intake
- OCR injection
- content deduplication
- unit tests

Next: Phase 6.2 — Content Understanding + Concept Extraction + Important Facts, with explicit provider-neutral interfaces and structured outputs before connecting an actual LLM.