# अध्याय 2 — हिंदी-प्रथम One-Liner भाषा-जाँच

**दिनांक:** 22 नवम्बर 2026  
**चरण:** Phase 6.56 के भीतर सामग्री-गुणवत्ता सुधार  
**स्थिति:** पहला batch पूरा; अध्याय-स्तरीय भाषा-सुधार जारी  
**मुख्य स्रोत:** `docs/study-notes/rajasthan-history/ancient-history/ancient-civilization-sites.md`

## समस्या और प्रारम्भिक माप

368 प्रश्नों के पूरे अध्याय-2 bank की जाँच में प्रश्न और उत्तर के भीतर देवनागरी के साथ लैटिन-लिपि वाले शब्द मिले। प्रारम्भिक heuristic scan में:

- 292/368 प्रश्नों में लैटिन-लिपि के अक्षर थे।
- 254/368 उत्तरों में लैटिन-लिपि के अक्षर थे।

यह केवल लिपि/शब्द-जाँच है; इससे अपने-आप तथ्यात्मक गलती या गलत भाषा-निर्णय सिद्ध नहीं होता। व्यक्तियों के नाम, तकनीकी शब्द और स्थिर पुरातात्त्विक संकेतांक अलग-अलग पहचानकर सुधारना आवश्यक है।

## Batch 1 — कालीबंगा KAL-001 से KAL-060

**परिणाम: 60/60 प्रश्न और 60/60 उत्तर हिंदी-प्रथम।**

सभी 60 प्रश्नों और उत्तरों में देवनागरी है; स्थिर स्थल-संकेतांक जैसे `KLB-I`, `KLB-II`, `KLB-1`, `KLB-2`, `KLB-3`, `KLB-8` को स्रोत से मिलान और पहचान के लिए जस का तस रखा गया। इनके अतिरिक्त प्रश्न/उत्तर के prose में लैटिन-अक्षर शेष नहीं रहे।

| पहले प्रयुक्त पद | हिंदी-प्रथम रूप |
|---|---|
| Early Harappan | प्रारम्भिक हड़प्पा |
| Mature Harappan | परिपक्व हड़प्पा |
| mound | टीला |
| cemetery mound | समाधि-टीला |
| burial forms | शवाधान के प्रकार |
| mud bricks | कच्ची ईंटें |
| pottery | मृद्भांड |
| seasons | उत्खनन सत्र |
| citadel | दुर्ग क्षेत्र |
| Lower Town | निचला नगर |
| fire altars | अग्निवेदियाँ |
| galleries | प्रदर्शनी-दीर्घाएँ |
| beads | मनके |
| decipher | पढ़ना / व्याख्यायित करना |

व्यक्तियों के नाम देवनागरी में लिखे गए, जैसे एल. पी. टेसिटोरी, ऑरेल स्टाइन और जेम्स टॉड। प्रश्नों के तथ्य, तारीखें, माप, क्रम, उत्तर और source evidence columns को भाषा सुधार के अतिरिक्त नहीं बदला गया। source locator और S-ID जस के तस हैं।

## Batch के बाद पुनः माप

पूरे 368-row chapter पर वही सरल लैटिन-अक्षर heuristic फिर चलाने पर, स्थिर KLB संकेतांकों को हटाकर:

- 252/368 प्रश्नों में अब भी लैटिन-लिपि के पद हैं।
- 211/368 उत्तरों में अब भी लैटिन-लिपि के पद हैं।
- KAL-001–KAL-060 में प्रश्न और उत्तर दोनों की शेष संख्या 0 है।

इसलिए शेष 308 rows पर भाषा-सुधार अभी लंबित है। अगले batch में KAL-061–KAL-120 लिए जाएँगे; उसके बाद शेष कालीबंगा तथा आहड़-बनास, गणेश्वर-जोधपुरा, बैराठ और मत्स्य जनपद के प्रश्नों पर यही प्रक्रिया लागू होगी। अंग्रेज़ी लिपि की हर घटना को अंधाधुंध बदलना उचित नहीं; code, आधिकारिक नाम, वैज्ञानिक संकेत और स्रोत-पहचान सुरक्षित रहेंगे।

## प्रकाशन और गुणवत्ता नियंत्रण

