from fastapi.testclient import TestClient

import ai_comp.api.source_health_routes as source_health_routes
from ai_comp.api.app import create_app


def test_source_health_route_reports_registered_hosts_without_raw_ip_addresses(monkeypatch):
    calls = []

    def fake_report(*, timeout_seconds):
        calls.append(timeout_seconds)
        return {
            "phase": "2.5-source-health",
            "probes_are_diagnostic_only": True,
            "results": [
                {
                    "source_id": "RSSB_OFFICIAL",
                    "host": "rssb.rajasthan.gov.in",
                    "dns_status": "OK",
                    "ipv4_records": 1,
                    "ipv4_tcp": "FAIL",
                    "ipv4_tls": "NOT_REACHED",
                    "ipv4_tcp_errors": ["TimeoutError"],
                    "ipv4_tls_errors": [],
                    "ipv6_records": 0,
                    "ipv6_tcp": "NO_RECORDS",
                    "ipv6_tls": "NO_RECORDS",
                    "ipv6_tcp_errors": [],
                    "ipv6_tls_errors": [],
                },
                {
                    "source_id": "RSSB_LEGACY_OFFICIAL",
                    "host": "rsmssb.rajasthan.gov.in",
                    "dns_status": "OK",
                    "ipv4_records": 1,
                    "ipv4_tcp": "PASS",
                    "ipv4_tls": "PASS",
                    "ipv4_tcp_errors": [],
                    "ipv4_tls_errors": [],
                    "ipv6_records": 0,
                    "ipv6_tcp": "NO_RECORDS",
                    "ipv6_tls": "NO_RECORDS",
                    "ipv6_tcp_errors": [],
                    "ipv6_tls_errors": [],
                }
            ],
        }

    monkeypatch.setattr(source_health_routes, "source_health_report", fake_report)
    client = TestClient(create_app())

    response = client.get("/diagnostics/official-source-health")

    assert response.status_code == 200
    assert response.json()["phase"] == "2.5-source-health"
    assert response.json()["results"][0]["ipv4_tcp"] == "FAIL"
    assert response.json()["results"][1]["source_id"] == "RSSB_LEGACY_OFFICIAL"
    assert response.json()["cache"] == {"cached": False, "ttl_seconds": 60}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-type"].startswith("application/json")
    assert calls == [0.75]
    assert "192.0.2." not in response.text
    assert "service_role" not in response.text


def test_source_health_route_caches_probe_results_for_sixty_seconds(monkeypatch):
    calls = []

    def fake_report(*, timeout_seconds):
        calls.append(timeout_seconds)
        return {
            "phase": "2.5-source-health",
            "probes_are_diagnostic_only": True,
            "results": [],
        }

    monkeypatch.setattr(source_health_routes, "source_health_report", fake_report)
    client = TestClient(create_app())

    first = client.get("/diagnostics/official-source-health")
    second = client.get("/diagnostics/official-source-health")

    assert first.status_code == second.status_code == 200
    assert first.json()["cache"]["cached"] is False
    assert second.json()["cache"]["cached"] is True
    assert calls == [0.75]


