from collections.abc import Iterable
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.matching import MatchEvidence, MatchType, QuestionMatch


class PostgresMatchRepository:
    """Persists symmetric question relationships and their evidence."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, match: QuestionMatch) -> None:
        left, right = sorted(
            (match.left_question_id, match.right_question_id)
        )
        evidence = match.evidence
        try:
            with self._connection.transaction():
                row = self._connection.execute(
                    """
                    INSERT INTO question_matches (
                        left_question_id,
                        right_question_id,
                        match_type,
                        confidence
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (left_question_id, right_question_id)
                    DO UPDATE SET
                        match_type = EXCLUDED.match_type,
                        confidence = EXCLUDED.confidence
                    RETURNING match_id
                    """,
                    (
                        left,
                        right,
                        match.match_type.value,
                        match.confidence,
                    ),
                ).fetchone()

                if row is None:
                    raise RepositoryError("match upsert returned no match_id")

                match_id = int(row[0])
                self._connection.execute(
                    "DELETE FROM match_evidence WHERE match_id = %s",
                    (match_id,),
                )
                for order, item in enumerate(evidence, start=1):
                    self._connection.execute(
                        """
                        INSERT INTO match_evidence (
                            match_id,
                            evidence_order,
                            method,
                            score,
                            notes
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            match_id,
                            order,
                            item.method,
                            item.score,
                            item.notes,
                        ),
                    )
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to persist question match") from exc

    def get_for_question(self, question_id: str) -> tuple[QuestionMatch, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT
                    match_id,
                    left_question_id,
                    right_question_id,
                    match_type,
                    confidence
                FROM question_matches
                WHERE left_question_id = %s
                   OR right_question_id = %s
                ORDER BY match_id
                """,
                (question_id, question_id),
            ).fetchall()

            result = []
            for row in rows:
                evidence_rows = self._connection.execute(
                    """
                    SELECT method, score, notes
                    FROM match_evidence
                    WHERE match_id = %s
                    ORDER BY evidence_order
                    """,
                    (row[0],),
                ).fetchall()
                result.append(
                    QuestionMatch(
                        left_question_id=str(row[1]),
                        right_question_id=str(row[2]),
                        match_type=MatchType(str(row[3])),
                        confidence=float(row[4]),
                        evidence=tuple(
                            MatchEvidence(
                                method=str(item[0]),
                                score=None if item[1] is None else float(item[1]),
                                notes=str(item[2]),
                            )
                            for item in evidence_rows
                        ),
                    )
                )
            return tuple(result)
        except Exception as exc:
            raise RepositoryError("failed to read question matches") from exc
