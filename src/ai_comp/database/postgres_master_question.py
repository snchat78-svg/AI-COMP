import json
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.master_questions import (
    MasterMembershipType,
    MasterQuestion,
    MasterQuestionMembership,
)
from ai_comp.domain.questions import QuestionKind, QuestionOption


class PostgresMasterQuestionRepository:
    """PostgreSQL persistence for canonical master-question identities."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save_master(self, master: MasterQuestion) -> None:
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO master_questions (
                        master_question_id,
                        canonical_question_id,
                        stem,
                        kind,
                        concept_id,
                        status,
                        merged_into_master_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (master_question_id) DO UPDATE SET
                        canonical_question_id = EXCLUDED.canonical_question_id,
                        stem = EXCLUDED.stem,
                        kind = EXCLUDED.kind,
                        concept_id = EXCLUDED.concept_id,
                        status = EXCLUDED.status,
                        merged_into_master_id = EXCLUDED.merged_into_master_id
                    """,
                    (
                        master.master_question_id,
                        master.canonical_question_id,
                        master.stem,
                        master.kind.value,
                        master.concept_id,
                        master.status.value,
                        master.merged_into_master_id,
                    ),
                )

                self._connection.execute(
                    "DELETE FROM master_question_options WHERE master_question_id = %s",
                    (master.master_question_id,),
                )
                for order, option in enumerate(master.options, start=1):
                    self._connection.execute(
                        """
                        INSERT INTO master_question_options (
                            master_question_id,
                            option_key,
                            option_text,
                            option_order
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            master.master_question_id,
                            option.key,
                            option.text,
                            order,
                        ),
                    )
        except Exception as exc:
            raise RepositoryError(
                "failed to persist master question"
            ) from exc

    def get_master(self, master_question_id: str) -> MasterQuestion | None:
        try:
            row = self._connection.execute(
                """
                SELECT
                    master_question_id,
                    canonical_question_id,
                    stem,
                    kind,
                    concept_id,
                    status,
                    merged_into_master_id
                FROM master_questions
                WHERE master_question_id = %s
                """,
                (master_question_id,),
            ).fetchone()
            if row is None:
                return None

            options = self._connection.execute(
                """
                SELECT option_key, option_text
                FROM master_question_options
                WHERE master_question_id = %s
                ORDER BY option_order
                """,
                (master_question_id,),
            ).fetchall()

            return self._master_from_rows(row, options)
        except Exception as exc:
            raise RepositoryError(
                "failed to read master question"
            ) from exc

    def get_master_for_question(
        self,
        question_id: str,
    ) -> MasterQuestion | None:
        try:
            row = self._connection.execute(
                """
                SELECT master_question_id
                FROM master_question_memberships
                WHERE question_id = %s
                """,
                (question_id,),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError(
                "failed to find question master"
            ) from exc

        if row is None:
            return None
        return self.get_master(str(row[0]))

    def save_membership(
        self,
        membership: MasterQuestionMembership,
    ) -> None:
        try:
            with self._connection.transaction():
                existing = self._connection.execute(
                    """
                    SELECT
                        master_question_id,
                        question_id,
                        relationship,
                        confidence
                    FROM master_question_memberships
                    WHERE question_id = %s
                    """,
                    (membership.question_id,),
                ).fetchone()

                if existing is not None:
                    current = MasterQuestionMembership(
                        master_question_id=str(existing[0]),
                        question_id=str(existing[1]),
                        relationship=MasterMembershipType(str(existing[2])),
                        confidence=float(existing[3]),
                    )
                    if current != membership:
                        raise RepositoryError(
                            "question is already assigned to a different master question"
                        )
                    return

                self._connection.execute(
                    """
                    INSERT INTO master_question_memberships (
                        master_question_id,
                        question_id,
                        relationship,
                        confidence
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        membership.master_question_id,
                        membership.question_id,
                        membership.relationship.value,
                        membership.confidence,
                    ),
                )
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(
                "failed to persist master membership"
            ) from exc

    def get_membership_for_question(
        self,
        question_id: str,
    ) -> MasterQuestionMembership | None:
        try:
            row = self._connection.execute(
                """
                SELECT
                    master_question_id,
                    question_id,
                    relationship,
                    confidence
                FROM master_question_memberships
                WHERE question_id = %s
                """,
                (question_id,),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError(
                "failed to read master membership"
            ) from exc

        if row is None:
            return None
        return MasterQuestionMembership(
            master_question_id=str(row[0]),
            question_id=str(row[1]),
            relationship=MasterMembershipType(str(row[2])),
            confidence=float(row[3]),
        )

    def get_memberships_for_master(
        self,
        master_question_id: str,
    ) -> tuple[MasterQuestionMembership, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT
                    master_question_id,
                    question_id,
                    relationship,
                    confidence
                FROM master_question_memberships
                WHERE master_question_id = %s
                ORDER BY
                    CASE relationship
                        WHEN 'CANONICAL' THEN 0
                        WHEN 'EXACT' THEN 1
                        ELSE 2
                    END,
                    question_id
                """,
                (master_question_id,),
            ).fetchall()
            return tuple(
                MasterQuestionMembership(
                    master_question_id=str(row[0]),
                    question_id=str(row[1]),
                    relationship=MasterMembershipType(str(row[2])),
                    confidence=float(row[3]),
                )
                for row in rows
            )
        except Exception as exc:
            raise RepositoryError(
                "failed to read master memberships"
            ) from exc

    @staticmethod
    def _master_from_rows(row, options) -> MasterQuestion:
        return MasterQuestion(
            master_question_id=str(row[0]),
            canonical_question_id=str(row[1]),
            stem=str(row[2]),
            kind=QuestionKind(str(row[3])),
            concept_id=None if row[4] is None else str(row[4]),
            status=row[5],
            merged_into_master_id=(
                None if row[6] is None else str(row[6])
            ),
            options=tuple(
                QuestionOption(
                    key=str(item[0]),
                    text=str(item[1]),
                )
                for item in options
            ),
        )
