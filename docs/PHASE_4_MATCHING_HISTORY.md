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

Exam appearances are also deduplicated by:
- exam ID
- year
- shift
- question number

This prevents copied source records from inflating the historical count.

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

## Question History Aggregator

QuestionHistoryAggregator converts appearance records plus explicit QuestionMatch relationships into a bounded history view.

The view keeps these relationships separate:
- exact_appearances
- rephrased_appearances
- same_concept_appearances
- related_topic_appearances

Only EXACT and REPHRASED are historical equivalents for the verified appearance count. SAME_CONCEPT and RELATED_TOPIC remain informative relationships and are not counted as repeats of the same question.

The aggregation also deduplicates the same real exam occurrence, so the same question copied to multiple source sites does not become multiple exam appearances.

HistoryService.build_history() connects the repository to this aggregator by loading the target question and the directly matched question IDs.

## Verified-history rule

Only VerificationStatus.VERIFIED contributes to the bounded verified appearance count.

The UI wording is:

"Verified database में N appearances मिले"

It must not claim:

"यह question सभी सरकारी परीक्षाओं में कुल N बार आया है."


## History Query API

HistoryService.query_history_view() adds read-time filtering without changing the underlying appearance records or matching relationships.

Supported filters:
- exam_id
- conducting_body_id
- year
- shift
- verification_status
- verified_only

verified_only=True returns only records backed by VerificationStatus.VERIFIED.

Filtering is applied after relationship classification, so EXACT, REPHRASED, SAME_CONCEPT, and RELATED_TOPIC remain separate buckets.

## Phase 4 implementation strategy

The matching layer is dependency-injected. Embeddings and concept resolution can later be connected to pgvector/LLM services without changing deterministic contracts.

No real embedding provider is hard-coded in this phase.

## Next step

Design the PostgreSQL schema and persistence adapter for questions, documents, papers, exam appearances, verification records, matches, and embeddings while preserving the current database-neutral contracts.
