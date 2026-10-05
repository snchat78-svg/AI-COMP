from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.answers import (
    AnswerResolution,
    AnswerResolutionMethod,
    AnswerResolutionStatus,
)


class PostgresAnswerResolutionRepository:
    """Persists deterministic mappings between source keys and question options."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, resolution: AnswerResolution) -> None:
        if not resolution.question_id:
            raise ValueError("resolved answer must reference a question")
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO question_answer_records (
                        question_id,
                        document_id,
                        question_number,
                        answer_key,
                        selected_option_key,
                        status,
                        method,
                        source_line,
                        notes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (question_id, document_id) DO UPDATE SET
                        question_number = EXCLUDED.question_number,
                        answer_key = EXCLUDED.answer_key,
                        selected_option_key = EXCLUDED.selected_option_key,
                        status = EXCLUDED.status,
                        method = EXCLUDED.method,
                        source_line = EXCLUDED.source_line,
                        notes = EXCLUDED.notes
                    """,
                    (
                        resolution.question_id,
                        resolution.document_id,
                        resolution.question_number,
                        resolution.answer_key,
                        resolution.selected_option_key,
                        resolution.status.value,
                        None if resolution.method is None else resolution.method.value,
                        resolution.source_line,
                        resolution.notes,
                    ),
                )
        except Exception as exc:
            raise RepositoryError("failed to persist answer resolution") from exc

    def get_for_question(
        self,
        question_id: str,
    ) -> tuple[AnswerResolution, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT
                    question_id,
                    document_id,
                    question_number,
                    answer_key,
                    selected_option_key,
                    status,
                    method,
                    source_line,
                    notes
                FROM question_answer_records
                WHERE question_id = %s
                ORDER BY document_id, answer_record_id
                """,
                (question_id,),
            ).fetchall()
            return tuple(
                AnswerResolution(
                    question_id=str(row[0]),
                    document_id=str(row[1]),
                    question_number=int(row[2]),
                    answer_key=str(row[3]),
                    selected_option_key=(
                        None if row[4] is None else str(row[4])
                    ),
                    status=AnswerResolutionStatus(str(row[5])),
                    method=(
                        None
                        if row[6] is None
                        else AnswerResolutionMethod(str(row[6]))
                    ),
                    source_line=int(row[7]),
                    notes=str(row[8]),
                )
                for row in rows
            )
        except Exception as exc:
            raise RepositoryError(
                "failed to read answer resolutions"
            ) from exc
