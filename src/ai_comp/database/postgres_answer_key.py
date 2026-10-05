from collections.abc import Iterable
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.questions import AnswerKeyEntry


class PostgresAnswerKeyRepository:
    """Persists source-observed answer-key entries separately from questions."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save_many(
        self,
        document_id: str,
        entries: Iterable[AnswerKeyEntry],
    ) -> None:
        try:
            with self._connection.transaction():
                for entry in entries:
                    self._connection.execute(
                        """
                        INSERT INTO answer_key_entries (
                            document_id,
                            question_number,
                            answer_key,
                            raw_text,
                            line_number
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (document_id, question_number) DO UPDATE SET
                            answer_key = EXCLUDED.answer_key,
                            raw_text = EXCLUDED.raw_text,
                            line_number = EXCLUDED.line_number
                        """,
                        (
                            document_id,
                            entry.question_number,
                            entry.answer_key,
                            entry.raw_text,
                            entry.line_number,
                        ),
                    )
        except Exception as exc:
            raise RepositoryError("failed to persist answer key entries") from exc

    def get_for_document(
        self,
        document_id: str,
    ) -> tuple[AnswerKeyEntry, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT question_number, answer_key, raw_text, line_number
                FROM answer_key_entries
                WHERE document_id = %s
                ORDER BY question_number, line_number
                """,
                (document_id,),
            ).fetchall()
            return tuple(
                AnswerKeyEntry(
                    question_number=int(row[0]),
                    answer_key=str(row[1]),
                    raw_text=str(row[2]),
                    line_number=int(row[3]),
                )
                for row in rows
            )
        except Exception as exc:
            raise RepositoryError(
                "failed to read answer key entries"
            ) from exc
