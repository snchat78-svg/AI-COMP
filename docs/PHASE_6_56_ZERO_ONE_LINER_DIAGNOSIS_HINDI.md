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
