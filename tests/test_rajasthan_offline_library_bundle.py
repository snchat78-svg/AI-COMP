from __future__ import annotations

import json
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "apps" / "mobile" / "assets" / "question_bank"


def _normalise(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _bundle():
    history = json.loads((ASSETS / "rajasthan_history_chapter_2_drafts.json").read_text(encoding="utf-8"))
    parallel = json.loads((ASSETS / "rajasthan_parallel_subjects_drafts.json").read_text(encoding="utf-8"))
    catalogue = json.loads((ASSETS / "rajasthan_offline_catalogue.json").read_text(encoding="utf-8"))
    return history, parallel["items"], catalogue


def test_rajasthan_offline_bundle_has_five_subjects_137_concepts_and_486_candidates():
    history, parallel, catalogue = _bundle()
    assert len(history) == 398
    assert len(parallel) == 88
    assert len(history) + len(parallel) == 486
    assert [subject["subject_label"] for subject in catalogue["subjects"]] == [
        "राजस्थान इतिहास",
        "राजस्थान भूगोल",
        "राजस्थान राजव्यवस्था एवं प्रशासन",
        "राजस्थान कला एवं संस्कृति",
        "राजस्थान अर्थव्यवस्था",
    ]
    concepts = [
        subtopic["concept_id"]
        for subject in catalogue["subjects"]
        for group in subject["topic_groups"]
        for subtopic in group["subtopics"]
    ]
    assert len(concepts) == 137
    assert len(concepts) == len(set(concepts))


def test_all_offline_candidates_are_hindi_source_attributed_and_review_pending():
    history, parallel, _ = _bundle()
    items = [*history, *parallel]
    assert len({item["one_liner_id"] for item in items}) == 486
    for item in items:
        assert item["language_code"] == "hi", item["one_liner_id"]
        assert item["verification_status"] == "NEEDS_REVIEW", item["one_liner_id"]
        assert item["question_text"].strip(), item["one_liner_id"]
        assert item["answer_text"].strip(), item["one_liner_id"]
        assert item["source_url"].startswith("https://"), item["one_liner_id"]
        assert item["source_evidence"].strip(), item["one_liner_id"]


def test_offline_bundle_has_no_exact_normalised_duplicate_question_stems():
    history, parallel, _ = _bundle()
    items = [*history, *parallel]
    stems = [_normalise(item["question_text"]) for item in items]
    assert len(stems) == 486
    assert len(stems) == len(set(stems))


def test_every_candidate_and_cross_reference_resolves_to_the_master_catalogue():
    history, parallel, catalogue = _bundle()
    concepts = {
        subtopic["concept_id"]
        for subject in catalogue["subjects"]
        for group in subject["topic_groups"]
        for subtopic in group["subtopics"]
    }
    for item in [*history, *parallel]:
        assert item["concept_id"] in concepts, item["one_liner_id"]
        for related_id in item.get("related_concept_ids", []):
            assert related_id in concepts, item["one_liner_id"]


def test_parallel_subject_draft_counts_match_the_five_subject_dashboard():
    _, parallel, _ = _bundle()
    counts = Counter(item["subject"] for item in parallel)
    assert counts == {
        "राजस्थान भूगोल": 36,
        "राजस्थान राजव्यवस्था एवं प्रशासन": 27,
        "राजस्थान कला एवं संस्कृति": 9,
        "राजस्थान अर्थव्यवस्था": 16,
    }
