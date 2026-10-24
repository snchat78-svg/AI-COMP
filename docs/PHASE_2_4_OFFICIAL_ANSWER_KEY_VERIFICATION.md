# Phase 2.4 — Official Answer-Key Verification and Historical Ingestion

## Goal

Turn only source-backed, explicitly identified official paper records into exam appearances. Keep answer-key pairing separate from question extraction, and retain the original answer-key document as provenance.

## Implemented

- Expanded the seeded Rajasthan registry with Patwar, LDC, VDO, Junior Assistant, Lab Assistant, RAS, Sub Inspector, School Lecturer, Senior Teacher, and Assistant Professor targets.
- Add the RPSC official answer-key archive as a separate controlled discovery seed.
- Resolve exam/year/shift only from explicit registered aliases and archive labels/URL path. Generic RPSC archive results and ambiguous/multiple-year titles remain in review.
- Pair a question paper and answer key only when the explicit exam/year match, exactly one eligible paper and one eligible key are present, the shift matches exactly, and both extractions contain records.
- Persist pair outcomes in paper_answer_key_pairs; ambiguous options use NEEDS_REVIEW.
- Persist verification queue state in paper_verification_state, with bounded batches ordered by last processing time so later batches do not starve behind the oldest rows.
- Reuse the existing verified-ingestion orchestrator to record official exam appearances. Unresolved answers stay empty instead of being guessed.
- If a separately stored official answer key resolves a question, record its document ID in question_answer_records.source_answer_key_document_id and link the key URL as an additional appearance_sources record.
- Make historical appearance writes idempotent. A later official answer key can fill a missing answer; a conflicting non-empty official answer is rejected for review, not overwritten.
- Add a manual/daily GitHub Actions runner and safe summary.

## Migration required

Before running the new workflow, apply migration 0018_phase2_4_official_answer_key_pairs.sql through the existing manual-only database migration workflow. The verification CLI fails closed when version 0018 is missing. It does not apply migrations during normal API startup.

The migration adds the pair/review queue tables and a nullable source_answer_key_document_id column. Existing question, login, test, result, and learning tables are not deleted or reset.

## Run order

1. Run Apply database migrations from GitHub Actions, with the existing explicit confirmation input (APPLY).
2. Run official-source-research to register and discover official source candidates.
3. Run official-paper-processing to fetch, hash, privately store, normalize, OCR when required, and extract question/answer-key candidates. This uses the configured AI_COMP_DATABASE_URL, SUPABASE_URL, and server-only SUPABASE_SERVICE_ROLE_KEY repository secrets.
4. Run official-answer-key-verification. Its defaults are source all and batch limit 500; the daily schedule runs after discovery/processing.

Never paste service-role keys, database passwords, or connection strings into chat or commit them to the repository. Keep the Supabase Storage bucket private.

## Verification and history rules

- A registered official HTTPS document can establish its source origin, but this alone does not establish an exam/year when those labels are missing.
- Exam ID, year and shift must be explicit and unambiguous before an exam_appearances row can be created.
- A paper may establish that a question appeared even if its official answer key has not yet been found. In that case, correct_answer stays NULL.
- A separate answer key is not automatically paired based on similar filenames alone.
- Matching questions across websites does not create additional exam appearances.
- The number reported is the number of supported records in this database, not a claim of full coverage of all government exams.
- The current workflow does not claim the learner practice-test pool has been populated. That needs the next test-selection increment to expose verified historical questions as a distinct source, without inserting them into the AI-generated question table.

## Latest live verification evidence (24 October 2026)

The scheduled [official-answer-key-verification run #8](https://github.com/snchat78-svg/AI-COMP/actions/runs/40077069998) exited successfully but reported `selected_candidates=0`, `pairs_matched=0`, `extracted_questions_seen=0`, and `failed=0`. This is an empty-queue run, not completed answer-key verification or historical ingestion. Rerun only after Phase 2.2 discovery persists real candidates and Phase 2.3 extracts real paper/key records; verify matched pairs, review states, resolved answers and source-linked appearance counts.

## Tests

Coverage includes explicit exam/year resolution, ambiguity-safe pairing, empty-extraction rejection, separate source-document provenance, database question-pool loading, and existing end-to-end verified-ingestion contracts. The full repository pytest suite and Docker build are the merge gate.
