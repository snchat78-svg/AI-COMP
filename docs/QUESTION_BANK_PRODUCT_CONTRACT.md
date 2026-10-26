# AI-COMP Question Bank Product Contract

**Status:** Permanent product requirement  
**Last updated:** 2026-10-26  
**Canonical state:** [Phase Registry](PHASE_REGISTRY.md)  
**Coverage policy:** [One-Liner Content Coverage](QUESTION_BANK_CONTENT_COVERAGE.md)  
**Continuity checkpoint:** [Project Continuity Checkpoint](PROJECT_CONTINUITY_CHECKPOINT.md)

## 1. Two separate learner-facing sections

The Question Bank has two distinct content lanes. They must not be merged into a single list or treated as interchangeable.

### A. One-Liner Questions

Navigation is **Subject → Topic → Subtopic → One-Liner Q&A**.

- The aim is to cover the complete applicable official syllabus for each supported exam, subject, topic and subtopic—not merely provide a few sample questions.
- Each learner-facing item is a concise, direct question and answer (Q → A), rather than a bare fact or short-note paragraph.
- For each topic, create a checklist of all relevant examinable knowledge points. Cover definitions, facts, names, places, dates, classifications, lists, comparisons, causes/effects, rules, formulas, exceptions and other syllabus-relevant points as appropriate.
- Use the exam's official syllabus to determine which topics apply. If an official syllabus includes a missing topic/subtopic, add it to the stable taxonomy and coverage ledger; do not silently omit it.
- Drafts require authoritative source URLs and evidence locators, deduplication and independent review. AI-generated content must not approve itself. Pending or disputed content must not be presented as independently verified.
- A minimum question count is a progress floor, not proof that the topic is complete. Show coverage honestly as not started, drafting, needs review, partially covered or verified complete.

### B. Previous Year Papers (Old Papers)

This is a separate section for actual published examination papers, navigable by exam/recruitment, year, paper/stage and other available official metadata.

- Find papers from the responsible official recruitment/exam authority's own official sources. Keep the original paper document and source provenance; preserve the actual wording, options, order and paper identity when presenting its questions.
- The existing official-source discovery and paper-processing pipeline should continuously check registered official sources on its configured schedule/workflow. When a new paper is published and becomes reachable, discover it, record it idempotently and process it through the existing ingestion pipeline so it appears in Previous Year Papers after the required checks pass.
- Deduplicate using the existing stable candidate identity, canonical source evidence and content hash. A revised paper/answer key must be represented as a clearly linked version or new artifact, not silently overwrite historical evidence.
- Keep newly discovered items pending until source authenticity, document integrity, exam/year/paper identity and required review gates are satisfied. Never label a candidate official/verified merely because its URL looks official or it was found by a crawler.
- Where an official answer key exists, pair it with the correct paper under the existing answer-key verification rules. Do not invent missing answers or infer that a paper is verified from a successful empty-queue workflow.
- Source/network failures must be visible in operational status. They must not create fake records, silently claim that the latest papers are current, remove already valid historical papers, or cause unofficial mirrors to be presented as official.
- A newly published paper being added to Previous Year Papers does **not** automatically make its questions approved One-Liners. Paper history and the curated topic-wise Q&A bank are separate products. Content may be separately proposed for the One-Liner bank only through its source, deduplication, topic-mapping and independent-review process.

## 2. Automatic update behaviour and its limits

The intended user experience is that new official papers show up in Previous Year Papers without manual paper uploads by the learner. This depends on the registered official sources being reachable, the scheduled/workflow discovery succeeding and each candidate passing required integrity/review gates. The system must report blocked/failed discovery honestly; it must never promise that the latest paper has been fetched when no evidence exists.

Current operational note (2026-10-26): official-source diagnostics show the current RSSB and RPSC hosts timing out at TCP, while the legacy RSSB host fails certificate-validated TLS. No registered official source has currently passed the required network/TLS gate, the latest source-health run persisted no paper candidates, and the pending CET syllabus fetch did not yield official PDF bytes. Therefore **automatic update is a required product behaviour, but current live auto-ingestion is not yet proven and remains blocked**. Keep normal TLS certificate validation enabled and do not use unofficial mirrors as official evidence.

## 3. Acceptance criteria

The product contract is satisfied only when all applicable criteria are demonstrated:

1. The mobile experience exposes clearly separate One-Liner and Previous Year Papers entry points.
2. One-Liners navigate subject → topic → subtopic and show concise Q → A items; coverage status is derived from the official-syllabus/topic ledger and independent review records.
3. Old Papers list real paper artifacts with exam, year, official source and status; paper detail preserves the source paper/question context and links only the matching verified answer key where available.
4. The scheduled or controlled official-source discovery detects a newly published official paper in an end-to-end test, stores it without duplicate rows, and makes it appear in Old Papers after its validation gates.
5. Tests prove that failed/blocked retrieval, empty queues, unverified candidates and unrelated answer keys are not misreported as successful ingestion.
6. A paper appearing in Old Papers does not bypass the independent Q&A approval workflow.
7. The feature is not called complete until current-head CI and the relevant live-data/mobile end-to-end acceptance checks pass.

## 4. Implementation guardrails

- Reuse the existing source registry, discovery workflows, paper candidate/document storage, extraction, SHA-256 identity, answer-key pairing, topic taxonomy, One-Liner repository and independent reviewer workflows.
- Do not create a parallel paper downloader, paper table or topic taxonomy merely to satisfy this product contract.
- Do not start a dependent phase while official-source connectivity and real-data ingestion remain blocked. Continue the earliest unsatisfied acceptance gate and record exact evidence in the [Phase Registry](PHASE_REGISTRY.md) and [Project Continuity Checkpoint](PROJECT_CONTINUITY_CHECKPOINT.md).
