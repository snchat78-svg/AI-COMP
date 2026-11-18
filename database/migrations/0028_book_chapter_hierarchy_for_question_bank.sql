-- Phase 6.56: map the four confirmed Chapter-2 ancient-site concepts
-- to the book-aligned parent chapter while retaining every canonical concept_id.
-- This changes catalogue navigation metadata only; it does not publish draft Q&A
-- or assert exam-specific syllabus verification.

BEGIN;

UPDATE concepts AS c
SET
    label = mapped.label,
    topic = 'राजस्थान के प्राचीन सभ्यता स्थल',
    subtopic = mapped.subtopic
FROM (
    VALUES
        (
            'catalog.rajasthan_history_ancient_history_kalibangan',
            'कालीबंगा',
            'कालीबंगा'
        ),
        (
            'catalog.rajasthan_history_ancient_history_ahar_banas_culture',
            'आहड़-बनास संस्कृति',
            'आहड़-बनास संस्कृति'
        ),
        (
            'catalog.rajasthan_history_ancient_history_ganeshwar_jodhpura_culture',
            'गणेश्वर-जोधपुरा संस्कृति',
            'गणेश्वर-जोधपुरा संस्कृति'
        ),
        (
            'catalog.rajasthan_history_ancient_history_bairat',
            'बैराठ / विराटनगर',
            'बैराठ / विराटनगर'
        )
) AS mapped(concept_id, label, subtopic)
WHERE c.concept_id = mapped.concept_id;

COMMIT;
