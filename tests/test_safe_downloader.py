from io import BytesIO
from urllib.error import URLError

import pytest

import ai_comp.research.safe_downloader as downloader_module
from ai_comp.domain.sources import CrawlPolicy, SourcePriority, SourceRecord, SourceType
from ai_comp.research.paper import DocumentFormat
from ai_comp.research.policy import ResearchPolicyError
from ai_comp.research.safe_downloader import (
    SafePaperDownloader,
    _RegisteredHostRedirectHandler,
)


class FakeResponse:
    def __init__(self, url, body, content_type="text/plain", status=200):
        self._url = url
        self._body = BytesIO(body)
        self.status = status
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size=-1):
        return self._body.read(size)

    def geturl(self):
        return self._url


class FakeOpener:
    def __init__(self, handler):
        self.handler = handler

    def open(self, request, timeout):
        if request.full_url.endswith("/robots.txt"):
            return FakeResponse(
                request.full_url,
                b"User-agent: *\nAllow: /\n",
            )
        return FakeResponse(
            request.full_url,
            b"%PDF-1.7\\nunit test paper",
            "application/pdf",
        )


def source():
    return SourceRecord(
        "RSSB_OFFICIAL",
        "RSSB official",
        "https://rssb.rajasthan.gov.in/",
        SourceType.OFFICIAL_WEBSITE,
        SourcePriority.OFFICIAL,
        allowed_paths=("/papers/",),
    )


def test_safe_downloader_rechecks_robots_and_detects_pdf(monkeypatch):
    calls = []
    monkeypatch.setattr(
        downloader_module,
        "build_opener",
        lambda handler: (calls.append(handler) or FakeOpener(handler)),
    )
    target = "https://rssb.rajasthan.gov.in/papers/cet-2024.pdf"

    result = SafePaperDownloader().download(
        source(),
        target,
        CrawlPolicy(True, respect_robots=True, respect_terms=True, rate_limit_seconds=0),
    )

    assert len(calls) == 2
    assert result.requested_url == target
    assert result.final_url == target
    assert result.content_type == "application/pdf"
    assert result.detected_format is DocumentFormat.PDF
    assert result.payload.startswith(b"%PDF-")


def test_safe_downloader_rejects_url_outside_registered_host(monkeypatch):
    monkeypatch.setattr(
        downloader_module,
        "build_opener",
        lambda _handler: pytest.fail("network must not be opened for an unregistered host"),
    )

    with pytest.raises(ResearchPolicyError):
        SafePaperDownloader().download(
            source(),
            "https://example.invalid/papers/hostile.pdf",
            CrawlPolicy(True, rate_limit_seconds=0),
        )


def test_redirect_handler_blocks_cross_host_redirect():
    handler = _RegisteredHostRedirectHandler(
        source(),
        CrawlPolicy(True, rate_limit_seconds=0),
        user_agent="AI-COMP/phase2.3",
        robots=None,
    )

    with pytest.raises(URLError, match="outside registered source"):
        handler.redirect_request(
            request=__import__("urllib.request", fromlist=["Request"]).Request(
                "https://rssb.rajasthan.gov.in/papers/a.pdf"
            ),
            fp=None,
            code=302,
            msg="Found",
            headers={},
            newurl="https://example.invalid/papers/a.pdf",
        )