- सभी 368 प्रश्न अब भी AI-authored review drafts हैं; भाषा सुधार अपने-आप factual verification या syllabus approval नहीं है।
- बदले गए 60 प्रश्नों के `NEEDS_REVIEW` status और स्रोत-सूचक नहीं बदले।
- किसी प्रश्न को `VERIFIED` या PYQ नहीं बनाया गया।
- अगले चरण में स्रोत-समीक्षा, निकट-समान प्रश्नों का मानवीय निर्णय और official syllabus applicability अलग gates रहेंगे।

## APK अनिवार्यता

`.github/workflows/flutter-mobile.yml` को इस प्रकार बढ़ाया गया है कि main पर Phase 6.56 दस्तावेज़, study-note सामग्री, coverage ledger या database migrations बदलने पर Flutter release pipeline भी चले। इसी तरह PR validation भी इन files पर चलेगा। Pipeline:
1. Flutter analyze;
2. सभी mobile tests;
3. release-mode Android APK build;
4. वास्तविक Firebase configuration अनिवार्य;
5. APK artifact verification और upload।

CI-only placeholder Firebase configuration से build को distributable APK artifact के रूप में सफल घोषित नहीं किया जाएगा। हर meaningful Phase/content/database merge के बाद main-run artifact की पुष्टि करनी होगी।

## Phase स्थिति और अगला काम

Phase 6.56 अभी `IN_PROGRESS` है। Phase 6.57 `PLANNED` और Phase 6.58 `BLOCKED` रहेंगे।  
**अगला bounded content batch:** KAL-061–KAL-120 का हिंदी-प्रथम सुधार, फिर समान automated language regression test।  
**अगला technical gate:** इस branch के exact head पर backend tests, Flutter analyze/tests, APK build, verification और artifact upload पास होना।


## Batch 2 — कालीबंगा KAL-061 से KAL-120

**परिणाम: 60/60 प्रश्न और 60/60 उत्तर हिंदी-प्रथम।**

- चूड़ियों, मृद्भांड-श्रेणियों, संग्रहालय-दीर्घाओं, धातु-वस्तुओं, रसोई उपकरणों, मनकों, मापन उपकरणों, शंख/सीप की वस्तुओं, वस्त्र-निर्माण और शवाधान से जुड़े प्रश्नों/उत्तर में सामान्य अंग्रेज़ी पदों को हिंदी किया गया।
- स्थिर स्थल संकेतांक, स्रोत पहचान, पृष्ठ-संख्या, संख्यात्मक आँकड़े और स्रोत-आधारित सावधानी सुरक्षित रखी गई। Fabric A–F को हिंदी में “श्रेणी A–F” किया गया; ये स्रोत की वर्ग-संज्ञाएँ हैं।
- यह भाषाई संपादन है; तथ्यात्मक सत्यापन या परीक्षा-प्रासंगिकता की स्वतंत्र स्वीकृति नहीं। सभी 60 प्रश्न NEEDS_REVIEW हैं।
- Batch 2 के प्रश्न/उत्तर prose में Latin-script शब्दों का lexical scan शून्य रहा; स्थिर श्रेणी-संकेत A–F को scan exception रखा गया।

## संचयी स्थिति

- कालीबंगा KAL-001–KAL-060: 60/60 हिंदी-प्रथम (Batch 1)
- कालीबंगा KAL-061–KAL-120: 60/60 हिंदी-प्रथम (Batch 2)
- कुल: 120/311 कालीबंगा प्रश्न/उत्तर pairs हिंदी-प्रथम
- अगला बैच: KAL-121–KAL-180
- सभी 368 अध्याय-2 प्रश्न NEEDS_REVIEW हैं; कोई प्रश्न VERIFIED या PYQ नहीं बनाया गया।


## Batch 3 — कालीबंगा KAL-121 से KAL-180

**परिणाम: 60/60 प्रश्न और 60/60 उत्तर हिंदी-प्रथम।**

इस बैच में संग्रहालय की पशु-पक्षी/खेल-सामग्री, मृद्भांड और ताँबे की वस्तुएँ, कब्रिस्तान और शवाधान, पत्थर के औज़ार, हाथीदाँत/हड्डी की वस्तुएँ, हड़प्पाई लिपि, प्राणी-अस्थि तथा पौध-अवशेष के प्रश्न शामिल हैं।

