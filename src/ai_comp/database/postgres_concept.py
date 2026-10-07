from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.matching import ConceptRecord


class PostgresConceptRepository:
    """PostgreSQL adapter for explicit concept taxonomy and question links."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, concept: ConceptRecord) -> None:
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO concepts (
                        concept_id, label, subject, topic, subtopic
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (concept_id) DO UPDATE SET
                        label = EXCLUDED.label,
                        subject = EXCLUDED.subject,
                        topic = EXCLUDED.topic,
                        subtopic = EXCLUDED.subtopic
                    """,
                    (
                        concept.concept_id,
                        concept.label,
                        concept.subject,
                        concept.topic,
                        concept.subtopic,
                    ),
                )
        except Exception as exc:
            raise RepositoryError("failed to persist concept") from exc

    def get(self, concept_id: str) -> ConceptRecord | None:
        try:
            row = self._connection.execute(
                """
                SELECT concept_id, label, subject, topic, subtopic
                FROM concepts
                WHERE concept_id = %s
                """,
                (concept_id,),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to read concept") from exc

        if row is None:
            return None
        return ConceptRecord(
            concept_id=str(row[0]),
            label=str(row[1]),
            subject=None if row[2] is None else str(row[2]),
            topic=None if row[3] is None else str(row[3]),
            subtopic=None if row[4] is None else str(row[4]),
        )

    def link_question(self, question_id: str, concept_id: str) -> None:
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO question_concepts (question_id, concept_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (question_id, concept_id),
                )
        except Exception as exc:
            raise RepositoryError("failed to link question concept") from exc
