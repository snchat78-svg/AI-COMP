from __future__ import annotations

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
