# Phase 4 — Matching & History Engine

## Phase 4 boundary

Phase 4 consumes structured QuestionCandidate records from Phase 3. It does not crawl the web, extract PDFs, run OCR, or generate practice questions.

## Ordered matching

1. EXACT — normalized stem and options match.
2. REPHRASED — injected embedding similarity crosses an explicit threshold.
3. SAME_CONCEPT — an explicit concept resolver assigns the same concept ID.
4. RELATED_TOPIC — reserved for a future relationship and is never counted as the same historical question.

A semantic match is a candidate relationship, not proof that two records are the same exam appearance.

## Duplicate rule

A copied question found on multiple websites is a question/document duplicate, not multiple exam appearances. Duplicate detection therefore lives separately from ExamAppearance.

## Historical appearance

ExamAppearance is the separate entity linking a question to an actual exam occurrence. It contains:

- exam ID
- conducting body
- year/date/shift
- question number
- original question/options
- answer when known
- paper ID
- source URL
- verification record
- match type

The source registry and verification model from Phase 1 remain authoritative.

## Verified-history rule

Only VerificationStatus.VERIFIED contributes to the bounded verified appearance count.

The UI wording must remain:

"Verified database में N appearances मिले"

It must not claim:

"यह question सभी सरकारी परीक्षाओं में कुल N बार आया है."

## Phase 4 implementation strategy

The matching layer is dependency-injected. Embeddings and concept resolution can later be connected to pgvector/LLM services without changing deterministic contracts.

No real embedding provider is hard-coded in this phase.

## Next step

Build the persistence adapter and candidate-pair indexing layer, then connect verified paper/question metadata from Phase 2/3 into ExamAppearance creation.
