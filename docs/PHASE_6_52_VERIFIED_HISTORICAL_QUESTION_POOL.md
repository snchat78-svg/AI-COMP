# Phase 6.52 — Verified Historical Questions in the Practice Pool

## Screenshot diagnosis

The dashboard warning is accurate for the old selector: it asks the backend for eligible practice questions, but the configured pool is empty. Source-backed historical questions are persisted by Phase 2.4 in `questions`, `question_options`, `question_answer_records`, `paper_answer_key_pairs`, `exam_appearances`, and `appearance_sources`. Until this phase, `PostgresPreparationContextProvider` only queried `generated_questions`. That meant a correctly verified past-paper appearance could exist without ever being considered for a timed practice test.

There are two separate issues; both matter:

1. **Pool integration gap — fixed in this phase:** the selector must read official answer-key-backed exam history as its own source, not pretend those rows are AI-generated.
2. **Live source reachability — still blocked:** the latest confirmed official-source research run persisted zero candidates. The current RSSB and RPSC hosts timed out at TCP; the official RSSB legacy host accepted TCP but failed certificate-validated TLS with `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`. This phase cannot invent live records to overcome that external restriction.

## Implemented

### 1. Separate historical-question read model

`PostgresVerifiedHistoryQuestionRepository` builds a read-only practice view from the existing Phase 2.4 tables. It accepts an MCQ only when the persisted evidence satisfies all of these gates:

- The recorded exam appearance is linked to a verified official question-paper source.
- The corresponding paper/key pair is explicitly `MATCHED` for the same exam, year, and shift.
- A verified official answer-key source is linked to the same appearance and paired key document.
- The question's resolved answer record points at that paired answer-key document and matches the appearance's correct option.
- Four distinct stored options exist and the answer key points to one of them.
- Paper and answer-key source URLs are HTTPS and match registered official hosts.
- The source is still registered as official. Ambiguous pairs, unresolved answers, secondary sources, unknown question types, and malformed option sets do not enter the historical practice pool.

The repository creates an in-memory practice-session item with `source_kind=VERIFIED_EXAM_HISTORY`; it does not insert that item into `generated_questions`. A storage guard rejects attempts to persist historical items as AI-generated rows.

### 2. One bounded, deduplicated eligible pool

The context provider now merges two separate bounded reads: accepted answer-verified generated questions and eligible official exam-history questions. It normalizes question stems and keeps only one exact textual duplicate, preferring the official source-backed historical item. The final combined pool remains capped by the configured pool limit, and concept-scoped tests still require matching concept metadata.

Historical source type, paper URL, answer-key URL, exam name/ID, year, shift, exam question number, and verified appearance count are persisted in the immutable test-session snapshot. A practice-question response labels official history explicitly; the correct answer stays hidden until the existing answer-review stage.

### 3. Readiness API and honest dashboard state

The authenticated read-only endpoint `GET /api/v1/learners/{learner_id}/question-bank/readiness` returns bounded aggregate counts split by source: eligible total, verified historical, and accepted generated questions.

The mobile dashboard displays those counts. When the count is known to be zero, it disables test creation instead of letting the learner repeatedly create a test that cannot start. When readiness cannot be checked, it reports that separately and also blocks the action until a reliable count can be loaded. A nonzero count still depends on the existing session and answer-verification gates; the UI never fabricates substitute questions.

## Validation required

- Unit tests check the official-source/answer-key/matched-pair gates, answer-option normalization, separate storage, and legacy session-snapshot compatibility.
- PostgreSQL integration test seeds a synthetic official paper plus official answer key and proves that a resolved historical MCQ can enter the pool; it also stores a generated duplicate stem and checks that it is counted only once and history provenance wins.
- API tests cover learner-scoped readiness and fail-closed behavior; Flutter tests cover readiness parsing and request headers.
- Validation on the merged implementation: main Python/PostgreSQL suite and Docker build passed; Flutter analyze and mobile tests passed. A test APK built and was verified/uploaded from the same Flutter source files as main; the latest main-branch packaging run was still in progress at this checkpoint.

A passing test with an empty real database proves only that the guards behave correctly. It does not prove that live papers or history records exist.

## Exact resume point

1. Phase 6.52 is merged as PR #34. The code fixes the source-selector integration gap but does not generate or backfill any historical paper records.
2. Confirm the live API responds to the readiness endpoint and that it returns real source-separated counts.
3. Restore one approved official HTTPS source path without bypassing TLS, robots, terms, or host restrictions.
4. Run the existing discovery workflow and require nonzero persisted candidates.
5. Run paper processing, then answer-key reconciliation; confirm actual verified appearance records.
6. Refresh the app and verify its readiness count changes based on the records—not on mock, duplicate, or unverified questions.

If official sources remain blocked, the app should continue to explain that the eligible pool is empty. That is a visible unresolved ingestion blocker, not a reason to lower verification standards.
