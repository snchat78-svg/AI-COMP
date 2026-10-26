"""Read-only, cached connectivity diagnostics for registered official exam sources."""
from __future__ import annotations

import json
import time
from typing import Any

from fastapi import APIRouter, Request
from starlette.responses import Response

from ai_comp.research.source_health import source_health_report


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
    """Probe registered official hosts only; no arbitrary host input or content fetch."""
    # ChatGPT adds this exact, non-functional tracking parameter to opened links.
    # Accept only that known value; never let callers supply a URL, host, or probe target.
    query_items = list(request.query_params.multi_items())
    allowed_link_tracking = [("utm_source", "chatgpt.com")]
    if query_items and query_items != allowed_link_tracking:
        return _response(400, {
            "error": {
                "code": "UNSUPPORTED_QUERY",
                "message": "This fixed diagnostic endpoint accepts no query parameters other than the known link-tracking parameter.",
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
            # This module has a fixed source registry; callers cannot supply URLs.
            # It opens only short-lived TCP/TLS probes and never downloads paper bytes.
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