def test_source_health_route_rejects_query_parameters_and_arbitrary_hosts():
    client = TestClient(create_app())

    response = client.get(
        "/diagnostics/official-source-health?url=https://example.org/"
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_QUERY"
    assert "https://example.org/" not in response.text


def test_source_health_route_is_not_listed_in_public_openapi_schema():
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/diagnostics/official-source-health" not in response.json()["paths"]



def test_source_health_route_returns_503_without_exposing_probe_exception_details(monkeypatch):
    def fail_report(**_kwargs):
        raise RuntimeError("private database or runtime details")

    monkeypatch.setattr(source_health_routes, "source_health_report", fail_report)
    client = TestClient(create_app())

    response = client.get("/diagnostics/official-source-health")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SOURCE_HEALTH_UNAVAILABLE"
    assert response.json()["error"]["exception_type"] == "RuntimeError"
    assert "private database or runtime details" not in response.text

def test_source_health_route_allows_only_chat_link_tracking_query(monkeypatch):
    calls = []

    def fake_report(*, timeout_seconds):
        calls.append(timeout_seconds)
        return {
            "phase": "2.5-source-health",
            "probes_are_diagnostic_only": True,
            "results": [
                {
                    "source_id": "RSSB_OFFICIAL",
                    "host": "rssb.rajasthan.gov.in",
                    "dns_status": "OK",
                    "ipv4_records": 1,
                    "ipv4_tcp": "FAIL",
                    "ipv4_tls": "NOT_REACHED",
                    "ipv4_tcp_errors": ["TimeoutError"],
                    "ipv4_tls_errors": [],
                    "ipv6_records": 0,
                    "ipv6_tcp": "NO_RECORDS",
                    "ipv6_tls": "NO_RECORDS",
                    "ipv6_tcp_errors": [],
                    "ipv6_tls_errors": [],
                }
            ],
        }

    monkeypatch.setattr(source_health_routes, "source_health_report", fake_report)
    client = TestClient(create_app())

    response = client.get(
        "/diagnostics/official-source-health?utm_source=chatgpt.com"
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["source_id"] == "RSSB_OFFICIAL"
    assert response.json()["results"][0]["ipv4_tcp"] == "FAIL"
    assert calls == [0.75]


def test_source_health_route_rejects_other_or_duplicate_tracking_parameters():
    client = TestClient(create_app())

    responses = (
        client.get("/diagnostics/official-source-health?utm_source=elsewhere"),
        client.get("/diagnostics/official-source-health?utm_source=chatgpt.com&url=https://example.org/"),
        client.get("/diagnostics/official-source-health?utm_source=chatgpt.com&utm_source=chatgpt.com"),
    )

    assert [response.status_code for response in responses] == [400, 400, 400]
    assert all(response.json()["error"]["code"] == "UNSUPPORTED_QUERY" for response in responses)




def test_jansoochna_service_diagnostic_returns_bounded_public_probe_report(monkeypatch):
    report = {
        "phase": "2.5-jansoochna-public-service-probe",
        "diagnostic_only": True,
        "host": "jansoochna.rajasthan.gov.in",
        "status": "SAME_HOST_RSSB_PAPER_SERVICE_LINK_FOUND",
        "robots": {"status": "READ", "can_fetch_services": True, "can_fetch_scheme": True},
        "pages_fetched": [{
            "path": "/Services",
            "status": "READ_ONLY_PUBLIC_HTML",
            "question_papers": [{
                "label": "Question Papers of RSSB",
                "same_host": True,
                "status": "PUBLIC_LINK_FOUND_NOT_FETCHED",
                "url": "https://jansoochna.rajasthan.gov.in/Services/RSSB?id=123",
            }],
            "answer_keys": [],
        }],
        "source_registry_modified": False,
        "paper_bytes_fetched": False,
    }
    calls = []
    monkeypatch.setattr(
        source_health_routes,
        "probe_jansoochna_rssb_service",
        lambda *, timeout_seconds: calls.append(timeout_seconds) or report,
    )
    client = TestClient(create_app())

    response = client.get("/diagnostics/jansoochna-rssb-service")

    assert response.status_code == 200
    assert response.json()["status"] == "SAME_HOST_RSSB_PAPER_SERVICE_LINK_FOUND"
    assert response.json()["pages_fetched"][0]["question_papers"][0]["same_host"] is True
    assert response.json()["source_registry_modified"] is False
    assert response.json()["paper_bytes_fetched"] is False
    assert response.json()["cache"] == {"cached": False, "ttl_seconds": 60}
    assert calls == [1.0]


def test_jansoochna_service_diagnostic_caches_the_read_only_report(monkeypatch):
    calls = []

    def fake_probe(*, timeout_seconds):
        calls.append(timeout_seconds)
        return {
            "phase": "2.5-jansoochna-public-service-probe",
            "diagnostic_only": True,
            "status": "ROBOTS_UNAVAILABLE",
            "pages_fetched": [],
            "source_registry_modified": False,
            "paper_bytes_fetched": False,
        }

    monkeypatch.setattr(source_health_routes, "probe_jansoochna_rssb_service", fake_probe)
    client = TestClient(create_app())

    first = client.get("/diagnostics/jansoochna-rssb-service")
    second = client.get("/diagnostics/jansoochna-rssb-service")

    assert first.status_code == second.status_code == 200
    assert first.json()["cache"]["cached"] is False
    assert second.json()["cache"]["cached"] is True
    assert calls == [1.0]


def test_jansoochna_service_diagnostic_rejects_caller_supplied_hosts():
    client = TestClient(create_app())
    response = client.get(
        "/diagnostics/jansoochna-rssb-service?url=https://example.org/"
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_QUERY"
    assert "example.org" not in response.text


def test_jansoochna_service_diagnostic_is_not_exposed_in_public_openapi():
    client = TestClient(create_app())
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/diagnostics/jansoochna-rssb-service" not in response.json()["paths"]



def test_recruitment_portal_route_diagnostic_returns_bounded_report_without_admitting_sources(monkeypatch):
    report = {
        "phase": "2.2-recruitment-portal-route-probe",
        "diagnostic_only": True,
        "host": "recruitment.rajasthan.gov.in",
        "status": "PUBLIC_INDEX_READ_BUT_NO_PAPER_OR_KEY_LINK_FOUND",
        "robots": {"status": "READ", "allowed_index_paths": {"/": True}},
        "pages_inspected": [{"path": "/", "status": "READ_ONLY_PUBLIC_HTML", "paper_links": []}],
        "source_registry_modified": False,
        "paper_bytes_fetched": False,
        "database_written": False,
        "candidate_promotions": 0,
    }
    calls = []
    monkeypatch.setattr(
        source_health_routes,
        "probe_recruitment_portal_route",
        lambda *, timeout_seconds: calls.append(timeout_seconds) or report,
    )
    client = TestClient(create_app())

    response = client.get("/diagnostics/recruitment-portal-paper-route")

    assert response.status_code == 200
    assert response.json()["phase"] == "2.2-recruitment-portal-route-probe"
    assert response.json()["source_registry_modified"] is False
    assert response.json()["paper_bytes_fetched"] is False
    assert response.json()["database_written"] is False
    assert response.json()["candidate_promotions"] == 0
    assert response.json()["cache"] == {"cached": False, "ttl_seconds": 60}
    assert calls == [1.0]


def test_recruitment_portal_route_diagnostic_caches_report(monkeypatch):
    calls = []

    def fake_probe(*, timeout_seconds):
        calls.append(timeout_seconds)
        return {
            "phase": "2.2-recruitment-portal-route-probe",
            "diagnostic_only": True,
            "host": "recruitment.rajasthan.gov.in",
            "status": "ROBOTS_UNAVAILABLE",
            "pages_inspected": [],
            "source_registry_modified": False,
            "paper_bytes_fetched": False,
            "database_written": False,
            "candidate_promotions": 0,
        }

    monkeypatch.setattr(source_health_routes, "probe_recruitment_portal_route", fake_probe)
    client = TestClient(create_app())

    first = client.get("/diagnostics/recruitment-portal-paper-route")
    second = client.get("/diagnostics/recruitment-portal-paper-route")

    assert first.status_code == second.status_code == 200
    assert first.json()["cache"]["cached"] is False
    assert second.json()["cache"]["cached"] is True
    assert calls == [1.0]


def test_recruitment_portal_route_diagnostic_rejects_supplied_host_or_url():
    client = TestClient(create_app())
    response = client.get("/diagnostics/recruitment-portal-paper-route?url=https://example.org/")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_QUERY"
    assert "example.org" not in response.text


def test_recruitment_portal_route_diagnostic_is_not_in_openapi():
    client = TestClient(create_app())
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/diagnostics/recruitment-portal-paper-route" not in response.json()["paths"]



def test_rbse_archive_route_returns_bounded_read_only_probe_report(monkeypatch):
    report = {
        "phase": "2.2-rbse-archive-route-probe",
        "diagnostic_only": True,
        "host": "rajeduboard.rajasthan.gov.in",
        "board_id": "RBSE",
        "status": "SAME_HOST_PAPER_LINKS_FOUND_NOT_FETCHED",
        "robots": {"status": "READ", "allowed_index_path": True},
        "pages_inspected": [{
            "path": "/books/PAPERS-2025/index.htm",
            "status": "READ_ONLY_PUBLIC_HTML",
            "pdf_links": [{
                "label": "Senior Secondary Geography",
                "target_host": "rajeduboard.rajasthan.gov.in",
                "path": "/books/PAPERS-2025/SRS/SS-14.pdf",
                "same_host": True,
                "query_present": False,
                "status": "PUBLIC_PDF_LINK_FOUND_NOT_FETCHED",
            }],
        }],
        "source_registry_modified": False,
        "paper_bytes_fetched": False,
        "database_written": False,
        "candidate_promotions": 0,
    }
    calls = []
    monkeypatch.setattr(
        source_health_routes,
        "probe_rbse_archive_route",
        lambda *, timeout_seconds: calls.append(timeout_seconds) or report,
    )
    client = TestClient(create_app())

    response = client.get("/diagnostics/rbse-archive-paper-route")

    assert response.status_code == 200
    assert response.json()["phase"] == "2.2-rbse-archive-route-probe"
    assert response.json()["board_id"] == "RBSE"
    assert response.json()["paper_bytes_fetched"] is False
    assert response.json()["database_written"] is False
    assert response.json()["candidate_promotions"] == 0
    assert response.json()["cache"] == {"cached": False, "ttl_seconds": 60}
    assert calls == [1.0]


def test_rbse_archive_route_caches_report(monkeypatch):
    calls = []

    def fake_probe(*, timeout_seconds):
        calls.append(timeout_seconds)
        return {
            "phase": "2.2-rbse-archive-route-probe",
            "diagnostic_only": True,
            "host": "rajeduboard.rajasthan.gov.in",
            "board_id": "RBSE",
            "status": "ROBOTS_UNAVAILABLE",
            "pages_inspected": [],
            "source_registry_modified": False,
            "paper_bytes_fetched": False,
            "database_written": False,
            "candidate_promotions": 0,
        }

    monkeypatch.setattr(source_health_routes, "probe_rbse_archive_route", fake_probe)
    client = TestClient(create_app())

    first = client.get("/diagnostics/rbse-archive-paper-route")
    second = client.get("/diagnostics/rbse-archive-paper-route")

    assert first.status_code == second.status_code == 200
    assert first.json()["cache"]["cached"] is False
    assert second.json()["cache"]["cached"] is True
    assert calls == [1.0]


def test_rbse_archive_route_rejects_arbitrary_hosts_and_urls():
    client = TestClient(create_app())
    response = client.get(
        "/diagnostics/rbse-archive-paper-route?url=https://example.org/"
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_QUERY"
    assert "example.org" not in response.text


def test_rbse_archive_route_is_not_listed_in_public_openapi_schema():
    client = TestClient(create_app())
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/diagnostics/rbse-archive-paper-route" not in response.json()["paths"]


def test_rbse_archive_route_allows_only_exact_chat_tracking_parameter(monkeypatch):
    calls = []

    def fake_probe(*, timeout_seconds):
        calls.append(timeout_seconds)
        return {
            "phase": "2.2-rbse-archive-route-probe",
            "diagnostic_only": True,
            "host": "rajeduboard.rajasthan.gov.in",
            "board_id": "RBSE",
            "status": "ROBOTS_UNAVAILABLE",
            "pages_inspected": [],
            "source_registry_modified": False,
            "paper_bytes_fetched": False,
            "database_written": False,
            "candidate_promotions": 0,
        }

    monkeypatch.setattr(source_health_routes, "probe_rbse_archive_route", fake_probe)
    client = TestClient(create_app())

    response = client.get(
        "/diagnostics/rbse-archive-paper-route?utm_source=chatgpt.com"
    )

    assert response.status_code == 200
    assert response.json()["board_id"] == "RBSE"
    assert calls == [1.0]
