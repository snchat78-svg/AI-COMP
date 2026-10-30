"""Read-only connectivity diagnostics for official sources and fixed public-route controls."""
from __future__ import annotations

import json
import time
from typing import Any

from fastapi import APIRouter, Request
from starlette.responses import Response

from ai_comp.research.source_health import source_health_report
from ai_comp.research.jansoochna_service_probe import probe_jansoochna_rssb_service
from ai_comp.research.recruitment_portal_probe import probe_recruitment_portal_route
from ai_comp.research.rbse_archive_probe import probe_rbse_archive_route


router = APIRouter(tags=["operations"])
CACHE_TTL_SECONDS = 60
PROBE_TIMEOUT_SECONDS = 0.75
SECURITY_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
}


def _response(status_code: int, payload: dict[str, Any]) -> Response:
    return Response(
        content=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        status_code=status_code,
        headers=SECURITY_HEADERS,
    )


@router.get("/diagnostics/official-source-health", include_in_schema=False)
def official_source_health(request: Request) -> Response:
    """Probe fixed hosts only; no arbitrary host input or content fetch."""
    # ChatGPT link navigation appends this analytics-only parameter to links.
    # Permit only that exact single pair so the diagnostic is usable from chat;
    # no query parameter can select or override the registered hosts.
    query_items = list(request.query_params.multi_items())
    if query_items and query_items != [("utm_source", "chatgpt.com")]:
        return _response(400, {
            "error": {
                "code": "UNSUPPORTED_QUERY",
                "message": "This fixed diagnostic endpoint does not accept source/host query parameters.",
            }
        })

    cache = request.app.state.source_health_cache
    lock = request.app.state.source_health_lock

    with lock:
        now = time.monotonic()
        cached_report = cache.get("report")
        expires_at = float(cache.get("expires_at", 0.0))
        if isinstance(cached_report, dict) and now < expires_at:
            return _response(int(cache.get("status_code", 200)), {
                **cached_report,
                "cache": {"cached": True, "ttl_seconds": CACHE_TTL_SECONDS},
            })

        try:
            # This module uses fixed official and diagnostic-only host lists; callers cannot supply URLs.
            # It opens short-lived TCP/TLS probes and never downloads page or paper bytes.
            report = source_health_report(timeout_seconds=PROBE_TIMEOUT_SECONDS)
        except Exception as exc:
            # Store only exception class, never messages that may reveal runtime data.
            report = {
                "phase": "2.5-source-health",
                "probes_are_diagnostic_only": True,
                "error": {
                    "code": "SOURCE_HEALTH_UNAVAILABLE",
                    "exception_type": type(exc).__name__,
                },
            }
            status_code = 503
        else:
            status_code = 200

        cache["report"] = report
        cache["status_code"] = status_code
        cache["expires_at"] = time.monotonic() + CACHE_TTL_SECONDS
        return _response(status_code, {
            **report,
            "cache": {"cached": False, "ttl_seconds": CACHE_TTL_SECONDS},
        })



@router.get("/diagnostics/jansoochna-rssb-service", include_in_schema=False)
def jansoochna_rssb_service_diagnostic(request: Request) -> Response:
    """Inspect only public Jan Soochna service-index links after robots permission."""
    query_items = list(request.query_params.multi_items())
    if query_items and query_items != [("utm_source", "chatgpt.com")]:
        return _response(400, {
            "error": {
                "code": "UNSUPPORTED_QUERY",
                "message": "This fixed diagnostic endpoint does not accept URL or host parameters.",
            }
        })

    cache = request.app.state.source_health_cache
    lock = request.app.state.source_health_lock
    with lock:
        now = time.monotonic()
        cached_report = cache.get("jansoochna_service_report")
        expires_at = float(cache.get("jansoochna_service_expires_at", 0.0))
        if isinstance(cached_report, dict) and now < expires_at:
            return _response(int(cache.get("jansoochna_service_status_code", 200)), {
                **cached_report,
                "cache": {"cached": True, "ttl_seconds": CACHE_TTL_SECONDS},
            })

        try:
            report = probe_jansoochna_rssb_service(timeout_seconds=1.0)
        except Exception as exc:
            # Never expose exception text, URL query values, or arbitrary host details.
            report = {
                "phase": "2.5-jansoochna-public-service-probe",
                "diagnostic_only": True,
                "status": "PROBE_UNAVAILABLE",
                "error_type": type(exc).__name__,
                "source_registry_modified": False,
                "paper_bytes_fetched": False,
            }
            status_code = 503
        else:
            status_code = 200

        cache["jansoochna_service_report"] = report
        cache["jansoochna_service_status_code"] = status_code
        cache["jansoochna_service_expires_at"] = time.monotonic() + CACHE_TTL_SECONDS
        return _response(status_code, {
            **report,
            "cache": {"cached": False, "ttl_seconds": CACHE_TTL_SECONDS},
        })


