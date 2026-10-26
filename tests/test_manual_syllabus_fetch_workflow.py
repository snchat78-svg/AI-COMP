from pathlib import Path


def _workflow_text() -> str:
    return (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "register-and-fetch-official-syllabus.yml"
    ).read_text(encoding="utf-8")


def test_manual_syllabus_candidate_fetch_is_explicit_and_review_gated() -> None:
    workflow = _workflow_text()

    assert "workflow_dispatch:" in workflow
    assert "default: DO_NOT_RUN" in workflow
    assert "REGISTER_AND_FETCH" in workflow
    assert "FETCH_EXISTING" in workflow
    assert "if: ${{ inputs.confirm_action == 'REGISTER_AND_FETCH' || inputs.confirm_action == 'FETCH_EXISTING' }}" in workflow
    assert "environment: official-source-review" in workflow
    assert "secrets.AI_COMP_SYLLABUS_ADMIN_TOKEN" in workflow
    assert "secrets.AI_COMP_SYLLABUS_REVIEW_TOKEN" in workflow
    assert "https://ai-comp-api.onrender.com" in workflow
    assert "X-AI-COMP-Syllabus-Admin-Token" in workflow
    assert "X-AI-COMP-Syllabus-Review-Token" in workflow


def test_fetch_uses_only_registered_candidate_and_never_accepts_a_fetch_url() -> None:
    workflow = _workflow_text()

    assert "source_url:" in workflow  # Only for registering the pending candidate.
    assert '"/api/v1/admin/exam-syllabi"' in workflow
    assert "fetch-source" in workflow
    assert "quote(syllabus_id, safe='')" in workflow
    assert 'if mode == "REGISTER_AND_FETCH":' in workflow
    assert 'elif mode == "FETCH_EXISTING":' in workflow
    assert "Registration: skipped; no duplicate candidate was created." in workflow

    fetch_call = workflow.split("result = call_api(", 1)[1].split("if result.get(", 1)[0]
    assert "source_url" not in fetch_call  # The fetch endpoint reads its URL from its database record.
    assert "successful fetch is not human verification" in workflow
    assert "source or syllabus content was promoted to VERIFIED" in workflow


def test_workflow_restricts_candidate_host_and_keeps_secrets_out_of_logs() -> None:
    workflow = _workflow_text()

    for host in (
        "rssb.rajasthan.gov.in",
        "www.rssb.rajasthan.gov.in",
        "rsmssb.rajasthan.gov.in",
        "www.rsmssb.rajasthan.gov.in",
    ):
        assert host in workflow

    assert "urlsplit" in workflow
    assert "ssl.create_default_context()" in workflow
    assert "class NoRedirect(HTTPRedirectHandler)" in workflow
    assert "Never forward an author/reviewer" in workflow
    assert "print(admin_token)" not in workflow
    assert "print(review_token)" not in workflow
    assert "No credential values or raw response bodies were written to the log." in workflow
    assert "The candidate remains REVIEW_PENDING" in workflow
