# राजस्थान के पाँच विषय — Parallel Offline Coverage Checkpoint

**तिथि:** 27 नवम्बर 2026  
**कार्यान्वयन शाखा:** `feature/rajasthan-parallel-offline-study-library`  
**नियंत्रक सूची:** [QUESTION_BANK_CONTENT_COVERAGE.csv](../QUESTION_BANK_CONTENT_COVERAGE.csv)  
**कैनोनिकल taxonomy:** [MASTER_SUBJECT_TOPIC_STRUCTURE.md](MASTER_SUBJECT_TOPIC_STRUCTURE.md)

## Product direction

अब Rajasthan lane के पाँच विषयों पर parallel काम होगा: राजस्थान इतिहास, भूगोल, राजव्यवस्था एवं प्रशासन, कला एवं संस्कृति और अर्थव्यवस्था। हर विषय अपने मौजूदा स्थायी concept IDs और Subject → Main Topic → Subtopic क्रम में रहेगा। किसी एक अध्याय को दूसरे Rajasthan विषय के काम को रोकने की आवश्यकता नहीं; लेकिन एक parent topic के भीतर उसके child-subtopics बिखरेंगे नहीं।

यह पाँच विषयों का offline first-pass bundle है, 137 concepts का पूर्ण-content completion नहीं। जिन concepts में प्रश्न नहीं हैं वे भी ऐप में दिखाई देते हैं और स्पष्ट रूप से “प्रश्न तैयारी में” चिह्नित हैं। प्रश्न-संख्या कोई completion प्रमाण नहीं।

## Offline APK bundle — वर्तमान candidate snapshot

| विषय | Master concepts | Bundled One-Liners |
|---|---:|---:|
| राजस्थान इतिहास | 34 | 398 |
| राजस्थान भूगोल | 32 | 36 |
| राजस्थान राजव्यवस्था एवं प्रशासन | 21 | 27 |
| राजस्थान कला एवं संस्कृति | 29 | 9 |
| राजस्थान अर्थव्यवस्था | 21 | 16 |
| **कुल** | **137** | **486** |

इन 486 candidate rows के लिए:
- सभी `language_code=hi`, HTTPS source URL और evidence locator रखते हैं।
- सभी `NEEDS_REVIEW` हैं; कोई self-approved `VERIFIED` record नहीं बनाया गया।
- ये AI-authored/paraphrased study notes हैं; वास्तविक PYQ नहीं।
- तीन offline assets: Chapter-2 history drafts, parallel subject drafts और Rajasthan offline catalogue।
- exact normalized question-stem audit: 486 IDs unique और 0 exact duplicate stems।
- राजस्थान भूगोल का RGEO-011 दो canonical concepts (बनास और चंबल) को cross-reference करता है; मूल प्रश्न एक ही बार रखा गया है।

## विषयवार source batches

**भूगोल — 36:** RGEO-001–029, पहले से मौजूद 7 official-source seed candidates सहित। प्राथमिक स्रोत: राजस्थान सरकार “Rajasthan at a Glance” और वन विभाग की संरक्षित क्षेत्र तालिका। वर्षा/तापमान/क्षेत्र-वर्गीकरण को स्रोत के scope में ही रखा गया है।

**राजव्यवस्था एवं प्रशासन — 27:** RPO-001–027। स्रोतों में राजस्थान विधानसभा, RPSC, सर्वोच्च न्यायालय e-Committee, राज्य वित्त आयोग की रिपोर्ट और लोकायुक्त अधिनियम/सचिवालय शामिल हैं। कानून/नियम का वर्तमान संशोधित संस्करण स्वतंत्र रूप से पुनः जाँचना बाकी है।

**कला एवं संस्कृति — 9:** कालबेलिया परंपरा के पहले से मौजूद 3 candidate + UNESCO Intangible Cultural Heritage विवरण से 6 नये Q&A। बाकी 28 concepts अभी content gaps हैं।

**अर्थव्यवस्था — 16:** राजस्थान सरकार की *Economic Review 2025-26* से कृषि, पशुपालन, ऊर्जा, पर्यटन और निर्यात के Q&A। हर बदलने वाले आँकड़े के प्रश्न में वित्त-वर्ष/दिसम्बर 2025 जैसी cut-off रखी गई है। PDF text-layer locators मिले हैं; संबंधित पृष्ठों की image-level visual review अभी बाकी है।

**इतिहास — 398:** राजस्थान इतिहास पुस्तक-अध्याय 2 के पाँच child-sites; यह अभी पूरा पुस्तक-अध्याय या आधिकारिक परीक्षा syllabus completion नहीं है।

## ऐप में अनुभव

Dashboard → **Open Rajasthan Offline Study Library** → विषय → मुख्य topic → उप-विषय → हिंदी प्रश्न/उत्तर/स्रोत। यह offline route API connection के बिना उपलब्ध होगा। खाली concepts छिपाए नहीं जाएँगे। Verified One-Liners, pending drafts और वास्तविक previous-paper questions की existing separation बनी रहेगी।

## अगली प्राथमिकताएँ

1. Exact-head Flutter analysis/widget tests और release APK build।
2. 486-row offline bundle integrity, duplicate/source/status tests।
3. Pending content को नियंत्रित migration के माध्यम से server question bank में लाने से पहले unique key/hash parity test; live DB status अभी NOT_QUERIED।
4. पाँच Rajasthan subjects के बचे हुए concept gaps पर छोटे source-backed parallel batches; विशेष रूप से history chapter 3 onwards, geography, polity, art/culture और economy।
5. PDF page-image visual review, legal/policy currentness, official exam syllabus mapping और independent reviewer audit।
6. उसके बाद ही approved study notes से practice MCQ; वास्तविक PYQ अलग रखे जाएँ।

**स्थिति:** Offline library implementation branch में है; CI/APK और live DB publication अभी सत्यापित नहीं हैं। Phase 6.56/6.57/6.58 के canonical states Phase Registry से ही लिए जाएँ।


## 2026-11-27 — APK and merge acceptance

- PR #135 merged into main at `706fd541d100a0fd8a1b2ccae2886409c14fa449`.
- Exact-head backend workflow [45958520679](https://github.com/snchat78-svg/AI-COMP/actions/runs/45958520679) passed pytest and API container build; exact-head Flutter workflow [45958520684](https://github.com/snchat78-svg/AI-COMP/actions/runs/45958520684) passed analyze, all widget/client tests, release APK build, artifact verification and upload.
- APK artifact [15179534142](https://github.com/snchat78-svg/AI-COMP/actions/runs/45958520684/artifacts/15179534142). SHA-256 of APK: `4b0272d1e6603f7c67654b5bf846e3a8fbc3bdc789fca391573b8f3aa2bb389c`. This is release-mode CI APK using debug signing, not production/store signing.
- APK contents rechecked: 398 History Chapter-2 candidates + 88 cross-subject candidates = 486 unique IDs and zero exact normalized duplicate stems. All Hindi, HTTPS/evidence-backed, NEEDS_REVIEW.
- Coverage status: 137 catalogue concepts; 32 concepts with candidate questions; 105 concepts with no questions. Keep blanks visible and create parallel important-question batches; do not fabricate fill or claim full coverage.
