"""Bounded DNS/TCP/TLS preflight for registered official research sources.

This diagnostic opens only a TCP connection and a certificate-validated TLS
handshake to registered official hosts. It does not fetch pages, follow
redirects, bypass TLS validation, or alter robots/terms policy.
"""
from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
from typing import Any, Callable
from urllib.parse import urlparse

from ai_comp.domain.sources import SourceRecord
from ai_comp.research.seed_registry import build_initial_registry


_ADDRESS_FAMILIES = (
    (socket.AF_INET, "ipv4"),
    (socket.AF_INET6, "ipv6"),
)
_MAX_ADDRESSES_PER_FAMILY = 2


def _validated_tls_probe(
    family: int,
    socktype: int,
    proto: int,
    sockaddr: tuple[Any, ...],
    hostname: str,
    timeout_seconds: float,
) -> tuple[bool, str | None]:
    """Probe one resolved address with normal certificate verification."""
    raw_socket = socket.socket(family, socktype, proto)
    try:
        raw_socket.settimeout(timeout_seconds)
        raw_socket.connect(sockaddr)
        context = ssl.create_default_context()
        tls_socket = context.wrap_socket(raw_socket, server_hostname=hostname)
        try:
            # The handshake and certificate validation happen during wrap_socket.
            tls_socket.getpeercert()
        finally:
            tls_socket.close()
        return True, None
    except (OSError, ssl.SSLError, TimeoutError) as exc:
        return False, type(exc).__name__
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
    address_probe: Callable[..., tuple[bool, str | None]] | None = None,
) -> dict[str, Any]:
    """Report per-address-family connectivity without exposing resolved IPs."""
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
            "ipv4_tls": "NOT_TESTED",
            "ipv4_errors": [],
            "ipv6_records": 0,
            "ipv6_tls": "NOT_TESTED",
            "ipv6_errors": [],
        }

    resolve = resolver or socket.getaddrinfo
    probe = address_probe or _validated_tls_probe
    try:
        addresses = resolve(hostname, 443, type=socket.SOCK_STREAM)
    except (OSError, socket.gaierror) as exc:
        return {
            "source_id": source.source_id,
            "host": hostname,
            "dns_status": "ERROR",
            "dns_error": type(exc).__name__,
            "ipv4_records": 0,
            "ipv4_tls": "NOT_TESTED",
            "ipv4_errors": [],
            "ipv6_records": 0,
            "ipv6_tls": "NOT_TESTED",
            "ipv6_errors": [],
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
            result[f"{label}_tls"] = "NO_RECORDS"
            result[f"{label}_errors"] = []
            continue

        errors: list[str] = []
        connected = False
        for socktype, proto, sockaddr in family_addresses[:_MAX_ADDRESSES_PER_FAMILY]:
            try:
                ok, error_type = probe(
                    family,
                    socktype,
                    proto,
                    sockaddr,
                    hostname,
                    timeout_seconds,
                )
            except (OSError, ssl.SSLError, TimeoutError) as exc:
                ok, error_type = False, type(exc).__name__
            if ok:
                connected = True
                break
            if error_type:
                errors.append(str(error_type))

        result[f"{label}_tls"] = "PASS" if connected else "FAIL"
        result[f"{label}_errors"] = sorted(set(errors))
    return result


def source_health_report(
    source_id: str = "all",
    *,
    timeout_seconds: float = 2.0,
    resolver: Callable[..., Any] | None = None,
    address_probe: Callable[..., tuple[bool, str | None]] | None = None,
) -> dict[str, Any]:
    """Probe one or all registered official sources only."""
    registry = build_initial_registry()
    sources = tuple(
        source
        for source in registry.sources()
        if source_id == "all" or source.source_id == source_id
    )
    if not sources:
        known = ", ".join(source.source_id for source in registry.sources())
        raise ValueError(f"Unknown official source; supported: {known}, all")

    return {
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


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose DNS and certificate-validated HTTPS reachability for registered official sources."
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
