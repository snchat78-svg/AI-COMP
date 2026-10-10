import json
from collections.abc import Sequence
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)


class PostgresGeneratedQuestionRepository:
    """Durable generated-question storage and eligible-question read model."""

    _SELECT_COLUMNS = """
        generated_question_id, generation_id, material_id, stem, options,
        correct_option_key, explanation, fact_ids, concept_ids, difficulty,
        importance_score, answer_verification_status, answer_verification_evidence,
        status, quality_score, duplicate_of_master_question_id
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, question: GeneratedMCQ) -> None:
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO generated_questions (
                        generated_question_id, generation_id, material_id, stem,
                        options, correct_option_key, explanation, fact_ids,
                        concept_ids, difficulty, importance_score,
                        answer_verification_status, answer_verification_evidence,
                        status, quality_score, duplicate_of_master_question_id
                    )
                    VALUES (
                        %s,%s,%s,%s,%s::jsonb,%s,%s,%s::jsonb,%s::jsonb,%s,%s,
                        %s,%s::jsonb,%s,%s,%s
                    )
                    ON CONFLICT (generated_question_id) DO UPDATE SET
                        answer_verification_status = EXCLUDED.answer_verification_status,
                        answer_verification_evidence = EXCLUDED.answer_verification_evidence,
                        status = EXCLUDED.status,
                        quality_score = EXCLUDED.quality_score,
                        duplicate_of_master_question_id = EXCLUDED.duplicate_of_master_question_id
                    """,
                    (
                        question.generated_question_id,
                        question.generation_id,
                        question.material_id,
                        question.stem,
                        json.dumps(
                            [{"key": o.key, "text": o.text} for o in question.options],
                            ensure_ascii=False,
                        ),
                        question.correct_option_key,
                        question.explanation,
                        json.dumps(list(question.fact_ids), ensure_ascii=False),
                        json.dumps(list(question.concept_ids), ensure_ascii=False),
                        question.difficulty,
                        question.importance_score,
                        question.answer_verification.value,
                        json.dumps(list(question.answer_verification_evidence), ensure_ascii=False),
                        question.status.value,
                        question.quality_score,
                        question.duplicate_of_master_question_id,
                    ),
                )
        except Exception as exc:
            raise RepositoryError("failed to persist generated question") from exc

    def get(self, generated_question_id: str) -> GeneratedMCQ | None:
        try:
            row = self._connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM generated_questions
                WHERE generated_question_id=%s
                """,
                (generated_question_id,),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to read generated question") from exc
        return None if row is None else self._from_row(row)

    def list_accepted(self, *, limit: int = 5000) -> tuple[GeneratedMCQ, ...]:
        """List a bounded pool of accepted, answer-verified, non-duplicate questions."""
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 10000
        ):
            raise ValueError("limit must be between 1 and 10000")
        try:
            rows = self._connection.execute(
                f"""
                SELECT {self._SELECT_COLUMNS}
                FROM generated_questions
                WHERE status = 'ACCEPTED'
                  AND answer_verification_status = 'VERIFIED'
                  AND duplicate_of_master_question_id IS NULL
                ORDER BY importance_score DESC, quality_score DESC,
                         generated_question_id ASC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to list accepted generated questions") from exc
        return tuple(self._from_row(row) for row in rows)

    @staticmethod
    def _json_list(value: object) -> list[Any]:
        result = json.loads(value) if isinstance(value, str) else value
        if not isinstance(result, list):
            raise ValueError("stored generated-question JSON field must be a list")
        return result

    @classmethod
    def _from_row(cls, row: Sequence[object]) -> GeneratedMCQ:
        options = cls._json_list(row[4])
        fact_ids = cls._json_list(row[7])
        concept_ids = cls._json_list(row[8])
        verification_evidence = cls._json_list(row[12])
        return GeneratedMCQ(
            generated_question_id=str(row[0]),
            generation_id=str(row[1]),
            material_id=str(row[2]),
            stem=str(row[3]),
            options=tuple(
                GeneratedOption(str(item["key"]), str(item["text"]))
                for item in options
            ),
            correct_option_key=str(row[5]),
            explanation=str(row[6]),
            fact_ids=tuple(str(item) for item in fact_ids),
            concept_ids=tuple(str(item) for item in concept_ids),
            difficulty=str(row[9]),
            importance_score=float(row[10]),
            answer_verification=AnswerVerificationStatus(str(row[11])),
            answer_verification_evidence=tuple(str(item) for item in verification_evidence),
            status=GeneratedQuestionStatus(str(row[13])),
            quality_score=float(row[14]),
            duplicate_of_master_question_id=(
                None if row[15] is None else str(row[15])
            ),
        )


__all__ = ["PostgresGeneratedQuestionRepository"]
