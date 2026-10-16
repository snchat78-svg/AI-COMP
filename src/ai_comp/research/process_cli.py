"""CLI for processing persisted official paper candidates in a GitHub runner."""
from __future__ import annotations

import argparse
import json
import os
import sys

from ai_comp.database.connection import connect_postgres
from ai_comp.research.paper_processing import process_pending_candidates
from ai_comp.research.supabase_storage import (
    ObjectStorageConfigurationError,
    SupabaseObjectStorage,
)
from ai_comp.research.tesseract_ocr import TesseractOCRAdapter


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch registered official exam-paper candidates, store original bytes "
            "privately, and persist extracted document/question candidates."
        )
    )
    parser.add_argument(
        "--source",
        default="all",
        help="Registered official source ID or all.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum pending documents to process (1-50).",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry candidates currently marked FAILED as well as DISCOVERED.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    dsn = os.environ.get("AI_COMP_DATABASE_URL", "").strip()
    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    bucket = os.environ.get("AI_COMP_DOCUMENT_BUCKET", "ai-comp-papers").strip()
    if not dsn:
        print(json.dumps({"error": "AI_COMP_DATABASE_URL is required"}), file=sys.stderr)
        return 2
    if not supabase_url or not service_key:
        print(
            json.dumps({
                "error": "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required",
                "note": "Configure GitHub Actions repository secrets; never commit or print the service key.",
            }),
            file=sys.stderr,
        )
        return 2

    try:
        object_storage = SupabaseObjectStorage(
            supabase_url,
            service_key,
            bucket=bucket,
        )
        ocr = TesseractOCRAdapter()
        connection = connect_postgres(dsn)
        try:
            summary = process_pending_candidates(
                connection,
                object_storage,
                source_id=args.source,
                limit=args.limit,
                retry_failed=args.retry_failed,
                ocr=ocr,
            )
        finally:
            connection.close()
    except ObjectStorageConfigurationError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    except Exception as exc:
        # Intentionally omit exception text: driver/network exceptions may expose
        # hostnames or deployment configuration. The exception type is enough
        # to locate the safe failure category in logs.
        print(
            json.dumps({
                "error": type(exc).__name__,
                "message": "paper processing could not complete; inspect safe run summary",
            }),
            file=sys.stderr,
        )
        return 2

    payload = {
        "phase": "2.3",
        "selected": summary.selected,
        "processed": summary.processed,
        "duplicate_documents": summary.duplicate_documents,
        "question_candidates": summary.question_candidates,
        "answer_key_entries": summary.answer_key_entries,
        "empty_extractions": summary.empty_extractions,
        "failed": summary.failed,
        "rejected": summary.rejected,
        "results": [
            {
                "candidate_id": item.candidate_id,
                "source_id": item.source_id,
                "status": item.status,
                "question_count": item.question_count,
                "answer_key_entry_count": item.answer_key_entry_count,
                "extraction_method": item.extraction_method,
                "error_type": item.error_type,
            }
            for item in summary.results
        ],
        "trust_boundary": (
            "Extracted questions and answer-key entries are source-observed candidates. "
            "This run does not mark answers VERIFIED, create exam appearances, or place "
            "questions into the accepted test pool."
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
