# Phase 6 — AI Material Analysis

## Phase 6.5 — AI Question Generation + Answer Verification + Duplicate / Quality Control

Phase 6.5 converts grounded material facts/concepts into **generated practice MCQs**.
It does not create historical exam appearances.

\`\`\`
Important Facts + Proposed Concepts
        +
Phase 6.4 Verified Match Result
        ↓
GenerationSpecification
        ↓
Structured AI MCQ
        ↓
Schema Validation
        ↓
Independent Answer Verification
        ↓
Duplicate / Existing Question Check
        ↓
Quality Control
        ↓
Difficulty + Importance
        ↓
Safe Generated Question
\`\`\`

### Safety boundaries

- Generated questions are always separate from \`QuestionCandidate\` and \`ExamAppearance\`.
- A generated question can never become historical evidence through this pipeline.
- Four options are required and must be A/B/C/D.
- Accepted questions require VERIFIED answer status and high verification confidence.
- Verification evidence must itself be an exact source-fact string.
- Source facts must meet minimum confidence/importance thresholds.
- Known master-question duplicates are rejected.
- Ambiguous semantic duplicate candidates are not rejected as certain duplicates; the
  duplicate finder only accepts a clear semantic winner.
- Malformed provider output fails closed through strict Pydantic schemas.
- API keys remain environment-driven; CI does not call the live model.

### Provider boundary

\`QuestionGenerationProvider\` and \`AnswerVerifier\` are provider-neutral protocols.
The current Gemini implementation uses the same existing provider configuration and
Google Gen AI SDK already present in the project. Tests use deterministic providers.

### Persistence

Accepted and rejected generated questions are persisted separately in
\`generated_questions\`. This provides an audit trail for quality-control decisions
without mixing generated content into the historical question database.

### Current limitation

The local \`FactGroundedAnswerVerifier\` is intentionally conservative and can only
verify answers whose option text is explicitly supported by the supplied fact text.
The Gemini verifier is an independent model stage; its evidence is still required
to match source facts exactly before a question can be accepted.

The next phase can consume only \`GeneratedMCQ(status=ACCEPTED)\` records.
