from __future__ import annotations

from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.topic_question_bank import QuestionBankTopic


class PostgresExamSyllabusRepository:
    """Read exam profiles and only independently reviewed syllabus-to-concept mappings."""

    _VERIFIED_MAPPING_SQL = """
        d.source_status = 'VERIFIED'
        AND d.syllabus_inventory_complete = TRUE
        AND m.applicability_status IN ('IN_SCOPE', 'OUT_OF_SCOPE')
        AND m.reviewed_at IS NOT NULL
        AND m.reviewed_by IS NOT NULL
        AND btrim(m.reviewed_by) <> ''
        AND btrim(m.source_locator) <> ''
        AND btrim(m.source_evidence) <> ''
    """

    _PROFILE_COMPLETENESS_SQL = """
        EXISTS (
            SELECT 1
            FROM exam_syllabus_inventory_units AS reviewed_inventory
            WHERE reviewed_inventory.syllabus_id = d.syllabus_id
        )
        AND NOT EXISTS (
            SELECT 1
            FROM concepts AS required_concept
            LEFT JOIN exam_concept_applicability AS required_map
              ON required_map.syllabus_id = d.syllabus_id
             AND required_map.concept_id = required_concept.concept_id
            WHERE required_map.concept_id IS NULL
               OR required_map.applicability_status NOT IN ('IN_SCOPE', 'OUT_OF_SCOPE')
               OR required_map.reviewed_at IS NULL
               OR required_map.reviewed_by IS NULL
               OR btrim(required_map.reviewed_by) = ''
               OR btrim(required_map.source_locator) = ''
               OR btrim(required_map.source_evidence) = ''
               OR btrim(required_map.review_note) = ''
        )
        AND NOT EXISTS (
            SELECT 1
            FROM exam_syllabus_inventory_units AS required_unit
            WHERE required_unit.syllabus_id = d.syllabus_id
              AND (
                  required_unit.review_status <> 'VERIFIED'
                  OR required_unit.reviewed_at IS NULL
                  OR required_unit.reviewed_by IS NULL
                  OR btrim(required_unit.reviewed_by) = ''
                  OR btrim(required_unit.review_note) = ''
                  OR NOT EXISTS (
                      SELECT 1
                      FROM exam_syllabus_unit_concepts AS verified_link
                      WHERE verified_link.syllabus_id = required_unit.syllabus_id
                        AND verified_link.unit_id = required_unit.unit_id
                        AND verified_link.review_status = 'VERIFIED'
                        AND verified_link.reviewed_at IS NOT NULL
                        AND verified_link.reviewed_by IS NOT NULL
                        AND btrim(verified_link.reviewed_by) <> ''
                        AND btrim(verified_link.source_locator) <> ''
                        AND btrim(verified_link.source_evidence) <> ''
                        AND btrim(verified_link.review_note) <> ''
                  )
              )
        )
        AND NOT EXISTS (
            SELECT 1
            FROM exam_concept_applicability AS in_scope
            WHERE in_scope.syllabus_id = d.syllabus_id
              AND in_scope.applicability_status = 'IN_SCOPE'
              AND NOT EXISTS (
                  SELECT 1
                  FROM exam_syllabus_unit_concepts AS verified_concept_link
                  WHERE verified_concept_link.syllabus_id = in_scope.syllabus_id
                    AND verified_concept_link.concept_id = in_scope.concept_id
                    AND verified_concept_link.review_status = 'VERIFIED'
              )
        )
        AND NOT EXISTS (
            SELECT 1 FROM exam_syllabus_unit_concepts AS pending_link
            WHERE pending_link.syllabus_id = d.syllabus_id
              AND pending_link.review_status = 'NEEDS_REVIEW'
        )
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def list_profiles(self, *, limit: int = 100) -> tuple[dict[str, object], ...]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        query = f"""
            SELECT e.exam_id, e.name, d.syllabus_id, d.source_title, d.source_url,
                   d.notification_number, d.source_status, d.syllabus_inventory_complete,
                   COUNT(DISTINCT c.concept_id)::INTEGER AS concept_count,
                   COUNT(DISTINCT c.concept_id) FILTER (
                       WHERE m.applicability_status = 'IN_SCOPE'
                         AND {self._VERIFIED_MAPPING_SQL}
                   )::INTEGER AS mapped_concept_count,
                   COUNT(DISTINCT c.concept_id) FILTER (
                       WHERE m.applicability_status = 'OUT_OF_SCOPE'
                         AND {self._VERIFIED_MAPPING_SQL}
                   )::INTEGER AS excluded_concept_count
                   ,
                   CASE WHEN
                       EXISTS (
                           SELECT 1 FROM exam_syllabus_inventory_units AS inventory
                           WHERE inventory.syllabus_id = d.syllabus_id
                       )
                       AND NOT EXISTS (
                           SELECT 1
                           FROM exam_syllabus_inventory_units AS inventory
                           WHERE inventory.syllabus_id = d.syllabus_id
                             AND (
                                 inventory.review_status <> 'VERIFIED'
                                 OR inventory.reviewed_at IS NULL
                                 OR inventory.reviewed_by IS NULL
                                 OR btrim(inventory.reviewed_by) = ''
                                 OR btrim(inventory.review_note) = ''
                                 OR NOT EXISTS (
                                     SELECT 1 FROM exam_syllabus_unit_concepts AS link
                                     WHERE link.syllabus_id = inventory.syllabus_id
                                       AND link.unit_id = inventory.unit_id
                                       AND link.review_status = 'VERIFIED'
                                       AND link.reviewed_at IS NOT NULL
                                       AND link.reviewed_by IS NOT NULL
                                       AND btrim(link.reviewed_by) <> ''
                                       AND btrim(link.source_locator) <> ''
                                       AND btrim(link.source_evidence) <> ''
                                       AND btrim(link.review_note) <> ''
                                 )
                             )
                       )
                       AND NOT EXISTS (
                           SELECT 1
                           FROM exam_concept_applicability AS in_scope
                           WHERE in_scope.syllabus_id = d.syllabus_id
                             AND in_scope.applicability_status = 'IN_SCOPE'
                             AND NOT EXISTS (
                                 SELECT 1 FROM exam_syllabus_unit_concepts AS link
                                 WHERE link.syllabus_id = in_scope.syllabus_id
                                   AND link.concept_id = in_scope.concept_id
                                   AND link.review_status = 'VERIFIED'
                             )
                       )
                       AND NOT EXISTS (
                           SELECT 1 FROM exam_syllabus_unit_concepts AS pending_link
                           WHERE pending_link.syllabus_id = d.syllabus_id
                             AND pending_link.review_status = 'NEEDS_REVIEW'
                       )
                   THEN TRUE ELSE FALSE END AS inventory_mapping_ready
            FROM exams AS e
            JOIN exam_syllabus_documents AS d
              ON d.exam_id = e.exam_id AND d.is_current = TRUE
            LEFT JOIN concepts AS c ON TRUE
            LEFT JOIN exam_concept_applicability AS m
              ON m.syllabus_id = d.syllabus_id AND m.concept_id = c.concept_id
            WHERE e.active = TRUE
            GROUP BY e.exam_id, e.name, d.syllabus_id, d.source_title,
                     d.source_url, d.notification_number, d.source_status
            ORDER BY lower(e.name), e.exam_id
            LIMIT %s
        """
        try:
            rows = self._connection.execute(query, (limit,)).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list exam syllabus profiles") from exc

        profiles: list[dict[str, object]] = []
        for row in rows:
            source_status = str(row[6])
            inventory_complete = row[7] is True
            total = int(row[8] or 0)
            mapped = int(row[9] or 0)
            excluded = int(row[10] or 0)
            unmapped = max(0, total - mapped - excluded)
            selection_ready = (
                source_status == "VERIFIED"
                and inventory_complete
                and total > 0
                and unmapped == 0
                and len(row) > 11
                and row[11] is True
            )
            profiles.append({
                "exam_id": str(row[0]),
                "exam_name": str(row[1]),
                "syllabus_id": str(row[2]),
                "syllabus_title": str(row[3]),
                "source_url": str(row[4]),
                "notification_number": str(row[5] or ""),
                "source_status": source_status,
                "syllabus_inventory_complete": inventory_complete,
                "concept_count": total,
                "mapped_concept_count": mapped,
                "excluded_concept_count": excluded,
                "unmapped_concept_count": unmapped,
                "selection_ready": selection_ready,
            })
        return tuple(profiles)

    def profile_exists(self, exam_id: str) -> bool:
        if not isinstance(exam_id, str) or not exam_id.strip() or exam_id != exam_id.strip():
            raise ValueError("exam_id must be a non-empty trimmed string")
        try:
            row = self._connection.execute(
                """
                SELECT 1
                FROM exams AS e
                JOIN exam_syllabus_documents AS d
                  ON d.exam_id = e.exam_id AND d.is_current = TRUE
                WHERE e.exam_id = %s AND e.active = TRUE
                LIMIT 1
                """,
                (exam_id,),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to check exam syllabus profile") from exc
        return row is not None

    def list_subjects(self, exam_id: str, *, limit: int = 100) -> tuple[tuple[str, int], ...]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        if not isinstance(exam_id, str) or not exam_id.strip() or exam_id != exam_id.strip():
            raise ValueError("exam_id must be a non-empty trimmed string")
        query = f"""
            SELECT btrim(c.subject) AS subject_name,
                   COUNT(DISTINCT c.concept_id)::INTEGER AS concept_count
            FROM concepts AS c
            JOIN exam_concept_applicability AS m ON m.concept_id = c.concept_id
            JOIN exam_syllabus_documents AS d ON d.syllabus_id = m.syllabus_id
            WHERE d.exam_id = %s
              AND d.is_current = TRUE
              AND {self._VERIFIED_MAPPING_SQL}
              AND {self._PROFILE_COMPLETENESS_SQL}
              AND m.applicability_status = 'IN_SCOPE'
              AND c.subject IS NOT NULL AND btrim(c.subject) <> ''
            GROUP BY btrim(c.subject)
            ORDER BY lower(btrim(c.subject)), btrim(c.subject)
            LIMIT %s
        """
        try:
            rows = self._connection.execute(query, (exam_id, limit)).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list exam syllabus subjects") from exc
        return tuple((str(row[0]), int(row[1])) for row in rows)

    def list_topics(
        self,
        exam_id: str,
        subject: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[QuestionBankTopic, ...]:
        self._validate_page(limit, offset)
        if not isinstance(exam_id, str) or not exam_id.strip() or exam_id != exam_id.strip():
            raise ValueError("exam_id must be a non-empty trimmed string")
        if not isinstance(subject, str) or not subject.strip() or subject != subject.strip():
            raise ValueError("subject must be a non-empty trimmed string")
        query = f"""
            SELECT c.concept_id, c.label, btrim(c.subject), c.topic, c.subtopic,
                   COUNT(DISTINCT ol.one_liner_id)::INTEGER AS verified_one_liner_count
            FROM concepts AS c
            JOIN exam_concept_applicability AS m ON m.concept_id = c.concept_id
            JOIN exam_syllabus_documents AS d ON d.syllabus_id = m.syllabus_id
            LEFT JOIN question_bank_one_liners AS ol
              ON ol.concept_id = c.concept_id
             AND ol.verification_status = 'VERIFIED'
            WHERE d.exam_id = %s
              AND d.is_current = TRUE
              AND {self._VERIFIED_MAPPING_SQL}
              AND {self._PROFILE_COMPLETENESS_SQL}
              AND m.applicability_status = 'IN_SCOPE'
              AND lower(btrim(c.subject)) = lower(%s)
            GROUP BY c.concept_id, c.label, c.subject, c.topic, c.subtopic
            ORDER BY lower(COALESCE(c.topic, '')),
                     lower(COALESCE(c.subtopic, '')),
                     lower(c.label), c.concept_id
            LIMIT %s OFFSET %s
        """
        try:
            rows = self._connection.execute(query, (exam_id, subject, limit, offset)).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list exam-mapped question-bank topics") from exc
        return tuple(
            QuestionBankTopic(
                concept_id=str(row[0]),
                label=str(row[1]),
                subject=str(row[2]),
                topic=None if row[3] is None else str(row[3]),
                subtopic=None if row[4] is None else str(row[4]),
                verified_one_liner_count=int(row[5]),
            )
            for row in rows
        )

    @staticmethod
    def _validate_page(limit: int, offset: int) -> None:
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        if not isinstance(offset, int) or not 0 <= offset <= 100000:
            raise ValueError("offset must be an integer between 0 and 100000")
