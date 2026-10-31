# Phase 6.56 — Examinable-point coverage checklist and gap report

**Status:** IN_PROGRESS — reviewer workflow design and acceptance contract started; no real official syllabus has been ingested or certified by this document.
**Parent phase:** Phase 6.56 Exam-profile selection and syllabus-to-concept mapping.
**Depends on:** verified official document bytes and identity; structured UNIT/TOPIC/SUBTOPIC inventory; independently reviewed concept mappings; Phase 6.55 source-backed One-Liner review.
**Must not unlock:** Phase 6.57 or exam-ready profile status.

## Purpose

Question count is not syllabus coverage. A topic may have many repeated questions while one or more examinable facts, definitions, formulas, exceptions, locations, processes, diagrams, or comparisons remain absent. This checklist defines the unit of coverage as an independently reviewable **examinable point**, not a generated question.

## Required hierarchy

Every selected exam must be represented as:

`Exam profile → official syllabus document/version → UNIT → TOPIC → SUBTOPIC → examinable point → canonical concept → learning item(s)`

Each node must retain stable IDs and parent relationships. An examinable point must not be silently merged with a neighbouring point merely to improve a coverage percentage.

## Examinable-point record contract

A point record must contain:

- Stable `point_id`, `syllabus_id`, `unit_id`, optional `topic_id` and `subtopic_id`.
- Concise point statement in the syllabus language, plus normalized display text where needed.
- Exact source page and section/heading locator; evidence excerpt must be short and traceable to the persisted official document digest.
- Point type: `FACT`, `DEFINITION`, `FORMULA`, `PROCESS`, `COMPARISON`, `CLASSIFICATION`, `LOCATION`, `DIAGRAM`, `EXCEPTION`, `NUMERICAL_SKILL`, or `OTHER`.
- One or more canonical concept IDs, or explicit `MAPPING_GAP` with a reason.
- Review state: `NEEDS_REVIEW`, `VERIFIED`, or `REJECTED`; author and independent reviewer identities/timestamps.
- Learning-item coverage state derived only from independently VERIFIED One-Liners or eligible verified historical questions. Draft/generated/rejected/duplicate items do not count.

## Coverage dimensions

For every point, reviewers assess these dimensions where applicable:

1. **Presence:** Is the point represented by at least one valid learning item?
2. **Correctness:** Does the answer match the official source and any necessary authoritative reference?
3. **Atomicity:** Does one question test one point rather than bundling unrelated facts?
4. **Recall depth:** Is direct recall covered where the point requires it?
5. **Application:** Is calculation, interpretation, sequence, or application covered where applicable?
6. **Discrimination:** Are likely confusions, contrasts, exceptions, and boundary cases covered where the source requires them?
7. **Language:** Is the Hindi/English wording faithful and unambiguous, without changing technical meaning?
8. **Provenance:** Can each item be traced to its evidence and reviewer decision?
9. **Duplication:** Are near-identical items counted once for coverage, with duplicate/rejection counts separately audited?

Not every point requires every dimension. The reviewer must mark a dimension `APPLICABLE`, `NOT_APPLICABLE` with a reason, or `GAP`; blank is not treated as passed.

## Gap report semantics

The report must be calculated per exam profile, syllabus version, unit, topic, subtopic, and point. It must report counts separately:

- Total inventoried points.
- Points awaiting review / rejected.
- Points with mapping gaps.
- Points with no verified learning item.
- Points with only draft or duplicate items.
- Points with missing applicable dimensions.
- Fully covered points.
- Verified One-Liner count and verified historical-question count (separate pools).
- Generated, rejected, duplicate, pending-review and verified batch counts (never combine these).

Coverage percentage is `fully_covered_points / reviewed_in_scope_points * 100`; it must be shown only when the denominator is non-zero and the source inventory is independently attested complete. Also show the raw numerator/denominator. An incomplete inventory must display **COVERAGE UNKNOWN — INVENTORY INCOMPLETE**, not a misleading percentage or 100%.

A topic is complete only when every in-scope point is verified and all applicable dimensions pass. An exam profile is complete only when every unit/topic/subtopic and point has been independently reviewed, all mappings are resolved, and every in-scope point meets the coverage rule. A question-count target is never a substitute.

## Reviewer checklist

- [ ] Official issuing body, notification number, title, version/date and exact document SHA-256 independently confirmed from actual bytes.
- [ ] Every page reviewed; all units, topics, subtopics and examinable points inventoried.
- [ ] Each inventory row has an exact page/section locator and evidence.
- [ ] Missing catalogue concepts added before inventory-complete attestation.
- [ ] Every canonical concept has an evidence-backed IN_SCOPE or OUT_OF_SCOPE decision; no UNMAPPED/NEEDS_REVIEW rows remain.
- [ ] Each point is atomic and linked to canonical concept(s).
- [ ] Applicable coverage dimensions are assessed; N/A decisions include reasons.
- [ ] Only independently VERIFIED items count; generated candidates remain NEEDS_REVIEW.
- [ ] Duplicate items do not inflate coverage; duplicate/rejected/pending counts remain visible.
- [ ] Old Papers and One-Liners remain separate content pools.
- [ ] A second reviewer independently checks the report and samples item evidence.
- [ ] Live API/mobile view shows the same counts and does not unlock incomplete profiles.

## Fail-closed rules

- No official PDF bytes/digest means no official point inventory and no exam-ready coverage claim.
- A secondary transcription may guide research only; it cannot be the source of VERIFIED points.
- Missing or ambiguous source locators, reviewer identity, mapping, or dimension assessment means GAP/NEEDS_REVIEW.
- Failed coverage query or partial pagination means report status is unavailable/incomplete, never zero gaps.
- AI-generated content cannot approve its own point, mapping, answer, or coverage dimension.
- Do not bypass TLS, robots policy, source allowlists, reviewer separation, copyright/reuse rights, or database constraints.

## Implementation sequence

1. Keep the current verified inventory/mapping gates; do not seed a real profile from secondary transcription.
2. Add persistent point/dimension records and append-only independent-review audit using existing syllabus author/reviewer identity controls.
3. Add a deterministic read-only gap-report query with bounded pagination and explicit inventory completeness.
4. Add tests for incomplete inventory, unmapped points, missing dimensions, draft-only items, duplicates, rejected items, separate Old Papers/One-Liners, empty denominators, query failure and reviewer separation.
5. Add reviewer API/UI and ensure only VERIFIED points/items affect coverage.
6. Run exact-head backend tests/container build and Flutter analyze/tests/release APK checks; then deploy and compare API report with the mobile view using real approved data.

## Current evidence and next action

At branch creation, main was `83841e01ef1a6a60d1d5a2a72daa53c70def9579`. PR #107 already supplies topic-level duplicate detection and batch audit; this increment must reuse those outputs rather than create a second deduplication engine. The current official-source blocker means the first implementation and tests must use synthetic fixtures only, clearly labelled as synthetic. No live exam syllabus or candidate is to be promoted.

**Next coding slice:** inspect the existing syllabus inventory and one-liner review schemas, then implement the smallest additive persistence/API slice for point coverage and deterministic gap reporting. Do not change the Phase 6.56 completion status until all parent acceptance gates pass.