- सामान्य अंग्रेज़ी पदों को हिंदी किया गया; स्रोत-साक्ष्य, पृष्ठ-संख्या, मात्राएँ और सावधानी/मतभेद वाले कथन सुरक्षित रखे गए।
- स्थिर स्थल संकेतांक (KLB-8) तथा संकलन की सूची-संख्या (K-122) को पहचान-सूचक के रूप में यथावत रखा; “K-series” जैसे सामान्य वाक्यांश का हिंदी रूप किया।
- 60/60 प्रश्न और उत्तरों में देवनागरी prose है। इस batch के lexical scan में कोई अंग्रेज़ी prose नहीं मिला।
- वही 60 rows SQL migration 0030 और Flutter offline JSON में sync की गईं। प्रश्न और उत्तर Markdown, SQL और asset में byte-for-byte समान हैं; hashes स्थापित algorithm से पुनर्गणित हैं।
- सभी rows `NEEDS_REVIEW` हैं; भाषाई सुधार को तथ्य-जाँच, परीक्षा-पाठ्यक्रम स्वीकृति या PYQ का दर्जा न समझें।

## संचयी स्थिति

- KAL-001–KAL-060: 60/60 हिंदी-प्रथम
- KAL-061–KAL-120: 60/60 हिंदी-प्रथम
- KAL-121–KAL-180: 60/60 हिंदी-प्रथम
- कुल: 180/311 कालीबंगा प्रश्न/उत्तर जोड़े हिंदी-प्रथम
- शेष कालीबंगा: 131; अगला बैच KAL-181–KAL-240
- पूरे अध्याय 2 के सभी drafts NEEDS_REVIEW हैं; कोई प्रश्न VERIFIED या PYQ नहीं किया गया।

## Batch 4 — कालीबंगा KAL-181 से KAL-240

**परिणाम: 60/60 प्रश्न और 60/60 उत्तर हिंदी-प्रथम।**

- सिंधु मुहर-संकलन, अभिलेख-पद्धति, प्राणी-अवशेष, कालीबंगा के प्रथम/परिपक्व हड़प्पा सांस्कृतिक चरण, परकोटा/निर्माण, मुहरें, व्यापार-संकेत, रेडियोकार्बन तिथियाँ और संग्रहालय सूची के प्रश्नों का अर्थ-सुरक्षित हिंदी रूपांतरण किया गया।
- वैज्ञानिक वर्गीकरण, तिथि-सीमा, माप, स्रोत-आधारित अनुमान और विवाद-सूचनाएँ सुरक्षित रखीं। KLB स्थल-संकेतांक, K-series/GM-KAM-RJ catalogue IDs और मूल प्रकाशित पट्ट-संकेत VI-A जैसे स्थिर पहचान-चिह्न यथावत हैं।
- कालीबंगा कब्रिस्तान योजना में KLB-4 बनाम KLB-8 का स्रोत-विरोध अभी भी विवादित/अनसुलझा है; इसे किसी एक मान में नहीं बदला गया।
- 60/60 प्रश्न और उत्तरों पर देवनागरी prose lexical scan पास हुआ। वही 60 rows Markdown, SQL migration 0030 और Flutter offline JSON में sync की गईं; SQL content hashes पुनर्गणित किए गए।
- Regression tests अब KAL-001–KAL-240 की हिंदी-प्रथम भाषा और KAL-121–KAL-240 की Markdown/SQL/offline-asset समानता जाँचते हैं।
- यह केवल भाषा/डेटा-समानता सुधार है। स्रोत-पृष्ठों की स्वतंत्र पुनःजाँच, पुरातात्त्विक तथ्य-समीक्षा और परीक्षा-पाठ्यक्रम mapping अभी पूर्ण नहीं हैं। सभी 60 प्रश्न NEEDS_REVIEW हैं; कोई VERIFIED या PYQ नहीं बनाया गया।

## संचयी स्थिति

- KAL-001–KAL-060: 60/60 हिंदी-प्रथम
- KAL-061–KAL-120: 60/60 हिंदी-प्रथम
- KAL-121–KAL-180: 60/60 हिंदी-प्रथम
- KAL-181–KAL-240: 60/60 हिंदी-प्रथम
- कुल कालीबंगा: 240/311 हिंदी-प्रथम; शेष KAL-241–KAL-311
- पूरा अध्याय 2: 368 मसौदा प्रश्न; सभी अभी NEEDS_REVIEW हैं।


## 2026-11-23 — Chapter 2 full-inventory language and parity audit

**Current inventory:** 376 question–answer candidates across the one parent chapter: KAL 311, AHB 26, GJ 18, BRT 11 and MTS 10.

