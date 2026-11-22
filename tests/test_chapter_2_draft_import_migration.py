from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "database"
    / "migrations"
    / "0030_import_chapter_2_hindi_draft_one_liners.sql"
)


def test_chapter_2_import_contains_all_368_unique_hindi_review_pending_drafts() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    values = sql.split("VALUES", 1)[1].split("ON CONFLICT DO NOTHING", 1)[0]
    row_pattern = re.compile(
        r"^\s+\('ch2_(KAL|AHB|GJ|BRT|MTS)-(\d{3})',.*?, "
        r"'NEEDS_REVIEW', 0\.80, '([0-9a-f]{64})', NULL\),?$"
    )
    records: list[tuple[str, str, str]] = []
    for line in values.splitlines():
        match = row_pattern.match(line)
        if match is not None:
            records.append((match.group(1), match.group(2), match.group(3)))

    assert len(records) == 368
    assert len({(prefix, number) for prefix, number, _ in records}) == 368
    assert len({content_hash for _, _, content_hash in records}) == 368
    assert Counter(prefix for prefix, _, _ in records) == {
        "KAL": 311,
        "AHB": 20,
        "GJ": 18,
        "BRT": 9,
        "MTS": 10,
    }
    assert "ON CONFLICT DO NOTHING" in sql
    assert "'VERIFIED'" not in values
    assert "NULL)" in values


def test_chapter_2_import_keeps_the_five_existing_canonical_concepts() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for concept_id in (
        "catalog.rajasthan_history_ancient_history_kalibangan",
        "catalog.rajasthan_history_ancient_history_ahar_banas_culture",
        "catalog.rajasthan_history_ancient_history_ganeshwar_jodhpura_culture",
        "catalog.rajasthan_history_ancient_history_bairat",
        "catalog.rajasthan_history_ancient_history_matsya_janapada",
    ):
        assert concept_id in sql


def test_kalibanga_batch_3_matches_markdown_migration_and_offline_asset() -> None:
    root = Path(__file__).resolve().parents[1]
    notes = (
        root
        / "docs"
        / "study-notes"
        / "rajasthan-history"
        / "ancient-history"
        / "ancient-civilization-sites.md"
    ).read_text(encoding="utf-8")
    asset = json.loads(
        (
            root
            / "apps"
            / "mobile"
            / "assets"
            / "question_bank"
            / "rajasthan_history_chapter_2_drafts.json"
        ).read_text(encoding="utf-8")
    )
    sql = MIGRATION.read_text(encoding="utf-8")
    values = sql.split("VALUES", 1)[1].split("ON CONFLICT DO NOTHING", 1)[0]
    row_pattern = re.compile(
        r"^\s+\('(ch2_KAL-(?:12[1-9]|1[3-7]\d|180))', "
        r"'([^']+)', '([^']*)', '([^']*)', 'hi', '([^']+)', "
        r"'([^']*)', 'NEEDS_REVIEW', 0\.80, '([0-9a-f]{64})', NULL\),?$"
    )
    migration_rows = {
        match.group(1): {
            "question_text": match.group(3),
            "answer_text": match.group(4),
            "content_hash": match.group(7),
        }
        for line in values.splitlines()
        if (match := row_pattern.match(line)) is not None
    }
    asset_rows = {
        row["one_liner_id"]: row
        for row in asset
        if row["one_liner_id"].startswith("ch2_KAL-")
    }
    note_rows = {}
    for line in notes.splitlines():
        if not re.match(r"^\| KAL-(?:12[1-9]|1[3-7]\d|180) \|", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        note_rows["ch2_" + cells[0]] = (cells[1], cells[2])

    expected = {f"ch2_KAL-{number:03d}" for number in range(121, 181)}
    assert set(migration_rows) == expected
    assert expected.issubset(asset_rows)
    assert set(note_rows) == expected

    for one_liner_id in expected:
        question, answer = note_rows[one_liner_id]
        local = asset_rows[one_liner_id]
        migrated = migration_rows[one_liner_id]
        assert local["question_text"] == migrated["question_text"] == question
        assert local["answer_text"] == migrated["answer_text"] == answer
        assert local["verification_status"] == "NEEDS_REVIEW"
        assert local["language_code"] == "hi"
        normalized_question = " ".join(question.casefold().split())
        normalized_answer = " ".join(answer.casefold().split())
        payload = f"{normalized_question}\\n{normalized_answer}"
        expected_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        assert migrated["content_hash"] == expected_hash
