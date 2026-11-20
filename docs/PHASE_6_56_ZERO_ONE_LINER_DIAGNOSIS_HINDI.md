# Phase 6.56 — APK में शून्य One-Liner प्रश्न: कारण और समाधान

**तारीख:** 20 नवम्बर 2026  
**स्थिति:** कोड-स्तरीय कारण की पुष्टि; live database import और स्वतंत्र समीक्षा लंबित।

## शून्य क्यों दिखता है?

1. `PostgresTopicQuestionBankRepository.list_topics()` verified count केवल `verification_status='VERIFIED'` पर गिनता है।
2. `list_one_liners()` का default `verified_only=True` है। Learner API pending drafts नहीं दिखाती।
3. APK इसी सुरक्षित learner API को कॉल करती है।
4. अध्याय 2 के 368 प्रश्न GitHub Markdown/CSV notes में हैं; Git files अपने-आप PostgreSQL में insert नहीं होते।
5. Migration 0022 में केवल 10 starter प्रश्न हैं और सभी `NEEDS_REVIEW` हैं।
6. Render workspace में API service live मिली, लेकिन कोई Render-managed PostgreSQL नहीं मिला। External DB संभव है; live DB count और migration स्थिति अभी सत्यापित नहीं हैं।

## इस बदलाव में

- Migration 0029 सभी starter subjects, parent topics और child labels को हिंदी में रखेगी; canonical concept IDs स्थिर रहेंगे।
- अध्याय 2 के पाँचों child topics एक ही parent “राजस्थान के प्राचीन सभ्यता स्थल” में होंगे।
- मोबाइल में हिंदी display-label fallback map भी है: पुराना API/database अभी अंग्रेज़ी नाम लौटाए तब भी विषय, मुख्य अध्याय और उप-विषय हिंदी दिखेंगे; API को भेजे जाने वाले वास्तविक subject IDs अपरिवर्तित रहेंगे। नवीन migration 0029 DB स्तर पर भी यही labels हिंदी करती है।
- मोबाइल Question Bank के navigation, खोज, empty/error states, Q&A labels और source labels हिंदी होंगे।
- किसी unreviewed candidate को VERIFIED नहीं किया जाएगा।

## प्रश्न publish करने का सुरक्षित तरीका

368 Q&A drafts को पहले existing authoring route से `NEEDS_REVIEW` के रूप में live DB में लोड करना होगा। फिर स्वतंत्र reviewer मूल स्रोत खोलेगा, प्रश्न और उत्तर की पुष्टि करेगा, हिंदी wording और topic/duplicate जाँचेगा और अलग reviewer credential से audit note के साथ निर्णय देगा। केवल VERIFIED items learner APK में आएँगे।

## शेष काम

- External DB को secrets खोले बिना पहचानना और migration status जाँचना।
- Approved migration लागू करना।
- 368 Hindi drafts का idempotent import as NEEDS_REVIEW।
- Independent source-by-source review और publishing।
- Authenticated learner API तथा APK में वास्तविक counts की पुष्टि।
- Exact-head backend/Flutter CI और release APK build + verification।

**साफ सीमा:** इस documentation या migration को GitHub में जोड़ने से live DB नहीं बदलता। समीक्षा से पहले drafts publish करना उचित नहीं है।


## 2026-11-20 — समाधान: 368 AI drafts अलग pending lane में

- Chapter 2 source-of-record से 368 Hindi Q&A rows निकाली गईं: KAL 311, AHB 20, GJ 18, BRT 9, MTS 10। हर row में प्रश्न, उत्तर और evidence locator है।
- Migration `0030_import_chapter_2_hindi_draft_one_liners.sql` इनको existing concept IDs और stable draft references के साथ `NEEDS_REVIEW` में insert करती है। `ON CONFLICT DO NOTHING` re-run safety देती है। Hash convention को migration 0022 की existing known content hash से मिलाया गया।
- नया learner route `GET /api/v1/learners/{learner_id}/question-bank/pending-one-liners` सिर्फ `DRAFT/NEEDS_REVIEW` लौटाता है। पुराना `/one-liners` route अभी भी सिर्फ `VERIFIED` लौटाता है।
- Flutter verified और pending lists अलग-अलग load करता है। Pending card पर “AI मसौदा — समीक्षा बाकी” chip, unverified source locator और स्पष्ट note दिखेगा। Previous-year questions अलग lane में रहेंगे।
- Subject/main-topic/subtopic catalogue अब pending counts भी दिखाता है; verified count नहीं बढ़ता।
- Live database migration अभी applied/verified नहीं है; सही DB पर controlled workflow के बाद ही APK में imported drafts दिखाई देंगे। सभी rows independent reviewer तक NEEDS_REVIEW रहेंगी।
