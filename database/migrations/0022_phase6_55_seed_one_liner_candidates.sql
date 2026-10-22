-- Phase 6.55: source-backed starter candidates for editorial review.
-- These are NOT VERIFIED. Only the independent review endpoint can promote a
-- candidate; this migration does not set reviewed_at/reviewed_by/source_checked_at.
BEGIN;

INSERT INTO question_bank_one_liners (
    one_liner_id, concept_id, question_text, answer_text, language_code,
    source_url, source_evidence, verification_status, importance_score,
    content_hash, reviewed_at
)
VALUES
(
    'p655_luni_desert_system',
    'catalog.rajasthan_geography_rivers_and_drainage_luni_river',
    'राजस्थान के मरुस्थलीय क्षेत्र की प्रमुख नदी प्रणाली कौन-सी है?',
    'लूणी नदी और उसकी सहायक नदियाँ।',
    'hi',
    'https://environment.rajasthan.gov.in/content/environment/en/rsbb/about-rajasthan/rajasthan-at-a-glance.html',
    'Rajasthan at a Glance, northwestern Rajasthan section: identifies the Luni River and its tributaries as the desert region''s major river system.',
    'NEEDS_REVIEW', 0.95,
    'ff783e3d75f09f78d4b2dd7eab4916d125c353030d21d89b38f8a80d8657eef3',
    NULL
),
(
    'p655_luni_rann_kutch',
    'catalog.rajasthan_geography_rivers_and_drainage_luni_river',
    'लूणी नदी किस बड़े आर्द्र क्षेत्र की ओर बहती है?',
    'दक्षिण-पश्चिम दिशा में गुजरात के ग्रेट रण ऑफ कच्छ की ओर।',
    'hi',
    'https://environment.rajasthan.gov.in/content/environment/en/rsbb/about-rajasthan/rajasthan-at-a-glance.html',
    'Rajasthan at a Glance: describes the Luni as flowing southwest into the Great Rann of Kutch wetland in neighbouring Gujarat.',
    'NEEDS_REVIEW', 0.90,
    '9424f0d6e7b2b8442e3e23d9535d8881b876e19f3376ed4ad2977403e1d495de',
    NULL
),
(
    'p655_thar_pakistan',
    'catalog.rajasthan_geography_location_and_physical_features_thar_desert',
    'राजस्थान के उत्तर-पश्चिमी भाग का बड़ा हिस्सा किस मरुस्थल से ढका है?',
    'थार मरुस्थल।',
    'hi',
    'https://environment.rajasthan.gov.in/content/environment/en/rsbb/about-rajasthan/rajasthan-at-a-glance.html',
    'Rajasthan at a Glance: describes most of northwestern Rajasthan as covered by the Thar Desert, which extends into adjoining Pakistan.',
    'NEEDS_REVIEW', 0.90,
    'cd86efbe1f9786e918b5335a959ad25f8dea648e97cb328567c6aadf6b431641',
    NULL
),
(
    'p655_aravalli_rain_shadow',
    'catalog.rajasthan_geography_location_and_physical_features_aravalli_range',
    'राजस्थान के उत्तर-पश्चिमी क्षेत्र में वर्षा-छाया प्रभाव से जुड़ी पर्वतमाला कौन-सी है?',
    'अरावली पर्वतमाला।',
    'hi',
    'https://environment.rajasthan.gov.in/content/environment/en/rsbb/about-rajasthan/rajasthan-at-a-glance.html',
    'Rajasthan at a Glance: explains that the Aravalli Range runs parallel to the moisture-bearing southwest monsoon winds, leaving northwestern Rajasthan in a rain shadow.',
    'NEEDS_REVIEW', 0.85,
    '72e617890ea441dc8569ec6edfe30b7b615fa7e18b63fb243b3aa43524c2b57d',
    NULL
),
(
    'p655_banas_chambal_east',
    'catalog.rajasthan_geography_rivers_and_drainage_banas_river',
    'राजस्थान के पूर्वी और दक्षिण-पूर्वी भागों का अपवाह किन दो प्रमुख नदियों से होता है?',
    'बनास और चंबल नदियों से।',
    'hi',
    'https://environment.rajasthan.gov.in/content/environment/en/rsbb/about-rajasthan/rajasthan-at-a-glance.html',
    'Rajasthan at a Glance: names the Banas and Chambal rivers as draining eastern and southeastern Rajasthan.',
    'NEEDS_REVIEW', 0.85,
    '53ba36daf37cc5e59197b4c5c8e681355ff181dcf4774555d65ab9397610bcbc',
    NULL
),
(
    'p655_keoladeo_district',
    'catalog.rajasthan_geography_climate_and_environment_national_parks_and_sanctuaries',
    'राजस्थान वन विभाग की राष्ट्रीय उद्यान सूची में केवलादेव राष्ट्रीय उद्यान किस जिले में दर्ज है?',
    'भरतपुर जिले में।',
    'hi',
    'https://forest.rajasthan.gov.in/content/raj/forest/en/aboutus/forest-statistics/general-introduction1/national-parks-and-sanctuaries-in-rajasthan.html',
    'Rajasthan Forest Department, National Parks table: lists Keoladeo National Park in Bharatpur district. District attribution follows this page''s table.',
    'NEEDS_REVIEW', 0.90,
    'e3b52f09384885db7122c4ddeed9d5c4bdf6f4960779d16970d8253d8e6fc864',
    NULL
),
(
    'p655_ranthambore_district',
    'catalog.rajasthan_geography_climate_and_environment_national_parks_and_sanctuaries',
    'राजस्थान वन विभाग की राष्ट्रीय उद्यान सूची में रणथम्भौर राष्ट्रीय उद्यान किस जिले में दर्ज है?',
    'सवाई माधोपुर जिले में।',
    'hi',
    'https://forest.rajasthan.gov.in/content/raj/forest/en/aboutus/forest-statistics/general-introduction1/national-parks-and-sanctuaries-in-rajasthan.html',
    'Rajasthan Forest Department, National Parks table: lists Ranthambore National Park in Sawai Madhopur district. District attribution follows this page''s table.',
    'NEEDS_REVIEW', 0.90,
    '122ad414143888067f296be09fc02bbf79560db111634793f025b464a11f583b',
    NULL
),
(
    'p655_kalbelia_year',
    'catalog.rajasthan_art_and_culture_folk_dance_and_music_kalbelia_dance',
    'राजस्थान के कालबेलिया लोकगीत और नृत्य को यूनेस्को की प्रतिनिधि सूची में किस वर्ष अंकित किया गया?',
    '2010 में।',
    'hi',
    'https://ich.unesco.org/en/RL/kalbelia-folk-songs-and-dances-of-rajasthan-00340?lang=en',
    'UNESCO Intangible Cultural Heritage entry: records inscription on the Representative List in 2010.',
    'NEEDS_REVIEW', 0.95,
    '41e567247959006d117a47cc57122005ac1569d2099d2a5fa08c1c10ea0fe208',
    NULL
),
(
    'p655_kalbelia_instruments',
    'catalog.rajasthan_art_and_culture_folk_dance_and_music_kalbelia_dance',
    'यूनेस्को के कालबेलिया विवरण में पुरुष कलाकार किन दो वाद्यों के साथ नृत्य-संगीत में साथ देते हैं?',
    'खंजरी और पूंगी।',
    'hi',
    'https://ich.unesco.org/en/RL/kalbelia-folk-songs-and-dances-of-rajasthan-00340?lang=en',
    'UNESCO Intangible Cultural Heritage entry: describes male performers accompanying dancers with the khanjari percussion instrument and poongi wind instrument.',
    'NEEDS_REVIEW', 0.85,
    '9df027539da459ff92ce028c780b150ee4e9b98a15897fcfb618076975df934b',
    NULL
),
(
    'p655_kalbelia_snake',
    'catalog.rajasthan_art_and_culture_folk_dance_and_music_kalbelia_dance',
    'यूनेस्को के विवरण के अनुसार कालबेलिया नृत्य की घूमती गतियाँ किसकी चाल की याद दिलाती हैं?',
    'साँप की चाल की।',
    'hi',
    'https://ich.unesco.org/en/RL/kalbelia-folk-songs-and-dances-of-rajasthan-00340?lang=en',
    'UNESCO Intangible Cultural Heritage entry: compares the dancers'' swirling movements to a serpent.',
    'NEEDS_REVIEW', 0.80,
    '3f7fe7f6b64ef478ab52c187a932328a7ad97f38ae174e2bba426d30d6fbdf45',
    NULL
)
ON CONFLICT (concept_id, language_code, content_hash) DO NOTHING;

COMMIT;
