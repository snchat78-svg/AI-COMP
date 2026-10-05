import json
from collections.abc import Sequence
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
)


class PostgresAppearanceRepository:
    """PostgreSQL implementation of the Phase 4 appearance repository.

    The supplied connection must expose a transaction() context manager
    and execute() API compatible with Psycopg 3.
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, appearance: ExamAppearance) -> None:
        try:
            with self._connection.transaction():
                inserted = self._connection.execute(
                    """
                    INSERT INTO exam_appearances (
                        appearance_id,
                        question_id,
                        exam_id,
                        conducting_body_id,
                        year,
                        exam_date,
                        shift,
                        question_number,
                        original_question,
                        options,
                        correct_answer,
                        source_url,
                        paper_id,
                        verification_id,
                        match_type
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s::jsonb, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT DO NOTHING
                    RETURNING appearance_id
                    """,
                    self._appearance_values(appearance),
                ).fetchone()

                if inserted is not None:
                    canonical_id = inserted[0]
                else:
                    canonical_id = self._find_canonical_id(appearance)

                if canonical_id is None:
                    raise RepositoryError(
                        "could not resolve canonical exam appearance after insert conflict"
                    )

                self._connection.execute(
                    """
                    INSERT INTO appearance_sources (
                        appearance_id,
                        source_url,
                        paper_id,
                        verification_id
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        canonical_id,
                        appearance.source_url,
                        appearance.paper_id,
                        appearance.verification.verification_id,
                    ),
                )
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to persist exam appearance") from exc

    def get_for_question(self, question_id: str) -> tuple[ExamAppearance, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT
                    a.appearance_id,
                    a.question_id,
                    a.exam_id,
                    a.conducting_body_id,
                    a.year,
                    a.exam_date,
                    a.shift,
                    a.question_number,
                    a.original_question,
                    a.options,
                    a.correct_answer,
                    a.source_url,
                    a.paper_id,
                    a.match_type,
                    v.verification_id,
                    v.source_id,
                    v.source_url,
                    v.status,
                    v.evidence_type,
                    v.checked_at,
                    v.confidence,
                    v.notes
                FROM exam_appearances AS a
                JOIN source_verifications AS v
                  ON v.verification_id = a.verification_id
                WHERE a.question_id = %s
                ORDER BY
                    a.year DESC,
                    a.exam_date DESC NULLS LAST,
                    a.question_number,
                    a.appearance_id
                """,
                (question_id,),
            ).fetchall()
            return tuple(self._row_to_appearance(row) for row in rows)
        except Exception as exc:
            raise RepositoryError(
                "failed to read exam appearances for question"
            ) from exc

    def _find_canonical_id(self, appearance: ExamAppearance) -> str | None:
        row = self._connection.execute(
            """
            SELECT appearance_id
            FROM exam_appearances
            WHERE exam_id = %s
              AND year = %s
              AND shift IS NOT DISTINCT FROM %s
              AND question_number = %s
            LIMIT 1
            """,
            (
                appearance.exam_id,
                appearance.year,
                appearance.shift,
                appearance.question_number,
            ),
        ).fetchone()
        return None if row is None else str(row[0])

    @staticmethod
    def _appearance_values(appearance: ExamAppearance) -> Sequence[object]:
        return (
            appearance.appearance_id,
            appearance.question_id,
            appearance.exam_id,
            appearance.conducting_body_id,
            appearance.year,
            appearance.exam_date,
            appearance.shift,
            appearance.question_number,
            appearance.original_question,
            json.dumps(list(appearance.options), ensure_ascii=False),
            appearance.correct_answer,
            appearance.source_url,
            appearance.paper_id,
            appearance.verification.verification_id,
            appearance.match_type,
        )

    @staticmethod
    def _row_to_appearance(row: Sequence[object]) -> ExamAppearance:
        (
            appearance_id,
            question_id,
            exam_id,
            conducting_body_id,
            year,
            exam_date,
            shift,
            question_number,
            original_question,
            options,
            correct_answer,
            source_url,
            paper_id,
            match_type,
            verification_id,
            verification_source_id,
            verification_source_url,
            verification_status,
            evidence_type,
            checked_at,
            confidence,
            notes,
        ) = row

        if isinstance(options, str):
            options = json.loads(options)

        normalized_options = tuple(
            (str(item[0]), str(item[1])) for item in (options or ())
        )

        return ExamAppearance(
            appearance_id=str(appearance_id),
            question_id=str(question_id),
            exam_id=str(exam_id),
            conducting_body_id=(
                None if conducting_body_id is None else str(conducting_body_id)
            ),
            year=int(year),
            exam_date=(
                None
                if exam_date is None
                else (
                    exam_date.isoformat()
                    if hasattr(exam_date, "isoformat")
                    else str(exam_date)
                )
            ),
            shift=None if shift is None else str(shift),
            question_number=int(question_number),
            original_question=str(original_question),
            options=normalized_options,
            correct_answer=None if correct_answer is None else str(correct_answer),
            source_url=str(source_url),
            paper_id=str(paper_id),
            verification=SourceVerification(
                verification_id=str(verification_id),
                source_id=str(verification_source_id),
                source_url=str(verification_source_url),
                status=VerificationStatus(str(verification_status)),
                evidence_type=EvidenceType(str(evidence_type)),
                checked_at=checked_at,
                confidence=None if confidence is None else float(confidence),
                notes=str(notes),
            ),
            match_type=str(match_type),
        )
