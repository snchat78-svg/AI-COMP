import socket

import pytest

from ai_comp.research.seed_registry import build_initial_registry
from ai_comp.research.source_health import probe_source, source_health_report


def official_source(source_id="RSSB_OFFICIAL"):
    return next(
        source
        for source in build_initial_registry().sources()
        if source.source_id == source_id
    )


def test_probe_source_reports_ipv4_and_ipv6_tls_separately_without_ip_addresses():
    source = official_source()
    calls = []

    def resolver(host, port, *, type):
        assert host == "rssb.rajasthan.gov.in"
        assert port == 443
        assert type == socket.SOCK_STREAM
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("192.0.2.10", 443)),
            (socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("2001:db8::10", 443, 0, 0)),
        ]

    def probe(family, socktype, proto, sockaddr, hostname, timeout):
        calls.append((family, hostname, timeout))
        if family == socket.AF_INET:
            return True, None
        return False, "TimeoutError"

    result = probe_source(
        source,
        timeout_seconds=1.5,
        resolver=resolver,
        address_probe=probe,
    )

    assert result["dns_status"] == "OK"
    assert result["ipv4_records"] == 1
    assert result["ipv4_tls"] == "PASS"
    assert result["ipv6_records"] == 1
    assert result["ipv6_tls"] == "FAIL"
    assert result["ipv6_errors"] == ["TimeoutError"]
    assert "192.0.2.10" not in repr(result)
    assert "2001:db8::10" not in repr(result)
    assert calls == [
        (socket.AF_INET, "rssb.rajasthan.gov.in", 1.5),
        (socket.AF_INET6, "rssb.rajasthan.gov.in", 1.5),
    ]


def test_probe_source_reports_missing_address_families_without_network_attempts():
    source = official_source("RPSC_OFFICIAL")

    result = probe_source(
        source,
        resolver=lambda *_args, **_kwargs: [],
        address_probe=lambda *_args: pytest.fail("no address should be probed"),
    )

    assert result["dns_status"] == "NO_RECORDS"
    assert result["ipv4_tls"] == "NO_RECORDS"
    assert result["ipv6_tls"] == "NO_RECORDS"


def test_probe_source_reports_dns_errors_without_leaking_exception_text():
    source = official_source()

    def fail_dns(*_args, **_kwargs):
        raise socket.gaierror("private resolver diagnostics")

    result = probe_source(source, resolver=fail_dns)

    assert result["dns_status"] == "ERROR"
    assert result["dns_error"] == "gaierror"
    assert "private resolver diagnostics" not in repr(result)


def test_source_health_report_probes_only_registered_official_sources():
    report = source_health_report(
        "RPSC_OFFICIAL",
        resolver=lambda *_args, **_kwargs: [],
    )

    assert report["phase"] == "2.5-source-health"
    assert report["probes_are_diagnostic_only"] is True
    assert [item["source_id"] for item in report["results"]] == ["RPSC_OFFICIAL"]


def test_source_health_report_rejects_unknown_sources():
    with pytest.raises(ValueError, match="Unknown official source"):
        source_health_report("UNREGISTERED_SOURCE")


def test_probe_source_rejects_unbounded_timeouts():
    with pytest.raises(ValueError, match="between 0.5 and 5.0"):
        probe_source(official_source(), timeout_seconds=30)
