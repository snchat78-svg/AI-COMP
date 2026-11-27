-- Phase 6.56 content correction: tighten AHB-041 and AHB-042 source wording.
-- Migration 0032 may already have been applied. This forward-only migration updates
-- only records that are still unreviewed; it never overwrites a reviewer decision.
BEGIN;

UPDATE question_bank_one_liners
SET
    question_text = 'राजस्थान बोर्ड की कक्षा 10 की पुस्तक के अनुसार आहड़ में सबसे पहले उत्खनन किसने किया और उसके बाद किन पुरातत्वविदों ने कार्य किया?',
    answer_text = 'पुस्तक के अनुसार 1953 में अक्षयकीर्ति व्यास ने प्रारंभिक उत्खनन किया; बाद में रतन चंद्र अग्रवाल और एच. डी. सांकलिया ने उत्खनन कार्य किया।',
    source_url = 'https://rajeduboard.rajasthan.gov.in/books-2019/books-2022/cls10/HistorynCulture.pdf',
    source_evidence = 'AHB-041 — S32 — राजस्थान माध्यमिक शिक्षा बोर्ड, History and Culture of Rajasthan, कक्षा 10, मुद्रित पृ. 4, Ahar अनुच्छेद; प्रश्न उसी पुस्तक में दिए उत्खनन-क्रम को सारांशित करता है।',
    content_hash = '59f0a57967a534c8a5ab35ef99c62aaa6419342ae0e6f5678ab9bcd97e38f786'
WHERE one_liner_id = 'ch2_AHB-041'
  AND verification_status = 'NEEDS_REVIEW'
  AND reviewed_at IS NULL;

UPDATE question_bank_one_liners
SET
    question_text = 'शोध के अनुसार आहड़ संस्कृति में हड़प्पा सभ्यता के साथ बढ़ता व्यापारिक संपर्क कब से बताया गया है?',
    answer_text = 'लगभग 2600 ईसा पूर्व के बाद; लेखक इसे आहड़ संस्कृति के विकास और उत्कर्ष से जोड़ते हैं।',
    source_url = 'https://ignca.gov.in/Asi_data/87125.pdf',
    source_evidence = 'AHB-042 — S30 — Shinde, Possehl और Sinha-Deshpande, The Ceramic Assemblage in Protohistoric Mewar, Puratattva 32 (2001–02), मुद्रित पृ. 5, Introduction; लेख में Harappans के साथ growing trade contact after 2600 B.C. स्पष्ट कहा गया है।',
    content_hash = '491b1c5524cd4c70a30d186d20e61075a9bc08d9a19e7181885a62138b4eab6d'
WHERE one_liner_id = 'ch2_AHB-042'
  AND verification_status = 'NEEDS_REVIEW'
  AND reviewed_at IS NULL;

COMMIT;
