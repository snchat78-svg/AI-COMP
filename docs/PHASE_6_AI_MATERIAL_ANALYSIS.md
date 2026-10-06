# Phase 6 — AI Material Analysis

## Phase 6.2 — Content Understanding, Concept Extraction and Important Facts

Phase 6.2 consumes only NormalizedMaterial produced by Phase 6.1.

Pipeline:

NormalizedMaterial
-> Content Understanding
-> Proposed Concepts
-> Source-grounded Important Facts

### Content understanding

ContentUnderstanding captures:

- language;
- summary;
- key points;
- subject hints;
- topic hints;
- model confidence.

This is an analysis result, not a verified historical record.

### Concept extraction

Concepts are represented as ProposedConcept.

A proposed concept deliberately does not receive a permanent database concept_id at this layer. Its label and taxonomy hints are candidates that a later concept resolver can map to the existing canonical concept database.

Each proposed concept must carry evidence_text that occurs in the normalized material text.

### Important facts

ImportantFact captures:

- fact text;
- exact source evidence;
- importance score;
- extraction confidence;
- fact type.

Facts are grounded in the material text. The pipeline rejects a provider result when its evidence_text is not present in the source material.

This prevents an LLM adapter from silently turning an unsupported claim into a study fact.

### Provider boundary

MaterialAnalysisProvider is intentionally provider-neutral.

Three explicit operations are required:

1. understand;
2. extract_concepts;
3. extract_facts.

A deterministic StaticMaterialAnalysisProvider is included for tests and local development. It is not presented as the final AI implementation.

### Historical-data separation

Phase 6.2 does not create ExamAppearance records, previous-exam claims or verified answer records.

Later matching may compare extracted concepts/facts against the verified question database, but that comparison cannot upgrade user material into historical evidence.

Next: Phase 6.3 — connect an actual LLM provider through this contract, enforce structured output/schema validation, then add verified-database matching for material concepts and existing questions.