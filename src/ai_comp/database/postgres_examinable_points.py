from __future__ import annotations

from typing import Any

from ai_comp.database.repository import RepositoryError


class PostgresExaminablePointRepository:
    """Read-only coverage report for independently reviewed syllabus points."""

    _POINT_METRICS_CTE = """
        WITH point_metrics AS (
            SELECT
                p.syllabus_id,
                p.point_id,
                p.unit_id,
                p.point_type,
                p.point_statement,
                p.page_number,
                p.source_locator,
                p.mapping_status,
                p.review_status,
                p.created_by,
                p.reviewed_by,
                COALESCE(concepts.verified_mapping_count, 0)::INTEGER AS verified_mapping_count,
                COALESCE(concepts.total_mapping_count, 0)::INTEGER AS total_mapping_count,
                COALESCE(dimensions.dimension_count, 0)::INTEGER AS dimension_count,
                COALESCE(dimensions.gap_dimension_count, 0)::INTEGER AS gap_dimension_count,
                COALESCE(learning.verified_one_liner_count, 0)::INTEGER AS verified_one_liner_count,
                COALESCE(learning.pending_link_count, 0)::INTEGER AS pending_link_count
            FROM exam_syllabus_examinable_points AS p
            LEFT JOIN LATERAL (
                SELECT
                    COUNT(*) AS total_mapping_count,
                    COUNT(*) FILTER (WHERE review_status = 'VERIFIED') AS verified_mapping_count
                FROM exam_syllabus_point_concepts
                WHERE syllabus_id = p.syllabus_id AND point_id = p.point_id
            ) AS concepts ON TRUE
            LEFT JOIN LATERAL (
                SELECT
                    COUNT(*) AS dimension_count,
                    COUNT(*) FILTER (WHERE assessment = 'GAP') AS gap_dimension_count
                FROM exam_syllabus_point_dimensions
                WHERE syllabus_id = p.syllabus_id AND point_id = p.point_id
            ) AS dimensions ON TRUE
            LEFT JOIN LATERAL (
                SELECT
                    COUNT(DISTINCT link.one_liner_id) FILTER (
                        WHERE link.review_status = 'VERIFIED'
                          AND one_liner.verification_status = 'VERIFIED'
                    ) AS verified_one_liner_count,
                    COUNT(*) FILTER (WHERE link.review_status = 'NEEDS_REVIEW') AS pending_link_count
                FROM exam_syllabus_point_one_liner_links AS link
                JOIN question_bank_one_liners AS one_liner
                  ON one_liner.one_liner_id = link.one_liner_id
                WHERE link.syllabus_id = p.syllabus_id AND link.point_id = p.point_id
            ) AS learning ON TRUE
            WHERE p.syllabus_id = %s
        )
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def get_gap_report(
        self,
        syllabus_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, object] | None:
        if not isinstance(syllabus_id, str) or not syllabus_id.strip() or syllabus_id != syllabus_id.strip():
            raise ValueError("syllabus_id must be a non-empty trimmed string")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 100000:
            raise ValueError("offset must be an integer between 0 and 100000")

        try:
            source = self._connection.execute(
                """
                SELECT exam_id, source_status, syllabus_inventory_complete,
                       examinable_points_inventory_complete,
                       examinable_points_reviewed_at, examinable_points_reviewed_by,
                       examinable_points_review_note
                FROM exam_syllabus_documents
                WHERE syllabus_id = %s
                """,
                (syllabus_id,),
            ).fetchone()
            if source is None:
                return None

            summary_query = self._POINT_METRICS_CTE + """
                SELECT
                    COUNT(*)::INTEGER AS total_points,
                    COUNT(*) FILTER (WHERE review_status = 'NEEDS_REVIEW')::INTEGER AS pending_points,
                    COUNT(*) FILTER (WHERE review_status = 'REJECTED')::INTEGER AS rejected_points,
                    COUNT(*) FILTER (
                        WHERE mapping_status <> 'MAPPED' OR total_mapping_count = 0
                           OR verified_mapping_count <> total_mapping_count
                    )::INTEGER AS mapping_gap_points,
                    COUNT(*) FILTER (
                        WHERE dimension_count <> 9 OR gap_dimension_count > 0
                    )::INTEGER AS points_with_missing_dimensions,
                    COUNT(*) FILTER (
                        WHERE review_status = 'VERIFIED' AND verified_one_liner_count = 0
                    )::INTEGER AS points_without_verified_learning_items,
                    COUNT(*) FILTER (WHERE review_status = 'VERIFIED')::INTEGER AS reviewed_in_scope_points,
                    COUNT(*) FILTER (
                        WHERE review_status = 'VERIFIED'
                          AND mapping_status = 'MAPPED'
                          AND total_mapping_count > 0
                          AND verified_mapping_count = total_mapping_count
                          AND dimension_count = 9
                          AND gap_dimension_count = 0
                          AND verified_one_liner_count > 0
                    )::INTEGER AS fully_covered_points,
                    COALESCE(SUM(verified_one_liner_count), 0)::INTEGER AS verified_one_liner_count,
                    COALESCE(SUM(pending_link_count), 0)::INTEGER AS pending_learning_item_links
                FROM point_metrics
            """
            aggregate = self._connection.execute(summary_query, (syllabus_id,)).fetchone()
            if aggregate is None:
                raise RepositoryError("examinable-point coverage summary returned no row")

            detail_query = self._POINT_METRICS_CTE + """
                SELECT point_id, unit_id, point_type, point_statement, page_number,
                       source_locator, mapping_status, review_status, created_by, reviewed_by,
                       total_mapping_count, verified_mapping_count, dimension_count,
                       gap_dimension_count, verified_one_liner_count, pending_link_count
                FROM point_metrics
                ORDER BY unit_id, point_id
                LIMIT %s OFFSET %s
            """
            detail_rows = self._connection.execute(
                detail_query, (syllabus_id, limit, offset)
            ).fetchall()
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to build examinable-point coverage report") from exc

        summary = {
            "total_points": int(aggregate[0] or 0),
            "pending_points": int(aggregate[1] or 0),
            "rejected_points": int(aggregate[2] or 0),
            "mapping_gap_points": int(aggregate[3] or 0),
            "points_with_missing_dimensions": int(aggregate[4] or 0),
            "points_without_verified_learning_items": int(aggregate[5] or 0),
            "reviewed_in_scope_points": int(aggregate[6] or 0),
            "fully_covered_points": int(aggregate[7] or 0),
            "verified_one_liner_count": int(aggregate[8] or 0),
            "pending_learning_item_links": int(aggregate[9] or 0),
            # Historical questions deliberately remain a separate pool. Point links
            # to verified history are not part of this increment, so do not infer 0.
            "verified_history_question_count": None,
            "historical_question_linking": "NOT_IMPLEMENTED",
        }

        source_verified = str(source[1]) == "VERIFIED"
        syllabus_inventory_complete = source[2] is True
        points_inventory_complete = source[3] is True
        report_ready = (
            source_verified
            and syllabus_inventory_complete
            and points_inventory_complete
            and summary["reviewed_in_scope_points"] > 0
        )
        percentage = None
        if report_ready:
            percentage = round(
                summary["fully_covered_points"] * 100.0
                / summary["reviewed_in_scope_points"],
                2,
            )

        items: list[dict[str, object]] = []
        for row in detail_rows:
            items.append({
                "point_id": str(row[0]),
                "unit_id": str(row[1]),
                "point_type": str(row[2]),
                "point_statement": str(row[3]),
                "page_number": None if row[4] is None else int(row[4]),
                "source_locator": str(row[5]),
                "mapping_status": str(row[6]),
                "review_status": str(row[7]),
                "created_by": str(row[8]),
                "reviewed_by": None if row[9] is None else str(row[9]),
                "total_mapping_count": int(row[10] or 0),
                "verified_mapping_count": int(row[11] or 0),
                "dimension_count": int(row[12] or 0),
                "gap_dimension_count": int(row[13] or 0),
                "verified_one_liner_count": int(row[14] or 0),
                "pending_learning_item_links": int(row[15] or 0),
            })

        return {
            "syllabus_id": syllabus_id,
            "exam_id": str(source[0]),
            "source_status": str(source[1]),
            "syllabus_inventory_complete": syllabus_inventory_complete,
            "examinable_points_inventory_complete": points_inventory_complete,
            "examinable_points_reviewed_at": source[4].isoformat() if hasattr(source[4], "isoformat") else source[4],
            "examinable_points_reviewed_by": source[5],
            "examinable_points_review_note": str(source[6] or ""),
            "coverage_status": (
                "READY_FOR_COVERAGE_PERCENTAGE" if report_ready
                else "COVERAGE_UNKNOWN_INVENTORY_INCOMPLETE"
            ),
            "coverage_label": (
                "reviewed points covered" if report_ready
                else "COVERAGE UNKNOWN — INVENTORY INCOMPLETE"
            ),
            "coverage_percentage": percentage,
            "summary": summary,
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "returned": len(items),
            },
        }


__all__ = ["PostgresExaminablePointRepository"]
