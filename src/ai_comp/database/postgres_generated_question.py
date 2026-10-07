import json
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)


class PostgresGeneratedQuestionRepository:
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
                """
                SELECT generated_question_id,generation_id,material_id,stem,options,
                       correct_option_key,explanation,fact_ids,concept_ids,difficulty,
                       importance_score,answer_verification_status,
                       answer_verification_evidence,status,quality_score,
                       duplicate_of_master_question_id
                FROM generated_questions
                WHERE generated_question_id=%s
                """,
                (generated_question_id,),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to read generated question") from exc
        if row is None:
            return None
        return GeneratedMCQ(
            generated_question_id=str(row[0]),
            generation_id=str(row[1]),
            material_id=str(row[2]),
            stem=str(row[3]),
            options=tuple(GeneratedOption(str(x["key"]), str(x["text"])) for x in (row[4] if isinstance(row[4], list) else json.loads(row[4]))),
            correct_option_key=str(row[5]),
            explanation=str(row[6]),
            fact_ids=tuple(row[7] if isinstance(row[7], list) else json.loads(row[7])),
            concept_ids=tuple(row[8] if isinstance(row[8], list) else json.loads(row[8])),
            difficulty=str(row[9]),
            importance_score=float(row[10]),
            answer_verification=AnswerVerificationStatus(str(row[11])),
            answer_verification_evidence=tuple(row[12] if isinstance(row[12], list) else json.loads(row[12])),
            status=GeneratedQuestionStatus(str(row[13])),
            quality_score=float(row[14]),
            duplicate_of_master_question_id=row[15],
        )
