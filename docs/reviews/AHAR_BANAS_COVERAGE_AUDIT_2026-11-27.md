# Ahar-Banas subtopic draft-coverage audit — 2026-11-27

## Scope and result

Canonical parent: Rajasthan History → Chapter 2, “राजस्थान के प्राचीन सभ्यता स्थल”.
Child concept: `catalog.rajasthan_history_ancient_history_ahar_banas_culture`.

The authoring inventory now contains **42 Hindi-first AI-authored candidate Q&A (AHB-001–AHB-042)**. The additions in this batch were derived from the RBSE Class X textbook (S32) and the published *Puratattva* analysis (S30). This is a draft-scope sweep only; it is not a verified syllabus-completeness result.

| Coverage dimension | Draft coverage in current set | Audit status / remaining check |
|---|---|---|
| Regional setting / river basin / geographic spread | AHB-001–004, 012–014, 021 | Present in drafts; reconcile textbook wording, district lists and map scope |
| Site and mound identity | AHB-004–006, 012–016, 033 | Dhoolkot added; page-image and site identity check pending |
| Excavation history / researchers | AHB-005, 015, 036, 041 | AHB-041 now states the S32 textbook sequence only: Akshayakirti Vyas (1953), followed by R.C. Agrawal and H.D. Sankalia; independent chronology review is still pending |
| Cultural chronology / phases | AHB-016, 020, 029, 031–032, 037 | Do not conflate Balathal radiocarbon range, Ahar ceramic subphases and Gilund's textbook phases |
| Pottery / ceramic taxonomy / decoration | AHB-007–011, 018, 028–030, 038 | Multi-source classifications differ; present each classification with named source |
| Settlement layout / houses / defenses / storage / bricks | AHB-019, 022–023, 026, 031–032, 040 | Functions of central enclosure and “oldest” superlatives remain interpretive; brick contrast source-specific |
| Subsistence / crops / fauna / economy | AHB-017, 024–025 | Present; primary archaeobotanical/archaeozoological evidence still needs direct review |
| Metallurgy / furnaces / copper | AHB-006, 027–028 | Furnace function is an interpretation; kiln and copper-smelting features must not be confused |
| Trade / exchange / interregional contact | AHB-021, 042 | S30 Introduction, printed p.5, explicitly dates growing Harappan trade contact after c.2600 BCE; independently assess how broadly that inference applies |
| Burial / beliefs / material culture / crafts | AHB-034–035, 039 | Burial-belief inference is textbook interpretation; blocks' function also source-attributed |
| Book-Chapter 2 scope and exam applicability | Child-topic exists in parent file | User's printed pp.145–149 and the selected official exam-specific syllabus must be mapped before claiming complete |
| Duplicate / semantic coverage | All 392 IDs unique; exact normalized question-stem and exact Q&A-pair scan returned 0 duplicate groups | This is exact-string screening only; semantic/concept-equivalence audit and database-side duplicate check remain pending |

## Source register

- **S23:** B.R. Meena, “Recent Exploration in the Valley of Khari and Mansi Rivers, Rajasthan”, *Puratattva* 16 (1985–86), printed pp.20–21. IGNCA scan: https://ignca.gov.in/Asi_data/74144.pdf
- **S24:** Parth Chouhan, “Chalcolithic Cultures Northern and Central India”, e-PG Pathshala / INFLIBNET, Chapter 27, §4: https://ebooks.inflibnet.ac.in/icp02/chapter/152/
- **S30:** Vasant Shinde, Gregory L. Possehl and Shweta Sinha-Deshpande, “The Ceramic Assemblage in Protohistoric Mewar (Rajasthan), with Special Reference to Gilund and Balathal”, *Puratattva* 32 (2001–02), printed pp.5–24. AHB-042 uses the Introduction on p.5. IGNCA scan: https://ignca.gov.in/Asi_data/87125.pdf
- **S31:** Debasri Dasgupta, “Site Catchment Analysis of the Chalcolithic Settlement of Gilund in the Banas Basin”, *Puratattva* 35 (2004–05), printed pp.103–104. IGNCA scan: https://ignca.gov.in/Asi_data/88233.pdf
- **S32:** Rajasthan Board of Secondary Education, *History and Culture of Rajasthan*, Class X, printed p.4: https://rajeduboard.rajasthan.gov.in/books-2019/books-2022/cls10/HistorynCulture.pdf

## Additional static checks on AHB-033–AHB-042

- All 10 new IDs are unique; across the 392-row Chapter 2 offline pool, normalized exact question-stem duplicates: 0 groups, and exact normalized Q&A-pair duplicates: 0 groups.
- Each new question contains exactly one question mark, contains Devanagari prose without Latin-script prose, and each question and answer is under the 240-character one-liner limit.
- All 10 rows use `language_code=hi`, `verification_status=NEEDS_REVIEW`, and retain source evidence; none is a PYQ or verified row.

## Material limitations

1. The source text/indexed content was retrievable, but screenshot/page-image inspection of the large RBSE and IGNCA-hosted PDFs failed due runtime file-size limits. Printed page/plate images remain a mandatory independent-review task.
2. AHB-041 has been tightened to the S32 textbook's explicit sequence: Akshayakirti Vyas (1953), followed by Ratan Chandra Agrawal and H.D. Sankalia. The previous draft incorrectly framed S23 as a conflicting discovery attribution; that interpretation has been removed. A full excavation-history review remains open.
3. No official exam-specific syllabus mapping has been accepted.
4. The live database has not been queried after migration 0032. Git migration files and local JSON do not prove production persistence.
5. All 42 AHB and all 392 Chapter 2 candidates remain `NEEDS_REVIEW`; no reviewer audit events, VERIFIED status or PYQ provenance are claimed.
6. The full Chapter 2 parent has five child-site sections. Completing this Ahar-Banas drafting pass does not complete Chapter 2.

## Acceptance actions still required

- Obtain a visual/manual review of S23, S30, S31 and S32 printed pages/plates.
- Match the full user-supplied book Chapter 2 and a selected official exam syllabus to each child-topic and concept.
- Run a semantic duplicate check against the full Chapter 2 pool and source-specific fact conflicts.
- Submit individual decisions through the protected independent-review workflow, retaining reviewer identity, time and notes.
- Apply migrations through the controlled workflow and query live counts/statuses.
- Verify authenticated learner behaviour and the release APK on the exact accepted main SHA.

**Conclusion:** Ahar-Banas has a materially broader draft coverage inventory (42 items), but is **not independently verified or complete**. Rajasthan History Chapter 2 remains **IN_PROGRESS**; do not advance to Chapter 3 or Indian GK.


## 2026-11-27 — Source precision correction (AHB-041 and AHB-042)

- AHB-041 is revised to the RBSE Class X book's own sequence: Akshayakirti Vyas began excavation in 1953, followed by Ratan Chandra Agrawal and H.D. Sankalia. The previous draft's claim that S23 provided a conflicting attribution was too strong and has been removed.
- AHB-042 now exactly reflects S30's Introduction (printed p.5): Ahar Culture developed and flourished with growing trade contact with the Harappans after 2600 B.C. The answer no longer generalises the claim to every community in the full Banas region.
- New forward migration 0033 updates only records still NEEDS_REVIEW with reviewed_at NULL, avoiding any overwrite of an independent reviewer decision. All 392 rows remain NEEDS_REVIEW in the Git/offline candidate bank; live DB effect remains unconfirmed.
