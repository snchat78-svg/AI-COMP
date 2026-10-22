"""Read-only, answer-key-backed historical MCQs eligible for practice.

This is intentionally separate from generated_questions. A source-paper question
is returned only when an official question paper AND its uniquely matched
official answer key are both verified, the resolved answer matches the key, and
the same appearance is already recorded as verified history.
"""
from __future__ import annotations

import json
from typing import Any, Sequence

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
    QuestionSourceKind,
)


class PostgresVerifiedHistoryQuestionRepository:
    """Builds an eligible practice read model from verified exam appearances."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def list_eligible(
        self,
        *,
        limit: int = 5000,
        concept_ids: Sequence[str] | None = None,
        subject_id: str | None = None,
    ) -> tuple[GeneratedMCQ, ...]:
        """Return one representative per active master/exact question identity.

        Historical records are never inserted into the AI-generated question
        table. All trust checks happen in SQL so the test engine sees only rows
        with a linked official paper, linked official answer key, a MATCHED
        paper/key pair, and a resolved answer consistent with the verified key.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10000:
            raise ValueError("limit must be between 1 and 10000")
        scoped_ids = tuple(concept_ids or ())
        if (
            len(set(scoped_ids)) != len(scoped_ids)
            or any(
                not isinstance(item, str) or not item.strip() or item != item.strip()
                for item in scoped_ids
            )
        ):
            raise ValueError("concept_ids must be unique, non-empty, trimmed strings")
        if subject_id is not None and (
            not isinstance(subject_id, str) or not subject_id.strip() or subject_id != subject_id.strip()
        ):
            raise ValueError("subject_id must be a non-empty trimmed string when supplied")

        query = """
            WITH option_sets AS (
                SELECT
                    qo.question_id,
                    jsonb_agg(
                        jsonb_build_object('key', qo.option_key, 'text', qo.option_text)
                        ORDER BY qo.option_order
                    ) AS options,
                    COUNT(*)::INTEGER AS option_count
                FROM question_options AS qo
                GROUP BY qo.question_id
            ),
            eligible AS (
                SELECT
                    CASE
                        WHEN mq.master_question_id IS NOT NULL
                            THEN 'master:' || mq.master_question_id
                        ELSE 'question:' || q.question_id
                    END AS pool_identity,
                    q.question_id,
                    q.stem,
                    options.options,
                    a.correct_answer,
                    e.exam_id,
                    e.name AS exam_name,
                    a.year AS exam_year,
                    a.shift AS exam_shift,
                    a.question_number AS exam_question_number,
                    qv.source_url AS question_source_url,
                    kv.source_url AS answer_key_source_url,
                    array_remove(
                        ARRAY[mq.concept_id]::TEXT[]
                        || COALESCE(qconcepts.concept_ids, ARRAY[]::TEXT[]),
                        NULL
                    ) AS concept_ids,
                    COUNT(*) OVER (
                        PARTITION BY CASE
                            WHEN mq.master_question_id IS NOT NULL
                                THEN 'master:' || mq.master_question_id
                            ELSE 'question:' || q.question_id
                        END
                    )::INTEGER AS verified_appearance_count
                FROM exam_appearances AS a
                JOIN questions AS q
                  ON q.question_id = a.question_id
                 AND q.document_id IS NOT NULL
                JOIN option_sets AS options
                  ON options.question_id = q.question_id
                 AND options.option_count = 4
                JOIN exams AS e
                  ON e.exam_id = a.exam_id
                 AND e.active = TRUE
                JOIN papers AS qp
                  ON qp.paper_id = a.paper_id
                 AND qp.source_id IS NOT NULL
                JOIN sources AS qs
                  ON qs.source_id = qp.source_id
                 AND qs.priority = 'OFFICIAL'
                 AND qs.source_type IN ('OFFICIAL_WEBSITE', 'OFFICIAL_PAPER')
                JOIN source_verifications AS qv
                  ON qv.verification_id = a.verification_id
                 AND qv.source_id = qs.source_id
                 AND qv.status = 'VERIFIED'
                 AND qv.evidence_type = 'OFFICIAL_PAPER'
                JOIN paper_candidates AS qpc
                  ON qpc.candidate_id = qp.candidate_id
                 AND qpc.source_id = qs.source_id
                 AND qpc.status = 'FETCHED'
                JOIN documents AS qdoc
                  ON qdoc.document_id = q.document_id
                 AND qdoc.candidate_id = qpc.candidate_id
                JOIN paper_answer_key_pairs AS pair
                  ON pair.question_paper_id = qp.paper_id
                 AND pair.question_document_id = qdoc.document_id
                 AND pair.exam_id = a.exam_id
                 AND pair.year = a.year
                 AND pair.shift IS NOT DISTINCT FROM a.shift
                 AND pair.pair_status = 'MATCHED'
                JOIN papers AS kp
                  ON kp.paper_id = pair.answer_key_paper_id
                 AND kp.candidate_id = pair.answer_key_candidate_id
                JOIN paper_candidates AS kpc
                  ON kpc.candidate_id = pair.answer_key_candidate_id
                 AND kpc.status = 'FETCHED'
                JOIN sources AS ks
                  ON ks.source_id = kp.source_id
                 AND ks.priority = 'OFFICIAL'
                 AND ks.source_type IN ('OFFICIAL_WEBSITE', 'OFFICIAL_ANSWER_KEY')
                JOIN appearance_sources AS key_appearance_source
                  ON key_appearance_source.appearance_id = a.appearance_id
                 AND key_appearance_source.paper_id = kp.paper_id
                JOIN source_verifications AS kv
                  ON kv.verification_id = key_appearance_source.verification_id
                 AND kv.source_id = ks.source_id
                 AND kv.source_url = key_appearance_source.source_url
                 AND kv.status = 'VERIFIED'
                 AND kv.evidence_type = 'OFFICIAL_ANSWER_KEY'
                JOIN question_answer_records AS resolved
                  ON resolved.question_id = q.question_id
                 AND resolved.document_id = qdoc.document_id
                 AND resolved.source_answer_key_document_id = pair.answer_key_document_id
                 AND resolved.status = 'RESOLVED'
                 AND resolved.selected_option_key = a.correct_answer
                LEFT JOIN master_question_memberships AS membership
                  ON membership.question_id = q.question_id
                LEFT JOIN master_questions AS mq
                  ON mq.master_question_id = membership.master_question_id
                 AND mq.status = 'ACTIVE'
                LEFT JOIN LATERAL (
                    SELECT array_agg(DISTINCT qc.concept_id ORDER BY qc.concept_id) AS concept_ids
                    FROM question_concepts AS qc
                    WHERE qc.question_id = q.question_id
                ) AS qconcepts ON TRUE
                WHERE q.kind = 'MCQ'
                  AND a.correct_answer IS NOT NULL
                  AND a.correct_answer <> ''
                  AND UPPER(a.correct_answer) IN (
                      SELECT UPPER(item ->> 'key')
                      FROM jsonb_array_elements(options.options) AS item
                  )
                  AND qv.source_url = a.source_url
                  AND qv.source_url LIKE 'https://%%'
                  AND kv.source_url LIKE 'https://%%'
                  AND lower(split_part(split_part(qv.source_url, '://', 2), '/', 1))
                      = lower(split_part(split_part(qs.base_url, '://', 2), '/', 1))
                  AND lower(split_part(split_part(kv.source_url, '://', 2), '/', 1))
                      = lower(split_part(split_part(ks.base_url, '://', 2), '/', 1))
                  AND EXISTS (
                      SELECT 1
                      FROM appearance_sources AS paper_appearance_source
                      WHERE paper_appearance_source.appearance_id = a.appearance_id
                        AND paper_appearance_source.paper_id = qp.paper_id
                        AND paper_appearance_source.verification_id = qv.verification_id
                        AND paper_appearance_source.source_url = qv.source_url
                  )
                  AND (
                      %s::TEXT IS NULL OR EXISTS (
                          SELECT 1
                          FROM question_concepts AS subject_question_concept
                          JOIN concepts AS subject_concept
                            ON subject_concept.concept_id = subject_question_concept.concept_id
                          WHERE subject_question_concept.question_id = q.question_id
                            AND lower(btrim(subject_concept.subject)) = lower(%s)
                      )
                  )
            )
            SELECT DISTINCT ON (pool_identity)
                question_id,
                stem,
                options,
                correct_answer,
                exam_id,
                exam_name,
                exam_year,
                exam_shift,
                exam_question_number,
                question_source_url,
                answer_key_source_url,
                concept_ids,
                verified_appearance_count
            FROM eligible
            WHERE cardinality(%s::TEXT[]) = 0
               OR concept_ids && %s::TEXT[]
            ORDER BY pool_identity, exam_year DESC, exam_shift NULLS LAST,
                     exam_question_number, question_id
            LIMIT %s
        """
        try:
            rows = self._connection.execute(
                query,
                (subject_id, subject_id, list(scoped_ids), list(scoped_ids), limit),
            ).fetchall()
            return tuple(self._from_row(row) for row in rows)
        except ValueError:
            raise
        except Exception as exc:
            raise RepositoryError("failed to load verified historical practice questions") from exc

    @classmethod
    def _from_row(cls, row: Sequence[object]) -> GeneratedMCQ:
        (
            question_id,
            stem,
            raw_options,
            correct_answer,
            exam_id,
            exam_name,
            exam_year,
            exam_shift,
            exam_question_number,
            question_source_url,
            answer_key_source_url,
            concept_ids,
            verified_appearance_count,
        ) = row

        options = json.loads(raw_options) if isinstance(raw_options, str) else raw_options
        if not isinstance(options, list):
            raise ValueError("verified historical question options must be a JSON array")
        normalized_options = tuple(
            GeneratedOption(str(item["key"]), str(item["text"]))
            for item in options
        )
        source_answer_key = str(correct_answer)
        matching_option_key = next(
            (
                option.key
                for option in normalized_options
                if option.key.strip().upper() == source_answer_key.strip().upper()
            ),
            None,
        )
        if matching_option_key is None:
            raise ValueError("verified answer key does not match the persisted paper options")
        concept_values = (
            json.loads(concept_ids)
            if isinstance(concept_ids, str)
            else concept_ids
        )
        if not isinstance(concept_values, (list, tuple)):
            concept_values = ()

        paper_url = str(question_source_url)
        key_url = str(answer_key_source_url)
        year = int(exam_year)
        question_number = int(exam_question_number)
        appearances = int(verified_appearance_count)
        evidence = (
            f"Official question paper: {paper_url}",
            f"Official answer key: {key_url}",
            f"Verified exam appearance: {exam_name} {year}, question {question_number}",
        )
        return GeneratedMCQ(
            # A separate namespace prevents collisions with AI-generated IDs.
            generated_question_id=f"verified-history:{question_id}",
            generation_id="verified-exam-history",
            material_id=f"verified-paper:{question_id}",
            stem=str(stem),
            options=normalized_options,
            correct_option_key=matching_option_key,
            explanation=(
                "Answer matched to the linked, official answer key. "
                "Review the original paper and key provenance before relying on this item."
            ),
            fact_ids=(),
            concept_ids=tuple(str(item) for item in concept_values),
            difficulty="MEDIUM",
            importance_score=min(1.0, 0.5 + 0.05 * appearances),
            answer_verification=AnswerVerificationStatus.VERIFIED,
            answer_verification_evidence=evidence,
            status=GeneratedQuestionStatus.ACCEPTED,
            # This is verified source eligibility for practice, not a generated
            # question's model-quality score.
            quality_score=1.0,
            duplicate_of_master_question_id=None,
            source_kind=QuestionSourceKind.VERIFIED_EXAM_HISTORY,
            source_url=paper_url,
            answer_key_source_url=key_url,
            exam_name=str(exam_name),
            exam_id=str(exam_id),
            exam_year=year,
            exam_shift=None if exam_shift is None else str(exam_shift),
            exam_question_number=question_number,
            verified_appearance_count=appearances,
        )


__all__ = ["PostgresVerifiedHistoryQuestionRepository"]
