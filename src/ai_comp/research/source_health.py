"""Bounded DNS/TCP/TLS preflight for official sources and a fixed control host.

The fixed example.com control is reported separately from registered official
sources. It is a network diagnostic only, never an exam-content source.
No page or paper content is fetched and certificate validation stays enabled.
"""
from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
from typing import Any, Callable
from urllib.parse import urlparse

from ai_comp.domain.sources import SourcePriority, SourceRecord, SourceType
from ai_comp.research.seed_registry import build_initial_registry


_ADDRESS_FAMILIES = (
    (socket.AF_INET, "ipv4"),
    (socket.AF_INET6, "ipv6"),
)
_MAX_ADDRESSES_PER_FAMILY = 2

# Fixed, non-user-configurable control: distinguishes general outbound HTTPS
# failures from official-host-specific failures. Never add it to the source
# registry or treat it as an exam-content source.
_NETWORK_CONTROL_SOURCE = SourceRecord(
    source_id="NETWORK_CONTROL",
    name="Fixed general HTTPS connectivity control",
    base_url="https://example.com/",
    source_type=SourceType.UNVERIFIED,
    priority=SourcePriority.UNVERIFIED,
    notes="Diagnostic control only; not an official exam-content source.",
)

# Public Rajasthan government portals are tested only as potential approved
# document-routing leads. They are deliberately excluded from the official
# exam-source registry and can never satisfy the official-source acceptance gate.
_GOVERNMENT_PORTAL_CONTROLS = (
    SourceRecord(
        source_id="RAJASTHAN_RECRUITMENT_PORTAL_CONTROL",
        name="Rajasthan Government Recruitment Portal connectivity control",
        base_url="https://recruitment.rajasthan.gov.in/",
        source_type=SourceType.UNVERIFIED,
        priority=SourcePriority.UNVERIFIED,
        notes="Public government portal connectivity only; not an exam-paper source.",
    ),
    SourceRecord(
        source_id="RAJASTHAN_LANDREVENUE_PORTAL_CONTROL",
        name="Rajasthan Government Land Revenue Portal connectivity control",
        base_url="https://landrevenue.rajasthan.gov.in/",
        source_type=SourceType.UNVERIFIED,
        priority=SourcePriority.UNVERIFIED,
        notes="Public government portal connectivity only; not an exam-paper source.",
    ),
)


