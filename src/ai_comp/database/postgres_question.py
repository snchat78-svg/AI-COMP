from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.questions import QuestionCandidate, QuestionKind, QuestionOption
from ai_comp.matching.duplicate import duplicate_key


class PostgresQuestionRepository:
    """PostgreSQL persistence for extracted QuestionCandidate records."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, question: QuestionCandidate) -> None:
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO questions (
                        question_id,
                        document_id,
                        document_sha256,
                        question_number,
                        stem,
                        kind,
                        raw_text,
                        start_line,
                        end_line,
                        duplicate_key
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (question_id) DO UPDATE SET
                        document_id = EXCLUDED.document_id,
                        document_sha256 = EXCLUDED.document_sha256,
                        question_number = EXCLUDED.question_number,
                        stem = EXCLUDED.stem,
                        kind = EXCLUDED.kind,
                        raw_text = EXCLUDED.raw_text,
                        start_line = EXCLUDED.start_line,
                        end_line = EXCLUDED.end_line,
                        duplicate_key = EXCLUDED.duplicate_key
                    """,
                    (
                        question.question_id,
                        question.document_id,
                        question.document_sha256,
                        question.question_number,
                        question.stem,
                        question.kind.value,
                        question.raw_text,
                        question.start_line,
                        question.end_line,
                        duplicate_key(question).normalized_key,
                    ),
                )
                self._connection.execute(
                    "DELETE FROM question_options WHERE question_id = %s",
                    (question.question_id,),
                )
                for order, option in enumerate(question.options, start=1):
                    self._connection.execute(
                        """
                        INSERT INTO question_options (
                            question_id, option_key, option_text, option_order
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            question.question_id,
                            option.key,
                            option.text,
                            order,
                        ),
                    )
        except Exception as exc:
            raise RepositoryError("failed to persist question") from exc

    def get(self, question_id: str) -> QuestionCandidate | None:
        try:
            row = self._connection.execute(
                """
                SELECT
                    question_id,
                    document_id,
                    document_sha256,
                    question_number,
                    stem,
                    kind,
                    raw_text,
                    start_line,
                    end_line
                FROM questions
                WHERE question_id = %s
                """,
                (question_id,),
            ).fetchone()
            if row is None:
                return None

            options = self._connection.execute(
                """
                SELECT option_key, option_text
                FROM question_options
                WHERE question_id = %s
                ORDER BY option_order
                """,
                (question_id,),
            ).fetchall()
            return self._from_rows(row, options)
        except Exception as exc:
            raise RepositoryError("failed to read question") from exc

    def get_for_document(self, document_id: str) -> tuple[QuestionCandidate, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT
                    question_id,
                    document_id,
                    document_sha256,
                    question_number,
                    stem,
                    kind,
                    raw_text,
                    start_line,
                    end_line
                FROM questions
                WHERE document_id = %s
                ORDER BY question_number, start_line, question_id
                """,
                (document_id,),
            ).fetchall()

            result = []
            for row in rows:
                options = self._connection.execute(
                    """
                    SELECT option_key, option_text
                    FROM question_options
                    WHERE question_id = %s
                    ORDER BY option_order
                    """,
                    (row[0],),
                ).fetchall()
                result.append(self._from_rows(row, options))
            return tuple(result)
        except Exception as exc:
            raise RepositoryError("failed to read document questions") from exc

    @staticmethod
    def _from_rows(row, options) -> QuestionCandidate:
        return QuestionCandidate(
            question_id=str(row[0]),
            document_id=str(row[1]),
            document_sha256=str(row[2]),
            question_number=int(row[3]),
            stem=str(row[4]),
            kind=QuestionKind(str(row[5])),
            raw_text=str(row[6]),
            start_line=int(row[7]),
            end_line=int(row[8]),
            options=tuple(
                QuestionOption(key=str(item[0]), text=str(item[1]))
                for item in options
            ),
        )
