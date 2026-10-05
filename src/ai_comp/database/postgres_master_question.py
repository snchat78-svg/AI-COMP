from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.master_questions import (
    MasterMembershipType,
    MasterQuestion,
    MasterQuestionMembership,
    MasterQuestionStatus,
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

    def list_masters(
        self,
        *,
        status: MasterQuestionStatus | None = None,
        concept_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[MasterQuestion, ...]:
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        if offset < 0:
            raise ValueError("offset must be non-negative")

        conditions = []
        params: list[object] = []
        if status is not None:
            conditions.append("status = %s")
            params.append(status.value)
        if concept_id is not None:
            conditions.append("concept_id = %s")
            params.append(concept_id)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        rows = self._fetchall(
            f"""
            SELECT
                master_question_id,
                canonical_question_id,
                stem,
                kind,
                concept_id,
                status,
                merged_into_master_id
            FROM master_questions
            {where}
            ORDER BY master_question_id
            LIMIT %s OFFSET %s
            """,
            tuple(params + [limit, offset]),
        )
        result = []
        for row in rows:
            options = self._fetchall(
                """
                SELECT option_key, option_text
                FROM master_question_options
                WHERE master_question_id = %s
                ORDER BY option_order
                """,
                (row[0],),
            )
            result.append(self._master_from_rows(row, options))
        return tuple(result)

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

    def merge_masters(
        self,
        source_master_id: str,
        target_master_id: str,
        *,
        reason: str,
    ) -> int:
        if source_master_id == target_master_id:
            raise ValueError("source and target masters must differ")
        if not reason.strip():
            raise ValueError("merge reason must not be empty")

        try:
            with self._connection.transaction():
                source_status, target_status = self._locked_master_statuses(
                    source_master_id,
                    target_master_id,
                )
                self._require_active_status(source_master_id, source_status)
                self._require_active_status(target_master_id, target_status)

                rows = self._connection.execute(
                    """
                    SELECT question_id, relationship, confidence
                    FROM master_question_memberships
                    WHERE master_question_id = %s
                    ORDER BY question_id
                    FOR UPDATE
                    """,
                    (source_master_id,),
                ).fetchall()

                moved = 0
                for question_id, relationship, confidence in rows:
                    target_relationship = (
                        MasterMembershipType.EXACT.value
                        if str(relationship) == MasterMembershipType.CANONICAL.value
                        else str(relationship)
                    )
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
                            target_master_id,
                            question_id,
                            target_relationship,
                            confidence,
                        ),
                    )
                    self._connection.execute(
                        """
                        DELETE FROM master_question_memberships
                        WHERE master_question_id = %s
                          AND question_id = %s
                        """,
                        (source_master_id, question_id),
                    )
                    moved += 1

                self._connection.execute(
                    """
                    UPDATE master_questions
                    SET status = %s,
                        merged_into_master_id = %s
                    WHERE master_question_id = %s
                    """,
                    (
                        MasterQuestionStatus.MERGED.value,
                        target_master_id,
                        source_master_id,
                    ),
                )
                self._connection.execute(
                    """
                    INSERT INTO master_merge_events (
                        source_master_id,
                        target_master_id,
                        reason
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (source_master_id, target_master_id, reason.strip()),
                )
                return moved
        except (RepositoryError, ValueError):
            raise
        except Exception as exc:
            raise RepositoryError("failed to merge master questions") from exc

    def reassign_question(
        self,
        question_id: str,
        target_master_id: str,
        *,
        relationship: MasterMembershipType,
        confidence: float,
        reason: str,
    ) -> None:
        if relationship is MasterMembershipType.CANONICAL:
            raise ValueError("canonical membership cannot be reassigned")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not reason.strip():
            raise ValueError("repair reason must not be empty")

        try:
            with self._connection.transaction():
                target_status = self._connection.execute(
                    """
                    SELECT status
                    FROM master_questions
                    WHERE master_question_id = %s
                    FOR UPDATE
                    """,
                    (target_master_id,),
                ).fetchone()
                if target_status is None:
                    raise ValueError(
                        f"master question not found: {target_master_id}"
                    )
                self._require_active_status(
                    target_master_id,
                    str(target_status[0]),
                )

                current = self._connection.execute(
                    """
                    SELECT
                        master_question_id,
                        relationship,
                        confidence
                    FROM master_question_memberships
                    WHERE question_id = %s
                    FOR UPDATE
                    """,
                    (question_id,),
                ).fetchone()
                if current is None:
                    raise ValueError(
                        "question has no current master membership"
                    )

                source_master_id = str(current[0])
                previous_relationship = MasterMembershipType(str(current[1]))
                previous_confidence = float(current[2])

                if source_master_id == target_master_id:
                    raise ValueError(
                        "question is already assigned to target master"
                    )
                self._require_active_status(
                    source_master_id,
                    str(
                        self._connection.execute(
                            """
                            SELECT status
                            FROM master_questions
                            WHERE master_question_id = %s
                            """,
                            (source_master_id,),
                        ).fetchone()[0]
                    ),
                )
                if previous_relationship is MasterMembershipType.CANONICAL:
                    raise ValueError(
                        "canonical membership cannot be reassigned"
                    )

                self._connection.execute(
                    """
                    DELETE FROM master_question_memberships
                    WHERE question_id = %s
                    """,
                    (question_id,),
                )
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
                        target_master_id,
                        question_id,
                        relationship.value,
                        confidence,
                    ),
                )
                self._connection.execute(
                    """
                    DELETE FROM master_question_memberships
                    WHERE master_question_id = %s
                      AND question_id = %s
                    """,
                    (source_master_id, question_id),
                )
                self._connection.execute(
                    """
                    INSERT INTO master_repair_events (
                        question_id,
                        source_master_id,
                        target_master_id,
                        previous_relationship,
                        new_relationship,
                        previous_confidence,
                        new_confidence,
                        reason
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        question_id,
                        source_master_id,
                        target_master_id,
                        previous_relationship.value,
                        relationship.value,
                        previous_confidence,
                        confidence,
                        reason.strip(),
                    ),
                )
        except (RepositoryError, ValueError):
            raise
        except Exception as exc:
            raise RepositoryError(
                "failed to reassign master question membership"
            ) from exc

    def _locked_master_statuses(
        self,
        source_master_id: str,
        target_master_id: str,
    ) -> tuple[str, str]:
        rows = self._connection.execute(
            """
            SELECT master_question_id, status
            FROM master_questions
            WHERE master_question_id IN (%s, %s)
            ORDER BY master_question_id
            FOR UPDATE
            """,
            (source_master_id, target_master_id),
        ).fetchall()
        statuses = {str(row[0]): str(row[1]) for row in rows}
        if source_master_id not in statuses:
            raise ValueError(
                f"master question not found: {source_master_id}"
            )
        if target_master_id not in statuses:
            raise ValueError(
                f"master question not found: {target_master_id}"
            )
        return statuses[source_master_id], statuses[target_master_id]

    @staticmethod
    def _require_active_status(master_id: str, status: str) -> None:
        if status != MasterQuestionStatus.ACTIVE.value:
            raise ValueError(f"master question is not active: {master_id}")

    def _fetchall(self, sql: str, params: tuple[object, ...] = ()):
        try:
            return self._connection.execute(sql, params).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to read master questions") from exc

    @staticmethod
    def _master_from_rows(row, options) -> MasterQuestion:
        return MasterQuestion(
            master_question_id=str(row[0]),
            canonical_question_id=str(row[1]),
            stem=str(row[2]),
            kind=QuestionKind(str(row[3])),
            concept_id=None if row[4] is None else str(row[4]),
            status=MasterQuestionStatus(str(row[5])),
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
