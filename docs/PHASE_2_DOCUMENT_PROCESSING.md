# Phase 2 Document Processing

The research pipeline now continues after content-addressed storage:

DocumentStorage
-> Stored Document Metadata
-> PDF / HTML / Image Detection
-> Text Extraction
-> OCR fallback
-> Normalized Document
-> Phase 3 Question Extraction

## Implemented

- DocumentStorage.read() verifies the stored bytes against SHA-256 before processing.
- StoredDocumentMetadata records source, hash, size, declared format, and detected format.
- Metadata is stored separately under the content-addressed storage root as JSON.
- Detection prefers binary signatures over HTTP declarations so an incorrect MIME type does not silently change the actual format.
- PDF extraction uses pypdf.
- HTML extraction uses the Python standard library and excludes script, style, template, and title content.
- Plain text extraction is UTF-8 tolerant.
- Image documents use an injected OCR adapter.
- PDFs with no extractable text can fall back to the OCR adapter.
- Normalization applies Unicode NFKC, stable line endings, whitespace cleanup, and blank-line limits.
- OCR remains an interface so a real OCR engine can be added without changing the processing contract.
- PaperResearchPipeline.process_fetched() connects fetched documents to the processing layer.

## Safety boundaries

- Stored content remains immutable and content-addressed by SHA-256.
- Processing reads stored bytes; it does not re-fetch source URLs.
- Actual detected format is persisted separately from the fetch-time declaration.
- OCR output is only extracted text; it is not treated as historical exam evidence by itself.
- Question extraction is intentionally not implemented in this phase.

## Next

Phase 3 can consume NormalizedDocument.text and create question candidates without coupling extraction to the source crawler or storage layer.
