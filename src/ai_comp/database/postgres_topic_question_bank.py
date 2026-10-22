from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.topic_question_bank import (
    OneLinerVerificationStatus,
    QuestionBankTopic,
    TopicOneLinerQA,
)


class PostgresTopicQuestionBankRepository:
    """Browse canonical concept topics and source-reviewed one-liner Q&A."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def list_subjects(self, *, limit: int = 100, offset: int = 0) -> tuple[tuple[str, int], ...]:
        self._validate_page(limit, offset)
        try:
            rows = self._connection.execute(
                """
                SELECT btrim(subject) AS subject_name,
                       COUNT(DISTINCT concept_id)::INTEGER AS concept_count
                FROM concepts
                WHERE subject IS NOT NULL AND btrim(subject) <> ''
                GROUP BY btrim(subject)
                ORDER BY lower(btrim(subject)), btrim(subject)
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            ).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list question-bank subjects") from exc
        return tuple((str(row[0]), int(row[1])) for row in rows)

    def list_topics(
        self,
        subject: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[QuestionBankTopic, ...]:
        self._validate_page(limit, offset)
        if not isinstance(subject, str) or not subject.strip() or subject != subject.strip():
            raise ValueError("subject must be a non-empty trimmed string")
        try:
            rows = self._connection.execute(
                """
                SELECT c.concept_id, c.label, btrim(c.subject), c.topic, c.subtopic,
                       COUNT(DISTINCT ol.one_liner_id)::INTEGER AS verified_one_liner_count
                FROM concepts AS c
                LEFT JOIN question_bank_one_liners AS ol
                  ON ol.concept_id = c.concept_id
                 AND ol.verification_status = 'VERIFIED'
                WHERE lower(btrim(c.subject)) = lower(%s)
                GROUP BY c.concept_id, c.label, c.subject, c.topic, c.subtopic
                ORDER BY lower(COALESCE(c.topic, '')),
                         lower(COALESCE(c.subtopic, '')),
                         lower(c.label), c.concept_id
                LIMIT %s OFFSET %s
                """,
                (subject, limit, offset),
            ).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list question-bank topics") from exc
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

    def list_one_liners(
        self,
        concept_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        verified_only: bool = True,
        language_code: str | None = None,
    ) -> tuple[TopicOneLinerQA, ...]:
        self._validate_page(limit, offset)
        if not isinstance(concept_id, str) or not concept_id.strip() or concept_id != concept_id.strip():
            raise ValueError("concept_id must be a non-empty trimmed string")
        if language_code is not None and (
            not language_code.strip() or language_code != language_code.strip()
        ):
            raise ValueError("language_code must be a non-empty trimmed string when supplied")

        conditions = ["concept_id = %s"]
        params: list[object] = [concept_id]
        if verified_only:
            conditions.append("verification_status = 'VERIFIED'")
        if language_code is not None:
            conditions.append("language_code = %s")
            params.append(language_code)
        params.extend((limit, offset))
        try:
            rows = self._connection.execute(
                f"""
                SELECT one_liner_id, concept_id, question_text, answer_text,
                       language_code, source_url, source_evidence, verification_status,
                       importance_score, reviewed_at, created_at, updated_at
                FROM question_bank_one_liners
                WHERE {' AND '.join(conditions)}
                ORDER BY importance_score DESC, lower(question_text), one_liner_id
                LIMIT %s OFFSET %s
                """,
                tuple(params),
            ).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list topic one-liners") from exc
        return tuple(self._one_liner_from_row(row) for row in rows)

    def save_one_liner(self, item: TopicOneLinerQA) -> None:
        """Persist a content-editor supplied item; the database enforces evidence for VERIFIED."""
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO question_bank_one_liners (
                        one_liner_id, concept_id, question_text, answer_text,
                        language_code, source_url, source_evidence,
                        verification_status, importance_score, content_hash,
                        reviewed_at, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                    ON CONFLICT (one_liner_id) DO UPDATE SET
                        concept_id = EXCLUDED.concept_id,
                        question_text = EXCLUDED.question_text,
                        answer_text = EXCLUDED.answer_text,
                        language_code = EXCLUDED.language_code,
                        source_url = EXCLUDED.source_url,
                        source_evidence = EXCLUDED.source_evidence,
                        verification_status = EXCLUDED.verification_status,
                        importance_score = EXCLUDED.importance_score,
                        content_hash = EXCLUDED.content_hash,
                        reviewed_at = EXCLUDED.reviewed_at,
                        updated_at = NOW()
                    """,
                    (
                        item.one_liner_id,
                        item.concept_id,
                        item.question_text,
                        item.answer_text,
                        item.language_code,
                        item.source_url,
                        item.source_evidence,
                        item.verification_status.value,
                        item.importance_score,
                        item.content_hash,
                        item.reviewed_at,
                        item.created_at,
                        item.updated_at,
                    ),
                )
        except Exception as exc:
            raise RepositoryError("failed to persist topic one-liner") from exc

    @staticmethod
    def _validate_page(limit: int, offset: int) -> None:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 100000:
            raise ValueError("offset must be between 0 and 100000")

    @staticmethod
    def _one_liner_from_row(row: Sequence[object]) -> TopicOneLinerQA:
        return TopicOneLinerQA(
            one_liner_id=str(row[0]),
            concept_id=str(row[1]),
            question_text=str(row[2]),
            answer_text=str(row[3]),
            language_code=str(row[4]),
            source_url=None if row[5] is None else str(row[5]),
            source_evidence=str(row[6]),
            verification_status=OneLinerVerificationStatus(str(row[7])),
            importance_score=float(row[8]),
            reviewed_at=row[9],
            created_at=row[10],
            updated_at=row[11],
        )


__all__ = ["PostgresTopicQuestionBankRepository"]
