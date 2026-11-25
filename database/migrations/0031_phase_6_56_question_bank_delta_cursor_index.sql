-- Phase 6.56: support bounded global keyset pagination for mobile content sync.
BEGIN;

CREATE INDEX IF NOT EXISTS idx_question_bank_one_liners_updated_at_id
    ON question_bank_one_liners(updated_at ASC, one_liner_id ASC);

COMMIT;
