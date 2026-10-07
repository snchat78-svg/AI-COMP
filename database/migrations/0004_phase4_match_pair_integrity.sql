-- Phase 4 matching pair integrity.
-- The application stores matches as unordered relationships, so the
-- database enforces a canonical lexical ordering for the pair.

BEGIN;

ALTER TABLE question_matches
    ADD CONSTRAINT question_matches_canonical_order
    CHECK (left_question_id < right_question_id);

COMMIT;
