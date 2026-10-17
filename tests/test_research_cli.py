from ai_comp.research.live_discovery import HttpResponse
from ai_comp.research.research_cli import (
    discovery_exit_code,
    is_likely_paper_url,
    run_discovery,
)


class FakeTransport:
    def __init__(self, pages):
        self.pages = pages
        self.requested = []

    def get(self, url):
        self.requested.append(url)
        return self.pages[url]


class FakeConnection:
    def __init__(self):
        self.calls = []

    def transaction(self):
        class Transaction:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return Transaction()

    def execute(self, sql, params=()):
        self.calls.append((sql, params))


def test_paper_url_heuristic_keeps_exam_documents_and_ignores_normal_pages():
    assert is_likely_paper_url("https://rsmssb.rajasthan.gov.in/files/qp-2024.pdf")
    assert is_likely_paper_url(
        "https://rpsc.rajasthan.gov.in/answer-key/final-answer-key"
    )
    assert not is_likely_paper_url("https://rsmssb.rajasthan.gov.in/news/latest-update")
    assert not is_likely_paper_url(
        "https://rpsc.rajasthan.gov.in/previousquestionpapers.aspx"
    )
    assert not is_likely_paper_url(
        "https://rpsc.rajasthan.gov.in/Static/AnswerKeys/"
    )


def test_run_discovery_syncs_registry_and_persists_only_paper_candidates():
    base = "https://rssb.rajasthan.gov.in/"
    sitemap = base + "sitemap.xml"
    question_pdf = base + "files/qp-2024.pdf"
    transport = FakeTransport({
        base + "robots.txt": HttpResponse(
            base + "robots.txt",
            200,
            "User-agent: AI-COMP/phase2\nSitemap: " + sitemap + "\n",
            "text/plain",
        ),
        base: HttpResponse(
            base,
            200,
            "<html><body>Rajasthan Staff Selection Board</body></html>",
            "text/html",
        ),
        sitemap: HttpResponse(
            sitemap,
            200,
            (
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                f"<url><loc>{question_pdf}</loc></url>"
                f"<url><loc>{base}news/latest-update</loc></url>"
                "</urlset>"
            ),
            "application/xml",
        ),
    })
    connection = FakeConnection()

    summary = run_discovery(
        connection,
        source_id="RSSB_OFFICIAL",
        max_documents=5,
        transport=transport,
    )

    assert summary["registry_synced"]["conducting_bodies"] == 2
    assert summary["registry_synced"]["exams"] >= 12
    assert summary["registry_synced"]["paper_categories"] >= 22
    assert summary["registry_synced"]["sources"] == 2
    assert summary["paper_candidates_persisted"] == 1
    assert summary["sources"][0]["discovered_links"] == 2
    assert summary["sources"][0]["paper_candidates_persisted"] == 1
    candidate_rows = [
        (sql, params)
        for sql, params in connection.calls
        if "INSERT INTO paper_candidates" in sql
    ]
    assert len(candidate_rows) == 1
    assert candidate_rows[0][1][1] == "RSSB_OFFICIAL"
    assert candidate_rows[0][1][2] == question_pdf
    assert candidate_rows[0][1][6]
    assert transport.requested == [base + "robots.txt", base, sitemap]


def test_run_discovery_fails_for_unknown_source_before_touching_database():
    connection = FakeConnection()
    try:
        run_discovery(connection, source_id="NOT_REGISTERED", transport=FakeTransport({}))
    except ValueError as exc:
        assert "Unknown source_id" in str(exc)
    else:
        raise AssertionError("unknown source should be rejected")
    assert connection.calls == []



def test_research_exit_code_fails_when_every_official_source_is_unavailable():
    assert discovery_exit_code({
        "sources": [
            {"source_id": "RSSB_OFFICIAL", "status": "BLOCKED_OR_FAILED"},
            {"source_id": "RPSC_OFFICIAL", "status": "BLOCKED_OR_FAILED"},
        ]
    }) == 1
    assert discovery_exit_code({"sources": []}) == 1


def test_research_exit_code_allows_a_reachable_source_with_no_papers():
    assert discovery_exit_code({
        "sources": [
            {"source_id": "RSSB_OFFICIAL", "status": "BLOCKED_OR_FAILED"},
            {"source_id": "RPSC_OFFICIAL", "status": "NO_PAPER_CANDIDATES"},
        ]
    }) == 0
    assert discovery_exit_code({
        "sources": [
            {"source_id": "RSSB_OFFICIAL", "status": "CANDIDATES_PERSISTED"},
        ]
    }) == 0
