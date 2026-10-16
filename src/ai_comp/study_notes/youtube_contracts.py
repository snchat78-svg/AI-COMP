"""Validated API contracts and URL parsing for YouTube study notes.

This module intentionally performs no network access. A validated video ID must
be passed to a separately scoped transcript provider; never fetch arbitrary URLs.
"""
from __future__ import annotations

import re
from typing import Literal
from urllib.parse import parse_qs, urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


VideoLanguage = Literal["hi", "en", "bilingual"]
VideoId = str
_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")

_YOUTUBE_HOSTS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "youtube-nocookie.com",
        "www.youtube-nocookie.com",
    }
)


class UnsupportedYouTubeURL(ValueError):
    """Raised when a URL is not a supported, canonical YouTube video URL."""


def validate_youtube_video_url(value: str) -> VideoId:
    """Return the 11-character video ID for a supported HTTPS YouTube URL.

    Supported shapes: /watch?v=ID, youtu.be/ID, /embed/ID, /shorts/ID,
    /live/ID, and youtube-nocookie.com/embed/ID. Playlist-only URLs and all
    non-YouTube hosts are rejected. This function never makes network requests.
    """
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise UnsupportedYouTubeURL("Unsupported YouTube URL")

    try:
        parsed = urlsplit(value.strip())
        hostname = parsed.hostname.lower() if parsed.hostname else ""
        port = parsed.port
    except (ValueError, UnicodeError):
        raise UnsupportedYouTubeURL("Unsupported YouTube URL") from None

    if (
        parsed.scheme.lower() != "https"
        or hostname not in _YOUTUBE_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
    ):
        raise UnsupportedYouTubeURL("Unsupported YouTube URL")

    video_id: str | None = None
    path_parts = [part for part in parsed.path.split("/") if part]

    if hostname == "youtu.be":
        if len(path_parts) == 1:
            video_id = path_parts[0]
    elif path_parts == ["watch"]:
        query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=False)
        ids = query.get("v", [])
        if len(ids) == 1:
            video_id = ids[0]
    elif len(path_parts) == 2 and path_parts[0] in {"embed", "shorts", "live"}:
        if path_parts[0] != "embed" and "youtube-nocookie.com" in hostname:
            video_id = None
        else:
            video_id = path_parts[1]

    if not video_id or not _VIDEO_ID_PATTERN.fullmatch(video_id):
        raise UnsupportedYouTubeURL("Unsupported YouTube URL")
    return video_id


class StudyNotesJobCreateRequest(BaseModel):
    """Request contract for a future authenticated study-notes job endpoint."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    video_url: str = Field(min_length=1, max_length=2048)
    language: VideoLanguage = "bilingual"

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, value: str) -> str:
        validate_youtube_video_url(value)
        return value


class StudyNotesJobResponse(BaseModel):
    """Stable job-status contract; persisted API routes are added in a later phase."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1, max_length=128)
    status: Literal["queued", "processing", "completed", "failed"]
    language: VideoLanguage
    error_code: Literal[
        "captions_unavailable",
        "unsupported_url",
        "input_limit_exceeded",
        "provider_unavailable",
        "processing_failed",
    ] | None = None


__all__ = [
    "StudyNotesJobCreateRequest",
    "StudyNotesJobResponse",
    "UnsupportedYouTubeURL",
    "VideoId",
    "VideoLanguage",
    "validate_youtube_video_url",
]
