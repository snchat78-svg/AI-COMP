"""Manual/scheduled CLI for source-backed paper metadata and history ingestion."""
from __future__ import annotations

import argparse
import json
import os
import sys

from ai_comp.database.connection import connect_postgres
from ai_comp.research.verification_pipeline import run_verification_pipeline


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Conservatively pair official exam papers and answer keys, verify "
            "source provenance, and record eligible historical appearances."
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
        default=500,
        help="Maximum already-processed official candidates to reconcile (1-5000).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    dsn = os.environ.get("AI_COMP_DATABASE_URL", "").strip()
    if not dsn:
        print(json.dumps({"error": "AI_COMP_DATABASE_URL is required"}), file=sys.stderr)
        return 2

    connection = None
    try:
        connection = connect_postgres(dsn)
        try:
            migration = connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = %s",
                ("0018",),
            ).fetchone()
        except Exception:
            migration = None
        if migration is None:
            print(
                json.dumps({
                    "error": "required_database_migration_not_applied",
                    "message": (
                        "Apply migration 0018_phase2_4_official_answer_key_pairs.sql "
                        "using the existing manual database migration workflow first."
                    ),
                }),
                file=sys.stderr,
            )
            return 2

        summary = run_verification_pipeline(
            connection,
            source_id=args.source,
            limit=args.limit,
        )
    except Exception as exc:
        print(
            json.dumps({
                "error": type(exc).__name__,
                "message": "official paper verification failed; credentials were not printed",
            }),
            file=sys.stderr,
        )
        return 2
    finally:
        if connection is not None:
            connection.close()

    payload = {
        "phase": "2.4",
        "selected_candidates": summary.selected_candidates,
        "metadata_ready": summary.metadata_ready,
        "needs_review": summary.needs_review,
        "pairs_matched": summary.pairs_matched,
        "pairs_needs_review": summary.pairs_needs_review,
        "history_records_written": summary.history_records_written,
        "extracted_questions_seen": summary.extracted_questions_seen,
        "answer_key_entries_seen": summary.answer_key_entries_seen,
        "failed": summary.failed,
        "items": [
            {
                "candidate_id": item.candidate_id,
                "role": item.role,
                "exam_id": item.exam_id,
                "year": item.year,
                "state": item.state,
                "question_count": item.question_count,
                "answer_key_entry_count": item.answer_key_entry_count,
                "appearance_count": item.appearance_count,
                "unresolved_answer_count": item.unresolved_answer_count,
                "reason": item.reason,
            }
            for item in summary.items
        ],
        "trust_boundary": (
            "Only explicit exam/year metadata from registered official HTTPS sources "
            "can create historical appearances. Ambiguous pairing remains in review. "
            "Unresolved answers are not guessed. Appearance counts describe processed "
            "database records, not complete coverage of all government exams."
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
