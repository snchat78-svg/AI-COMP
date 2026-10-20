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
