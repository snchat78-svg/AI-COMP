# Phase 3 Question Extraction

Phase 3 consumes only the output contract from Phase 2:

NormalizedDocument
-> QuestionExtractionPipeline
-> QuestionCandidate
-> QuestionOption
-> separate AnswerKeyEntry
-> Phase 4 matching/history

## Implemented

- QuestionCandidate is provenance-aware through document_id and document_sha256.
- Question numbering and source line ranges are retained.
- Question stem and raw source text are retained for auditability.
- English option labels (A-H) are supported.
- Hindi option labels (क-झ) and numeric option labels are supported.
- Multi-line question stems are preserved.
- Multi-line option text is continued into the same option.
- Incomplete questions are not promoted to candidates when they do not meet the configured minimum option count.
- Answer-key lines are extracted separately as AnswerKeyEntry; the question parser never invents or assigns an answer.
- The extraction pipeline accepts NormalizedDocument and has no dependency on live crawling or URL fetching.

## Architecture boundary

Phase 1 owns source, exam, and evidence contracts.

Phase 2 owns discovery, fetching, SHA-256 storage, document metadata, format detection, text extraction, OCR fallback, and normalization.

Phase 3 owns deterministic segmentation of observed normalized text into question candidates.

Phase 4 will own exact, semantic, and concept matching, duplicate detection, and historical appearance records.

Phase 5 can add AI-assisted extraction for difficult layouts, but AI output must remain traceable to the source document and must not manufacture historical evidence.

## Deliberately deferred

- semantic duplicate detection
- rephrased and same-concept matching
- answer-key verification
- exam-history appearance counts
- question classification and topic tagging
- AI-generated questions
- OCR engine selection