@router.get("/diagnostics/recruitment-portal-paper-route", include_in_schema=False)
def recruitment_portal_paper_route_diagnostic(request: Request) -> Response:
    """Inspect fixed public recruitment-index routes after robots permission."""
    query_items = list(request.query_params.multi_items())
    if query_items and query_items != [("utm_source", "chatgpt.com")]:
        return _response(400, {
            "error": {
                "code": "UNSUPPORTED_QUERY",
                "message": "This fixed diagnostic endpoint does not accept URL or host parameters.",
            }
        })

    cache = request.app.state.source_health_cache
    lock = request.app.state.source_health_lock
    with lock:
        now = time.monotonic()
        cached_report = cache.get("recruitment_portal_report")
        expires_at = float(cache.get("recruitment_portal_expires_at", 0.0))
        if isinstance(cached_report, dict) and now < expires_at:
            return _response(int(cache.get("recruitment_portal_status_code", 200)), {
                **cached_report,
                "cache": {"cached": True, "ttl_seconds": CACHE_TTL_SECONDS},
            })

        try:
            report = probe_recruitment_portal_route(timeout_seconds=1.0)
        except Exception as exc:
            report = {
                "phase": "2.2-recruitment-portal-route-probe",
                "diagnostic_only": True,
                "host": "recruitment.rajasthan.gov.in",
                "status": "PROBE_UNAVAILABLE",
                "error_type": type(exc).__name__,
                "pages_inspected": [],
                "source_registry_modified": False,
                "paper_bytes_fetched": False,
                "database_written": False,
                "candidate_promotions": 0,
            }
            status_code = 503
        else:
            status_code = 200

        cache["recruitment_portal_report"] = report
        cache["recruitment_portal_status_code"] = status_code
        cache["recruitment_portal_expires_at"] = time.monotonic() + CACHE_TTL_SECONDS
        return _response(status_code, {
            **report,
            "cache": {"cached": False, "ttl_seconds": CACHE_TTL_SECONDS},
        })



@router.get("/diagnostics/rbse-archive-paper-route", include_in_schema=False)
def rbse_archive_paper_route_diagnostic(request: Request) -> Response:
    """Inspect the one fixed RBSE paper index only after robots permission."""
    query_items = list(request.query_params.multi_items())
    if query_items and query_items != [("utm_source", "chatgpt.com")]:
        return _response(400, {
            "error": {
                "code": "UNSUPPORTED_QUERY",
                "message": "This fixed diagnostic endpoint does not accept URL or host parameters.",
            }
        })

    cache = request.app.state.source_health_cache
    lock = request.app.state.source_health_lock
    with lock:
        now = time.monotonic()
        cached_report = cache.get("rbse_archive_report")
        expires_at = float(cache.get("rbse_archive_expires_at", 0.0))
        if isinstance(cached_report, dict) and now < expires_at:
            return _response(int(cache.get("rbse_archive_status_code", 200)), {
                **cached_report,
                "cache": {"cached": True, "ttl_seconds": CACHE_TTL_SECONDS},
            })

        try:
            report = probe_rbse_archive_route(timeout_seconds=1.0)
        except Exception as exc:
            report = {
                "phase": "2.2-rbse-archive-route-probe",
                "diagnostic_only": True,
                "host": "rajeduboard.rajasthan.gov.in",
                "board_id": "RBSE",
                "status": "PROBE_UNAVAILABLE",
                "error_type": type(exc).__name__,
                "pages_inspected": [],
                "source_registry_modified": False,
                "paper_bytes_fetched": False,
                "database_written": False,
                "candidate_promotions": 0,
            }
            status_code = 503
        else:
            status_code = 200

        cache["rbse_archive_report"] = report
        cache["rbse_archive_status_code"] = status_code
        cache["rbse_archive_expires_at"] = time.monotonic() + CACHE_TTL_SECONDS
        return _response(status_code, {
            **report,
            "cache": {"cached": False, "ttl_seconds": CACHE_TTL_SECONDS},
        })
