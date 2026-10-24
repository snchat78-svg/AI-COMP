from pathlib import Path


def test_manual_syllabus_candidate_fetch_is_explicit_and_review_gated() -> None:
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "register-and-fetch-official-syllabus.yml"
    ).read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "default: DO_NOT_RUN" in workflow
    assert "REGISTER_AND_FETCH" in workflow
    assert "if: ${{ inputs.confirm_action == 'REGISTER_AND_FETCH' }}" in workflow
    assert "environment: official-source-review" in workflow
    assert "secrets.AI_COMP_SYLLABUS_ADMIN_TOKEN" in workflow
    assert "secrets.AI_COMP_SYLLABUS_REVIEW_TOKEN" in workflow
    assert "https://ai-comp-api.onrender.com" in workflow
    assert "X-AI-COMP-Syllabus-Admin-Token" in workflow
    assert "X-AI-COMP-Syllabus-Review-Token" in workflow


def test_fetch_workflow_never_accepts_a_fetch_url_or_marks_source_verified() -> None:
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "register-and-fetch-official-syllabus.yml"
    ).read_text(encoding="utf-8")

    assert "input: source_url" in workflow
    assert '"/api/v1/admin/exam-syllabi"' in workflow
    assert "fetch-source" in workflow
    assert "quote(syllabus_id, safe='')" in workflow
    assert "source_url" not in workflow.split('f"/api/v1/admin/exam-syllabi/{quote(syllabus_id, safe='')}/fetch-source"', 1)[1]
    assert "source_status" not in workflow or "VERIFIED" in workflow
    assert "successful fetch is not human verification" in workflow
    assert "source or syllabus content was promoted to VERIFIED" in workflow


def test_workflow_restricts_target_host_and_keeps_secrets_out_of_command_output() -> None:
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "register-and-fetch-official-syllabus.yml"
    ).read_text(encoding="utf-8")

    for host in (
        "rssb.rajasthan.gov.in",
        "www.rssb.rajasthan.gov.in",
        "rsmssb.rajasthan.gov.in",
        "www.rsmssb.rajasthan.gov.in",
    ):
        assert host in workflow
    assert "API request failed" not in workflow
    assert "No credential values or raw response bodies were written to the log." in workflow