def _validated_tls_probe(
    family: int,
    socktype: int,
    proto: int,
    sockaddr: tuple[Any, ...],
    hostname: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Report TCP connect and certificate-validated TLS handshake separately."""
    raw_socket = socket.socket(family, socktype, proto)
    try:
        try:
            raw_socket.settimeout(timeout_seconds)
            raw_socket.connect(sockaddr)
        except (OSError, TimeoutError) as exc:
            return {
                "tcp_ok": False,
                "tls_ok": False,
                "tcp_error": type(exc).__name__,
                "tls_error": None,
            }

        try:
            context = ssl.create_default_context()
            tls_socket = context.wrap_socket(raw_socket, server_hostname=hostname)
            try:
                # The handshake and certificate validation happen during wrap_socket.
                tls_socket.getpeercert()
            finally:
                tls_socket.close()
            return {
                "tcp_ok": True,
                "tls_ok": True,
                "tcp_error": None,
                "tls_error": None,
            }
        except (OSError, ssl.SSLError, TimeoutError) as exc:
            return {
                "tcp_ok": True,
                "tls_ok": False,
                "tcp_error": None,
                "tls_error": type(exc).__name__,
            }
    finally:
        try:
            raw_socket.close()
        except OSError:
            pass


def probe_source(
    source: SourceRecord,
    *,
    timeout_seconds: float = 2.0,
    resolver: Callable[..., Any] | None = None,
    address_probe: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Report DNS, TCP and TLS outcomes by address family without exposing IPs."""
    if not 0.5 <= timeout_seconds <= 5.0:
        raise ValueError("timeout_seconds must be between 0.5 and 5.0")

    hostname = urlparse(source.base_url).hostname
    if not hostname:
        return {
            "source_id": source.source_id,
            "host": "",
            "dns_status": "ERROR",
            "dns_error": "InvalidSourceHost",
            "ipv4_records": 0,
            "ipv4_tcp": "NOT_TESTED",
            "ipv4_tls": "NOT_TESTED",
            "ipv4_tcp_errors": [],
            "ipv4_tls_errors": [],
            "ipv6_records": 0,
            "ipv6_tcp": "NOT_TESTED",
            "ipv6_tls": "NOT_TESTED",
            "ipv6_tcp_errors": [],
            "ipv6_tls_errors": [],
        }

    resolve = resolver or socket.getaddrinfo
    probe = address_probe or _validated_tls_probe
    try:
        addresses = resolve(hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        return {
            "source_id": source.source_id,
            "host": hostname,
            "dns_status": "ERROR",
            "dns_error": type(exc).__name__,
            "ipv4_records": 0,
            "ipv4_tcp": "NOT_TESTED",
            "ipv4_tls": "NOT_TESTED",
            "ipv4_tcp_errors": [],
            "ipv4_tls_errors": [],
            "ipv6_records": 0,
            "ipv6_tcp": "NOT_TESTED",
            "ipv6_tls": "NOT_TESTED",
            "ipv6_tcp_errors": [],
            "ipv6_tls_errors": [],
        }

    result: dict[str, Any] = {
        "source_id": source.source_id,
        "host": hostname,
        "dns_status": "OK" if addresses else "NO_RECORDS",
    }
    for family, label in _ADDRESS_FAMILIES:
        family_addresses = []
        seen_sockaddrs: set[tuple[Any, ...]] = set()
        for record_family, socktype, proto, _canonname, sockaddr in addresses:
            if record_family != family or socktype != socket.SOCK_STREAM:
                continue
            normalized_sockaddr = tuple(sockaddr)
            if normalized_sockaddr in seen_sockaddrs:
                continue
            seen_sockaddrs.add(normalized_sockaddr)
            family_addresses.append((socktype, proto, normalized_sockaddr))

        result[f"{label}_records"] = len(family_addresses)
        if not family_addresses:
            result[f"{label}_tcp"] = "NO_RECORDS"
            result[f"{label}_tls"] = "NO_RECORDS"
            result[f"{label}_tcp_errors"] = []
            result[f"{label}_tls_errors"] = []
            continue

        observations: list[dict[str, Any]] = []
        for socktype, proto, sockaddr in family_addresses[:_MAX_ADDRESSES_PER_FAMILY]:
            try:
                observation = probe(
                    family,
                    socktype,
                    proto,
                    sockaddr,
                    hostname,
                    timeout_seconds,
                )
            except (OSError, ssl.SSLError, TimeoutError) as exc:
                observation = {
                    "tcp_ok": False,
                    "tls_ok": False,
                    "tcp_error": type(exc).__name__,
                    "tls_error": None,
                }
            observations.append(observation)
            if observation.get("tls_ok"):
                break

        tcp_passed = any(item.get("tcp_ok") for item in observations)
        tls_passed = any(item.get("tls_ok") for item in observations)
        tcp_errors = sorted({
            str(item["tcp_error"])
            for item in observations
            if not item.get("tcp_ok") and item.get("tcp_error")
        })
        tls_errors = sorted({
            str(item["tls_error"])
            for item in observations
            if item.get("tcp_ok") and not item.get("tls_ok") and item.get("tls_error")
        })
        result[f"{label}_tcp"] = "PASS" if tcp_passed else "FAIL"
        result[f"{label}_tls"] = (
            "PASS" if tls_passed else "FAIL" if tcp_passed else "NOT_REACHED"
        )
        result[f"{label}_tcp_errors"] = tcp_errors
        result[f"{label}_tls_errors"] = tls_errors
    return result


def source_health_report(
    source_id: str = "all",
    *,
    timeout_seconds: float = 2.0,
    resolver: Callable[..., Any] | None = None,
    address_probe: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Probe official sources plus fixed, separate route controls for full reports."""
    registry = build_initial_registry()
    sources = tuple(
        source
        for source in registry.sources()
        if source_id == "all" or source.source_id == source_id
    )
    if not sources:
        known = ", ".join(source.source_id for source in registry.sources())
        raise ValueError(f"Unknown official source; supported: {known}, all")

    report: dict[str, Any] = {
        "phase": "2.5-source-health",
        "probes_are_diagnostic_only": True,
        "results": [
            probe_source(
                source,
                timeout_seconds=timeout_seconds,
                resolver=resolver,
                address_probe=address_probe,
            )
            for source in sources
        ],
    }
    # Keep the control separate from the official-source result set. Only the
    # full report includes it, so single-source checks remain narrowly scoped.
    if source_id == "all":
        report["network_control"] = probe_source(
            _NETWORK_CONTROL_SOURCE,
            timeout_seconds=timeout_seconds,
            resolver=resolver,
            address_probe=address_probe,
        )
        report["government_portal_controls"] = [
            probe_source(
                source,
                timeout_seconds=timeout_seconds,
                resolver=resolver,
                address_probe=address_probe,
            )
            for source in _GOVERNMENT_PORTAL_CONTROLS
        ]
    return report


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose DNS/TCP/certificate-validated TLS for official sources and fixed public-route controls."
    )
    parser.add_argument("--source", default="all")
    parser.add_argument("--timeout-seconds", type=float, default=2.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        report = source_health_report(
            args.source,
            timeout_seconds=args.timeout_seconds,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    # A failed connectivity probe is diagnostic information, not a substitute
    # for the source-research CLI's own exit code and per-source crawl result.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
