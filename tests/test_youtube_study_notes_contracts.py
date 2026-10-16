from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_comp.study_notes.youtube_contracts import (
    StudyNotesJobCreateRequest,
    StudyNotesJobResponse,
    UnsupportedYouTubeURL,
    validate_youtube_video_url,
)


VIDEO_ID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtube.com/watch?v={VIDEO_ID}",
        f"https://m.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}",
        f"https://www.youtube.com/embed/{VIDEO_ID}",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/live/{VIDEO_ID}",
        f"https://www.youtube-nocookie.com/embed/{VIDEO_ID}",
        f"https://youtube.com:443/watch?v={VIDEO_ID}",
    ],
)
def test_supported_video_urls_return_video_id(url: str) -> None:
    assert validate_youtube_video_url(url) == VIDEO_ID


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not a url",
        f"http://youtube.com/watch?v={VIDEO_ID}",
        f"https://youtube.com.evil.example/watch?v={VIDEO_ID}",
        f"https://evil.example/watch?v={VIDEO_ID}",
        f"https://youtube.com@evil.example/watch?v={VIDEO_ID}",
        f"https://user:pass@youtube.com/watch?v={VIDEO_ID}",
        f"https://127.0.0.1/watch?v={VIDEO_ID}",
        f"https://localhost/watch?v={VIDEO_ID}",
        f"https://youtube.com:8443/watch?v={VIDEO_ID}",
        "https://youtube.com/playlist?list=PL123",
        "https://youtube.com/watch",
        "https://youtube.com/watch?v=short",
        f"https://youtube.com/watch?v={VIDEO_ID}&v=aaaaaaaaaaa",
        f"https://youtu.be/{VIDEO_ID}/extra",
        f"https://youtube.com/shorts/{VIDEO_ID}/extra",
        "https://youtube.com/watch?v=" + ("a" * 2050),
    ],
)
def test_unsupported_urls_are_rejected(url: str) -> None:
    with pytest.raises(UnsupportedYouTubeURL):
        validate_youtube_video_url(url)


@pytest.mark.parametrize("language", ["hi", "en", "bilingual"])
def test_create_request_accepts_supported_languages(language: str) -> None:
    request = StudyNotesJobCreateRequest(
        video_url=f"https://youtu.be/{VIDEO_ID}",
        language=language,
    )
    assert request.language == language
    assert validate_youtube_video_url(request.video_url) == VIDEO_ID


def test_create_request_defaults_to_bilingual() -> None:
    request = StudyNotesJobCreateRequest(video_url=f"https://youtu.be/{VIDEO_ID}")
    assert request.language == "bilingual"


def test_create_request_rejects_invalid_url_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        StudyNotesJobCreateRequest(video_url="https://example.com/video")
    with pytest.raises(ValidationError):
        StudyNotesJobCreateRequest(
            video_url=f"https://youtu.be/{VIDEO_ID}",
            learner_id="untrusted-client-supplied-identity",
        )


def test_job_response_contract_and_error_code() -> None:
    response = StudyNotesJobResponse(
        job_id="job-123",
        status="failed",
        language="hi",
        error_code="captions_unavailable",
    )
    assert response.status == "failed"
    assert response.error_code == "captions_unavailable"

    with pytest.raises(ValidationError):
        StudyNotesJobResponse(
            job_id="job-123",
            status="failed",
            language="hi",
            error_code="raw-provider-exception",
        )
