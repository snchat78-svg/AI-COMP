from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = (
    ROOT / "database" / "migrations" / "0030_import_chapter_2_hindi_draft_one_liners.sql",
    ROOT / "database" / "migrations" / "0031_phase_6_56_ahar_banas_one_liners_027_032.sql",
    ROOT / "database" / "migrations" / "0032_phase_6_56_ahar_banas_one_liners_033_042.sql",
)
CORRECTION_MIGRATION = (
    ROOT / "database" / "migrations" / "0033_phase_6_56_ahar_banas_source_corrections_041_042.sql"
)


def _migration_sql() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS)


def _migration_values() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8").split("VALUES", 1)[1].split("ON CONFLICT DO NOTHING", 1)[0]
        for path in MIGRATIONS
    )


def test_chapter_2_import_contains_all_392_unique_hindi_review_pending_drafts() -> None:
    sql = _migration_sql()
    values = _migration_values()
    row_pattern = re.compile(
        r"^\s+\('ch2_(KAL|AHB|GJ|BRT|MTS)-(\d{3})',.*?, "
        r"'NEEDS_REVIEW', 0\.80, '([0-9a-f]{64})', NULL\),?$"
    )
    records: list[tuple[str, str, str]] = []
    for line in values.splitlines():
        match = row_pattern.match(line)
        if match is not None:
            records.append((match.group(1), match.group(2), match.group(3)))

    assert len(records) == 392
    assert len({(prefix, number) for prefix, number, _ in records}) == 392
    assert len({content_hash for _, _, content_hash in records}) == 392
    assert Counter(prefix for prefix, _, _ in records) == {
        "KAL": 311,
        "AHB": 42,
        "GJ": 18,
        "BRT": 11,
        "MTS": 10,
    }
    assert "ON CONFLICT DO NOTHING" in sql
    assert "'VERIFIED'" not in values
    assert "NULL)" in values


def test_ahar_banas_source_correction_migration_only_updates_unreviewed_rows() -> None:
    sql = CORRECTION_MIGRATION.read_text(encoding="utf-8")
    for draft_id in ("ch2_AHB-041", "ch2_AHB-042"):
        assert f"WHERE one_liner_id = '{draft_id}'" in sql
        assert "AND verification_status = 'NEEDS_REVIEW'" in sql
        assert "AND reviewed_at IS NULL" in sql
    assert sql.count("UPDATE question_bank_one_liners") == 2
    assert "'VERIFIED'" not in sql


def test_chapter_2_import_keeps_the_five_existing_canonical_concepts() -> None:
    sql = _migration_sql()
    for concept_id in (
        "catalog.rajasthan_history_ancient_history_kalibangan",
        "catalog.rajasthan_history_ancient_history_ahar_banas_culture",
        "catalog.rajasthan_history_ancient_history_ganeshwar_jodhpura_culture",
        "catalog.rajasthan_history_ancient_history_bairat",
        "catalog.rajasthan_history_ancient_history_matsya_janapada",
    ):
        assert concept_id in sql


def test_full_chapter_2_markdown_sql_and_offline_asset_match() -> None:
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
    sql = _migration_sql()
    values = _migration_values()

    expected_ids = {
        f"ch2_{prefix}-{number:03d}"
        for prefix, count in {"KAL": 311, "AHB": 42, "GJ": 18, "BRT": 11, "MTS": 10}.items()
        for number in range(1, count + 1)
    }
    asset_rows = {row["one_liner_id"]: row for row in asset}
    assert len(asset_rows) == 392
    assert set(asset_rows) == expected_ids

    note_rows = {}
    for line in notes.splitlines():
        if not re.match(r"^\| (?:KAL|AHB|GJ|BRT|MTS)-\d{3} \|", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        note_rows["ch2_" + cells[0]] = (cells[1], cells[2])
    assert set(note_rows) == expected_ids

    row_pattern = re.compile(
        r"^\s+\('(ch2_(?:KAL|AHB|GJ|BRT|MTS)-\d{3})', "
        r"'([^']+)', '((?:[^']|'')*)', '((?:[^']|'')*)', "
        r"'([^']+)', '([^']*)', '((?:[^']|'')*)', "
        r"'(NEEDS_REVIEW)', (0\.80), '([0-9a-f]{64})', NULL\),?$"
    )
    migration_rows = {}
    for line in values.splitlines():
        match = row_pattern.match(line)
        if match is None:
            continue
        migration_rows[match.group(1)] = {
            "question_text": match.group(3).replace("''", "'"),
            "answer_text": match.group(4).replace("''", "'"),
            "language_code": match.group(5),
            "source_url": match.group(6),
            "source_evidence": match.group(7).replace("''", "'"),
            "verification_status": match.group(8),
            "content_hash": match.group(10),
        }

    correction_sql = CORRECTION_MIGRATION.read_text(encoding="utf-8")
    correction_pattern = re.compile(
        r"UPDATE question_bank_one_liners\s+SET\s+"
        r"question_text = '([^']*)',\s+answer_text = '([^']*)',\s+"
        r"source_url = '([^']*)',\s+source_evidence = '([^']*)',\s+"
        r"content_hash = '([0-9a-f]{64})'\s+"
        r"WHERE one_liner_id = '(ch2_AHB-\d{3})'\s+"
        r"AND verification_status = 'NEEDS_REVIEW'\s+"
        r"AND reviewed_at IS NULL;",
        re.DOTALL,
    )
    corrected_ids = set()
    for match in correction_pattern.finditer(correction_sql):
        draft_id = match.group(6)
        corrected_ids.add(draft_id)
        migration_rows[draft_id].update({
            "question_text": match.group(1),
            "answer_text": match.group(2),
            "source_url": match.group(3),
            "source_evidence": match.group(4),
            "content_hash": match.group(5),
        })
    assert corrected_ids == {"ch2_AHB-041", "ch2_AHB-042"}
    assert set(migration_rows) == expected_ids

    for one_liner_id in expected_ids:
        question, answer = note_rows[one_liner_id]
        local = asset_rows[one_liner_id]
        migrated = migration_rows[one_liner_id]
        assert local["question_text"] == migrated["question_text"] == question
        assert local["answer_text"] == migrated["answer_text"] == answer
        assert local["language_code"] == migrated["language_code"] == "hi"
        assert local["verification_status"] == migrated["verification_status"] == "NEEDS_REVIEW"
        normalized_question = " ".join(question.casefold().split())
        normalized_answer = " ".join(answer.casefold().split())
        payload = f"{normalized_question}\\n{normalized_answer}"
        expected_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        assert migrated["content_hash"] == expected_hash
