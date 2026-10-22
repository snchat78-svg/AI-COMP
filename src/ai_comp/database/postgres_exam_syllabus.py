from __future__ import annotations

from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.topic_question_bank import QuestionBankTopic


class PostgresExamSyllabusRepository:
    """Read exam profiles and only independently reviewed syllabus-to-concept mappings."""

    _VERIFIED_MAPPING_SQL = """
        d.source_status = 'VERIFIED'
        AND m.applicability_status IN ('IN_SCOPE', 'OUT_OF_SCOPE')
        AND m.reviewed_at IS NOT NULL
        AND m.reviewed_by IS NOT NULL
        AND btrim(m.reviewed_by) <> ''
        AND btrim(m.source_locator) <> ''
        AND btrim(m.source_evidence) <> ''
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def list_profiles(self, *, limit: int = 100) -> tuple[dict[str, object], ...]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        query = f"""
            SELECT e.exam_id, e.name, d.syllabus_id, d.source_title, d.source_url,
                   d.notification_number, d.source_status,
                   COUNT(DISTINCT c.concept_id)::INTEGER AS concept_count,
                   COUNT(DISTINCT c.concept_id) FILTER (
                       WHERE m.applicability_status = 'IN_SCOPE'
                         AND {self._VERIFIED_MAPPING_SQL}
                   )::INTEGER AS mapped_concept_count,
                   COUNT(DISTINCT c.concept_id) FILTER (
                       WHERE m.applicability_status = 'OUT_OF_SCOPE'
                         AND {self._VERIFIED_MAPPING_SQL}
                   )::INTEGER AS excluded_concept_count
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
            total = int(row[7] or 0)
            mapped = int(row[8] or 0)
            excluded = int(row[9] or 0)
            unmapped = max(0, total - mapped - excluded)
            source_status = str(row[6])
            selection_ready = source_status == "VERIFIED" and unmapped == 0
            profiles.append({
                "exam_id": str(row[0]),
                "exam_name": str(row[1]),
                "syllabus_id": str(row[2]),
                "syllabus_title": str(row[3]),
                "source_url": str(row[4]),
                "notification_number": str(row[5] or ""),
                "source_status": source_status,
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
