# Chapter 2 — static integrity audit and Matsya source-text review

**Date:** 2026-11-19  
**Repository base:** `main` at `1827bc7d984fcea2900cdb54921341f23cb2fc49`  
**Scope:** `docs/study-notes/rajasthan-history/ancient-history/ancient-civilization-sites.md`, cross-checked with `docs/QUESTION_BANK_CONTENT_COVERAGE.csv`.  
**Classification:** Documentation/static audit only. No question is promoted to VERIFIED.

## 1. Chapter row integrity

| Check | Result |
|---|---:|
| Parsed question rows | 368 |
| Unique IDs | 368 |
| Duplicate IDs | 0 |
| Blank question or answer | 0 |
| Missing/non-standard evidence locator | 0 |
| Exact normalized question-stem duplicate groups | 0 |
| Sequential ID gaps | 0 |

Draft counts by existing child:

- KAL: 311 (KAL-001–KAL-311)
- AHB: 20 (AHB-001–AHB-020)
- GJ: 18 (GJ-001–GJ-018)
- BRT: 9 (BRT-001–BRT-009)
- MTS: 10 (MTS-001–MTS-010)

Normalization used Unicode NFKC, lowercase, punctuation removal and whitespace folding. This detects exact normalized stem duplicates only; it does not prove factual correctness or absence of conceptual/semantic overlap.

## 2. Similar-stem candidates for human review

A light token-set Jaccard scan (candidate threshold 0.72) returned three parallel-stem pairs:

| Pair | Similarity | Why this is not auto-labelled a duplicate |
|---|---:|---|
| KAL-007 / KAL-008 | 0.889 | Separate Kalibanga-I and Kalibanga-II cultural-stage questions |
| KAL-009 / KAL-010 | 0.857 | Separate early-Harappan and mature-Harappan chronology questions |
| KAL-021 / KAL-022 | 1.000 | Same stem template asks about different mound IDs, KLB-2 and KLB-3 |

These are review cues, not duplicate findings. Keep both questions unless an independent reviewer finds the answers test the same fact without useful distinction.

## 3. Matsya source-text cross-check

### S28 — Rajasthan Board Class X textbook

The official Board of Secondary Education, Rajasthan PDF is titled *History and Culture of Rajasthan*, Class X. Its searchable text under “Janapadas of Rajasthan” and “Matsya Janapada” supports the source-attributed facts used by MTS-001–MTS-006 and MTS-010: Matsya is included in the sixteen-janapada list attributed there to the Anguttar Nikaya; the Matsya tribe is mentioned in the Rigveda, Shathpatha Brahmana and Kaushitaki Upanishad; the Mahabharata refers to Matsya as a prominent janapada; parts of modern Jaipur, Alwar and Bharatpur are included; and the textbook associates king Virata with Viratnagar/Bairath. The text also reports Bairath's Ashokan/Buddhist and Mauryan-period remains.

Official source: https://rajeduboard.rajasthan.gov.in/books-2019/books-2022/cls10/HistorynCulture.pdf  
Searchable PDF text locations checked: “Janapadas of Rajasthan” and “Matsya Janapada” (the chapter text occurs around the printed pp. 6–7 region).

### S29 — S. M. Ali

S. M. Ali, *The Geography of the Purāṇas*, Chapter X, printed p. 137, “Matsya”, supports MTS-007–MTS-009 as that author's geographical reconstruction: Vairāta/Bairāta in the Alwar hills, near the meeting/headwater region of the Sabi and Banganga, and the approximate southern limit along the middle Banas axis.

ASI Central Archaeological Library copy: https://ignca.gov.in/Asi_data/73689.pdf  
Searchable PDF text checked at printed page 137.

### Required attribution and limitations

- S28 and S29 give materially different approximate boundary descriptions. Preserve the source-specific attribution; do not merge them into one definitive boundary.
- Epic narrative about king Virata and the Pandavas remains literary tradition, not independent archaeological proof.
- PDF page-image screenshots could not be retrieved in this run because the source downloads timed out or exceeded the inspection size limit. Printed-page/figure visual inspection remains outstanding.
- The user's exact textbook pages 145–149 are not present in this review context. Therefore this audit does **not** certify that Matsya Janapada belongs as a child under that particular book's “राजस्थान के प्राचीन सभ्यता स्थल” Chapter 2. The current merged child placement remains pending confirmation against those pages.
- This cross-check is limited to the 10 Matsya draft references and source text. It is not a full independent scholarly review of all 368 questions.

## 4. Status and next gate

- All 368 remain AI-authored study-note drafts with `NEEDS_REVIEW`; none is a PYQ or learner-verified item.
- No exam-syllabus applicability, live database count or official RSSB profile is inferred from this content audit.
- Phase 6.56 remains `IN_PROGRESS`; Phase 6.57 remains `PLANNED`; Phase 6.58 remains `BLOCKED`.
- Next: inspect the user's exact book pages 145–149 to confirm the parent chapter's complete child inventory and Matsya placement; then review the three similar-stem pairs, carry out source-by-source fact review for the five children, and record reviewer decisions without self-approval.
