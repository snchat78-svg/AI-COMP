"""Bounded, scheduled entry point for official-source paper discovery."""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.parse import unquote, urlparse
from typing import Any

from ai_comp.database.connection import connect_postgres
from ai_comp.database.postgres_research import PostgresResearchRepository
from ai_comp.research.live_discovery import HttpTransport, LiveOfficialSourceDiscovery
from ai_comp.research.registry_sync import sync_source_registry
from ai_comp.research.seed_registry import DEFAULT_CRAWL_POLICY, build_initial_registry


_PAPER_PATH_MARKERS = (
    "question-paper",
    "question_paper",
    "questionpaper",
    "previous-paper",
    "previous_paper",
    "old-paper",
    "old_paper",
    "answer-key",
    "answer_key",
    "answerkey",
    "answerkey",
    "model-paper",
    "model_paper",
    "archive",
    "download",
)
_PAPER_SUFFIXES = (".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".webp")


def is_likely_paper_url(url: str) -> bool:
    """Avoid recording ordinary sitemap pages as paper candidates.

    This is only a discovery heuristic, not an authenticity or answer
    verification decision. Official-host, robots, terms and allowed-path gates
    are enforced before this function is reached.
    """
    path = unquote(urlparse(url).path).lower()
    # Archive/listing pages are traversal roots, not downloadable paper files.
    if path.endswith(("/", ".aspx", ".html", ".htm")):
        return False
    return path.endswith(_PAPER_SUFFIXES) or any(
        marker in path for marker in _PAPER_PATH_MARKERS
    )


def build_research_transport() -> HttpTransport:
    """Keep a full multi-source discovery run within its CI time budget.

    Public official portals can stall rather than immediately reject a
    connection. Research uses a shorter per-request timeout and one retry;
    robots/access checks and same-host restrictions remain mandatory.
    """
    return HttpTransport(
        timeout_seconds=6.0,
        retries=1,
        retry_delay_seconds=0.25,
    )


def run_discovery(
    connection: Any,
    *,
    source_id: str = "all",
    max_documents: int = 25,
    transport: Any | None = None,
) -> dict[str, Any]:
    """Sync the seed registry and persist bounded candidates from live sources."""
    if not 1 <= max_documents <= 100:
        raise ValueError("max_documents must be between 1 and 100")

    registry = build_initial_registry()
    selected_sources = tuple(
        source for source in registry.sources()
        if source_id == "all" or source.source_id == source_id
    )
    if not selected_sources:
        known = ", ".join(source.source_id for source in registry.sources())
        raise ValueError(f"Unknown source_id; supported sources: {known}, all")

    registry_counts = sync_source_registry(connection, registry)
    repository = PostgresResearchRepository(connection)
    results: list[dict[str, Any]] = []
    http_transport = transport or build_research_transport()

    for source in selected_sources:
        try:
            discovery = LiveOfficialSourceDiscovery(
                http_transport,
                max_documents=max_documents,
            )
            live_result = discovery.run(
                source,
                DEFAULT_CRAWL_POLICY,
                source.source_id,
            )
            candidates = tuple(
                candidate for candidate in live_result.candidates
                if is_likely_paper_url(candidate.url)
            )
            for candidate in candidates:
                repository.save_candidate(candidate)

            results.append({
                "source_id": source.source_id,
                "status": "CANDIDATES_PERSISTED" if candidates else "NO_PAPER_CANDIDATES",
                "discovered_links": len(live_result.candidates),
                "paper_candidates_persisted": len(candidates),
                "sitemap_count": len(live_result.sitemap_urls),
                "feed_count": len(live_result.feed_urls),
                "archive_count": len(live_result.archive_urls),
            })
        except Exception as exc:  # one inaccessible source must not block others
            message = str(exc).strip()
            safe_reason = (
                message[:120]
                if message and "://" not in message and "\n" not in message
                else type(exc).__name__
            )
            results.append({
                "source_id": source.source_id,
                "status": "BLOCKED_OR_FAILED",
                "error_type": type(exc).__name__,
                "reason": safe_reason,
                "paper_candidates_persisted": 0,
            })

    return {
        "phase": "2.2",
        "registry_synced": {
            "conducting_bodies": registry_counts.conducting_bodies,
            "exams": registry_counts.exams,
            "paper_categories": registry_counts.paper_categories,
            "sources": registry_counts.sources,
        },
        "sources": results,
        "paper_candidates_persisted": sum(
            int(item.get("paper_candidates_persisted", 0)) for item in results
        ),
        "verification_note": (
            "Discovery candidates are not verified exam questions. No candidate "
            "is promoted to VERIFIED or shown as exam history by this workflow."
        ),
    }


def discovery_exit_code(summary: dict[str, Any]) -> int:
    """Return failure only when no registered source completed discovery.

    A reachable source returning no candidate is a valid zero-result run.
    A run in which every source is blocked/failed (or no source result exists)
    must not be reported by automation as a successful research run.
    """
    sources = summary.get("sources")
    if not sources:
        return 1
    reachable_statuses = {"CANDIDATES_PERSISTED", "NO_PAPER_CANDIDATES"}
    return 0 if any(
        source.get("status") in reachable_statuses
        for source in sources
    ) else 1


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover likely paper/answer-key URLs from registered official sources."
    )
    parser.add_argument(
        "--source",
        default="all",
        help="Registered source ID (RSSB_OFFICIAL, RPSC_OFFICIAL) or all.",
    )
    parser.add_argument(
        "--max-documents",
        type=int,
        default=25,
        help="Bound per-source sitemap/archive traversal (1-100).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    dsn = os.environ.get("AI_COMP_DATABASE_URL", "").strip()
    if not dsn:
        print(
            json.dumps({"error": "AI_COMP_DATABASE_URL is required"}),
            file=sys.stderr,
        )
        return 2

    try:
        connection = connect_postgres(dsn)
        try:
            summary = run_discovery(
                connection,
                source_id=args.source,
                max_documents=args.max_documents,
            )
        finally:
            connection.close()
    except Exception as exc:
        # Avoid printing configuration values or a full traceback that might
        # accidentally include infrastructure details in scheduled job logs.
        print(
            json.dumps({
                "error": type(exc).__name__,
                "message": str(exc)[:200] if "://" not in str(exc) else "research run failed",
            }),
            file=sys.stderr,
        )
        return 2

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    exit_code = discovery_exit_code(summary)
    if exit_code:
        print(
            "No registered official source completed discovery; "
            "check the per-source status in the JSON summary.",
            file=sys.stderr,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
