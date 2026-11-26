from __future__ import annotations

import json
import re
from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "study-notes"
    / "rajasthan-history"
    / "ancient-history"
    / "ancient-civilization-sites.md"
)


def _chapter_rows() -> dict[str, tuple[str, str, str]]:
    result: dict[str, tuple[str, str, str]] = {}
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        if not line.startswith(("| KAL-", "| AHB-")):
            continue
        columns = [value.strip() for value in line.strip("|").split("|")]
        if len(columns) < 4:
            continue
        result[columns[0]] = (columns[1], columns[2], columns[3])
    return result


def test_first_180_kalibangan_one_liners_are_hindi_first() -> None:
    rows = _chapter_rows()
    expected_ids = {f"KAL-{number:03d}" for number in range(1, 241)}
    assert expected_ids.issubset(rows)

    for draft_id in sorted(expected_ids):
        question, answer, evidence = rows[draft_id]
        # KLB site IDs, K-series catalogue IDs, NMMA catalogue IDs, source plate IDs
        # and source-defined fabric classes A-F are identifiers, not English prose.
        prose = re.sub(
            r"\b(?:KLB-(?:I{1,2}|\d+)|K-\d+|GM-KAM-RJ-\d+|VI-A|[A-F])\b",
            "",
            f"{question} {answer}",
        )
        assert not re.search(r"[A-Za-z]", prose), f"{draft_id} contains English prose: {prose}"
        assert re.search(r"[\u0900-\u097F]", question), draft_id
        assert re.search(r"[\u0900-\u097F]", answer), draft_id
        assert evidence.strip(), draft_id


def test_kalibangan_site_identifiers_and_review_provenance_are_preserved() -> None:
    rows = _chapter_rows()
    assert "KLB-I" in rows["KAL-007"][0]
    assert "KLB-II" in rows["KAL-008"][0]
    assert "KLB-1" in rows["KAL-019"][0]
    assert "KLB-8" in rows["KAL-023"][1]
    assert all(rows[f"KAL-{number:03d}"][2] for number in range(1, 241))



def test_ahar_banas_batch_027_to_032_is_hindi_first_and_review_pending() -> None:
    rows = _chapter_rows()
    expected_ids = {f"AHB-{number:03d}" for number in range(27, 33)}
    assert expected_ids.issubset(rows)

    for draft_id in sorted(expected_ids):
        question, answer, evidence = rows[draft_id]
        assert not re.search(r"[A-Za-z]", f"{question} {answer}"), draft_id
        assert re.search(r"[\u0900-\u097F]", question), draft_id
        assert re.search(r"[\\u0900-\\u097F]", answer), draft_id
        assert evidence.strip(), draft_id


def test_phase_changes_trigger_a_firebase_configured_release_apk() -> None:
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "flutter-mobile.yml"
    ).read_text(encoding="utf-8")

    for trigger in (
        '      - "docs/study-notes/**"',
        '      - "docs/PHASE_6_56*.md"',
        '      - "docs/PHASE_REGISTRY.md"',
        '      - "docs/PROJECT_CONTINUITY_CHECKPOINT.md"',
        '      - "docs/QUESTION_BANK_CONTENT_COVERAGE.*"',
        '      - "database/migrations/**"',
    ):
        assert trigger in workflow

    assert "Require real Firebase configuration for distributable APK" in workflow
    assert "GOOGLE_SERVICES_JSON_BASE64 is required" in workflow
    assert "flutter build apk --release" in workflow
    assert "actions/upload-artifact@v4" in workflow


def test_all_chapter_2_question_and_answer_text_is_hindi_first() -> None:
    asset = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "apps"
            / "mobile"
            / "assets"
            / "question_bank"
            / "rajasthan_history_chapter_2_drafts.json"
        ).read_text(encoding="utf-8")
    )
    expected_counts = {"KAL": 311, "AHB": 32, "GJ": 18, "BRT": 11, "MTS": 10}
    assert len(asset) == sum(expected_counts.values())

    for prefix, expected_count in expected_counts.items():
        rows = [row for row in asset if row["one_liner_id"].startswith(f"ch2_{prefix}-")]
        assert len(rows) == expected_count
        for row in rows:
            prose = re.sub(
                r"\b(?:KLB-(?:I{1,2}|\d+)|K-\d+|GM-KAM-RJ-\d+|VI-A|[A-F])\b",
                "",
                f"{row['question_text']} {row['answer_text']}",
            )
            assert not re.search(r"[A-Za-z]", prose), row["one_liner_id"]
            assert re.search(r"[\u0900-\u097F]", row["question_text"]), row["one_liner_id"]
            assert re.search(r"[\u0900-\u097F]", row["answer_text"]), row["one_liner_id"]
            assert row["language_code"] == "hi", row["one_liner_id"]
            assert row["verification_status"] == "NEEDS_REVIEW", row["one_liner_id"]
