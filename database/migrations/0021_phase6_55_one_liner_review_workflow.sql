-- Phase 6.55: auditable one-liner review with a credential separate from authoring.
-- Any legacy VERIFIED entry without recorded independent review is sent back to review.
BEGIN;

ALTER TABLE question_bank_one_liners
    ADD COLUMN IF NOT EXISTS reviewed_by TEXT,
    ADD COLUMN IF NOT EXISTS review_note TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS source_checked_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS question_bank_one_liner_reviews (
    review_id TEXT PRIMARY KEY,
    one_liner_id TEXT NOT NULL
        REFERENCES question_bank_one_liners(one_liner_id) ON DELETE CASCADE,
    decision TEXT NOT NULL CHECK (decision IN ('VERIFIED', 'REJECTED', 'NEEDS_REVIEW')),
    reviewer_id TEXT NOT NULL CHECK (length(btrim(reviewer_id)) > 0),
    review_note TEXT NOT NULL CHECK (length(btrim(review_note)) > 0),
    source_checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_question_bank_one_liner_reviews_item_time
    ON question_bank_one_liner_reviews(one_liner_id, created_at DESC);

-- Earlier code could mark a row VERIFIED using the authoring token alone.
-- There is no independent reviewer identity for those records, so they must be
-- re-reviewed rather than grandfathered into the learner-visible verified pool.
UPDATE question_bank_one_liners
SET verification_status = 'NEEDS_REVIEW',
    reviewed_at = NULL,
    reviewed_by = NULL,
    review_note = 'Re-review required: independent reviewer evidence was not recorded.',
    source_checked_at = NULL,
    updated_at = NOW()
WHERE verification_status = 'VERIFIED'
  AND (reviewed_by IS NULL OR length(btrim(reviewed_by)) = 0);

ALTER TABLE question_bank_one_liners
    DROP CONSTRAINT IF EXISTS question_bank_one_liners_verified_review_gate;

ALTER TABLE question_bank_one_liners
    ADD CONSTRAINT question_bank_one_liners_verified_review_gate
    CHECK (
        verification_status <> 'VERIFIED'
        OR (
            source_url IS NOT NULL
            AND source_url LIKE 'https://%'
            AND length(btrim(source_evidence)) > 0
            AND reviewed_at IS NOT NULL
            AND reviewed_by IS NOT NULL
            AND length(btrim(reviewed_by)) > 0
            AND source_checked_at IS NOT NULL
        )
    );

COMMIT;