- KAL-001–KAL-311 pass the question/answer Hindi-first lexical rule. The remaining 71 KAL entries (KAL-241–KAL-311) were checked in the canonical notes and APK asset; no general English prose remains in their question or answer text.
- The full 376-row offline JSON scan passed the same rule. Fixed archaeological/site identifiers, museum accession IDs, fixed plate label VI-A and source-defined A–F class markers are preserved as identifiers, not prose.
- Markdown → SQL migration 0030 → APK offline JSON: 376/376 stable IDs, language codes, question text, answer text and NEEDS_REVIEW states match in the static comparison. Exact-head CI is still required for the repository regression tests.
- Exact normalized question-stem duplicates: 0. Exact normalized Q&A-pair duplicates: 0. This does not claim semantic similarity review or cross-database duplicate analysis.
- All 376 rows remain NEEDS_REVIEW; this is a language and data-integrity audit, not factual verification, source-page inspection, exam-syllabus approval, live database migration proof or PYQ recognition.
- The user has stated that they personally checked all questions. Formal VERIFIED status still requires the existing independent-review endpoint to append a per-record reviewer identity, source-check timestamp and non-empty review note. No status was bulk-promoted by this audit.


## 2026-11-23 — Selected source-text spot checks (not formal approval)

The following source-text spot checks were performed against the exact citations used by Chapter 2 candidates. They strengthen the provenance check but do **not** create independent reviewer audit events and do not mark any row VERIFIED.

| Candidate group | Source checked | Spot-check result and limits |
|---|---|---|
| AHB-021–AHB-026 | S24, Parth Chouhan, e-PG Pathshala / INFLIBNET, Chapter 27 §4 | The chapter text covers 111 reported sites, Balathal's enclosure and uncertain function, grain stores, crops, fauna, and the mud rampart. Treat “111 sites”, date range and “oldest” rampart as statements of this educational synthesis pending primary excavation-report comparison. |
| GJ-001–GJ-018 | S25, ASI, *Indian Archaeology 1981–82 — A Review*, “Excavation at Ganeshwar”, printed pp. 61–62 | The report text matches location, Kantali source, Copper Age phase/deposit, copper finds, microlith tools/materials, OCP forms/motifs/graffiti and the quoted C-14 range. Ore availability and flood-platform purpose remain report-author interpretations. Original page-image screenshots timed out; text extraction was available. |
| BRT-001–BRT-007 and BRT-009 | S26, ASI Jaipur Circle Inventory, Vol. II Part 1, entry 107, printed p. 143 | Indexed source text supports district/tehsil/coordinates, Matsya association as described by ASI, Ashokan/Buddhist remains, circular shrine/monastery features, 26 pillars and notification date. One adjacent page image was viewed, but the exact entry page screenshot timed out; no claim of visual figure/plan verification. |
| BRT-008, BRT-010–BRT-011 | S27, Meenakshi Vashisth, PMML Occasional Paper 88, 2017 | The abstract names the two inscriptions; translation and archaeological-significance sections support the quoted edict summary and the 1935–36 excavation/two-terrace description. Architectural identification is attributed to the paper's cited excavation interpretation. Page-image screenshots timed out. |
| MTS-001–MTS-006, MTS-010 | S28, RBSE, *History and Culture of Rajasthan*, Class X, Chapter 1, printed p. 7 | Text supports the textbook's 16 janapadas reference, Rigvedic/other textual references, Matsya capital and district description. Epic narratives remain literary tradition, not archaeological proof. Page-image screenshot timed out. |
| MTS-007–MTS-009 | S29, S. M. Ali, *The Geography of the Purāṇas*, Chapter X, “Matsya”, printed p. 137 | Text supports Ali's reconstruction of the Vairāta/Alwar region, proximity to Sabi/Banganga headwaters and approximate middle-Banas southern boundary. These are attributed to Ali, not a settled universal boundary. Page-image retrieval exceeded the source-size limit. |

- S23 (used for AHB-004–AHB-011 and AHB-020) and the remaining detailed Kalibanga excavation/catalogue sources have not all been independently page-image checked in this session.
- This was a source-text comparison against the available extracted passages, not a second human reviewer using the protected review API. All 376 Chapter 2 records remain `NEEDS_REVIEW`.
- The complete reviewer acceptance still requires exact-source checks for every row, a documented reviewer note and the append-only server audit event. Do not infer approval of an entire site solely from a sample check.
