# Phase 6 — AI Material Analysis

## Phase 6.4 — Verified Exam DB Matching + Existing Question Detection

Phase 6.4 consumes the grounded Phase 6.2 analysis result and matches it only
against **ACTIVE master questions that have at least one VERIFIED exam appearance**.

### Matching boundary

\`\`\`
NormalizedMaterial
  -> MaterialAnalysisResult
       -> explicit question probes
       -> proposed concepts
  -> verified ACTIVE master-question candidates
  -> exact existing-question detection
  -> conservative rephrased detection
  -> same-concept matches
  -> related-topic matches
  -> persistence of accepted match decisions
\`\`\`

### Existing-question detection

A plain study fact is **never** converted into a previous-exam question match merely
because embeddings are similar.

EXACT/REPHRASED detection is performed only for question-text probes. The default
probe extractor requires an explicit question mark (\`?\` or \`？\`) and preserves the
source text as evidence.

EXACT uses normalized question-stem equality.

REPHRASED uses an injected embedding function and two safety gates:

- minimum similarity \`0.94\`;
- winning-candidate margin \`0.05\` over the second eligible candidate.

When the winner is ambiguous, the result is left unmatched. No guessing is allowed.

### Verified evidence gate

For every candidate master question, Phase 6.4 counts only VERIFIED
\`ExamAppearance\` records and deduplicates the real exam occurrence by:

\`exam_id + year + shift + question_number\`

A master question with zero verified appearances is not a search candidate.

Therefore:

- a user note cannot create historical evidence;
- an unverified website copy cannot make a question historical;
- SAME_CONCEPT is not previous-question equivalence;
- RELATED_TOPIC is not previous-question equivalence.

### Concept and topic matching

\`ProposedConcept\` is resolved through an injected canonical concept resolver.
Only an explicit canonical concept ID may produce SAME_CONCEPT.

RELATED_TOPIC is also provider-injected. A score below the configured threshold
(\`0.85\`) is ignored. SAME_CONCEPT takes precedence over RELATED_TOPIC for the
same material concept/master pair.

No keyword guessing is used.

### Persistence

Accepted matches are stored in \`material_question_matches\`.

The record contains:

- material ID;
- probe ID and probe type;
- master-question ID;
- match type;
- confidence;
- verified appearance count;
- machine-readable evidence.

NO_MATCH and AMBIGUOUS results are intentionally not persisted as positive
historical links.

### Current scale boundary

The in-memory service retrieves a bounded set (maximum 1000 in the current repository contract) of active masters and filters them
by verified appearance. This is deterministic and safe for the current phase.
For production scale, the next data-layer optimization should replace this
candidate scan with a persistent verified-master/vector retrieval index.

### Next phase

Phase 6.5 should take the verified matching result as a hard input boundary and
implement AI question generation:

ImportantFact/ProposedConcept
  -> generation specification
  -> structured MCQ generation
  -> answer verification
  -> duplicate/master/history safety checks

Generated questions must never be represented as previous-exam questions.
