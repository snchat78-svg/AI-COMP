from __future__ import annotations

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
        if not line.startswith("| KAL-"):
            continue
        columns = [value.strip() for value in line.strip("|").split("|")]
        if len(columns) < 4:
            continue
        result[columns[0]] = (columns[1], columns[2], columns[3])
    return result


def test_first_180_kalibangan_one_liners_are_hindi_first() -> None:
    rows = _chapter_rows()
    expected_ids = {f"KAL-{number:03d}" for number in range(1, 181)}
    assert expected_ids.issubset(rows)

    for draft_id in sorted(expected_ids):
        question, answer, evidence = rows[draft_id]
        # KLB site IDs, K-series catalogue IDs and source-defined fabric
        # classes A-F are fixed identifiers, not English prose.
        prose = re.sub(
            r"\b(?:KLB-(?:I{1,2}|\d+)|K-\d+|[A-F])\b",
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
    assert all(rows[f"KAL-{number:03d}"][2] for number in range(1, 181))


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
