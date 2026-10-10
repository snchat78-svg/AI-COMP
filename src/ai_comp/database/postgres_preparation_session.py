from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Sequence

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)
from ai_comp.domain.test_engine import (
    ScoringPolicy,
    TestAnswer,
    TestResult,
    TestSession,
    TestSessionStatus,
    TestSpecification,
)


class PostgresPreparationTestSessionRepository:
    """Durable TestEngine repository scoped to one authenticated learner.

    New rows snapshot the selected question set and immutable test specification.
    Later requests reconstruct the same questions/settings before resuming the timer,
    answering, navigating, or submitting; they do not silently rerank the test.
    """

    def __init__(
        self,
        connection_factory,
        *,
        learner_id: str,
        preparation_request_id: str | None = None,
        specification: TestSpecification | None = None,
        questions: Sequence[GeneratedMCQ] = (),
        new_session_id: str | None = None,
    ) -> None:
        if not learner_id.strip():
            raise ValueError("learner_id is required")
        self._connection_factory = connection_factory
        self.learner_id = learner_id
        self._preparation_request_id = preparation_request_id
        self._specification = specification
        self._questions = tuple(questions)
        self._new_session_id = new_session_id
        if new_session_id is not None:
            if not preparation_request_id or specification is None:
                raise ValueError("new sessions require a preparation request and specification")
            if not self._questions:
                raise ValueError("new sessions require question snapshots")
            if any(q.status is not GeneratedQuestionStatus.ACCEPTED for q in self._questions):
                raise ValueError("only accepted questions can be snapshotted")

    def _run(self, operation):
        connection = self._connection_factory()
        try:
            return operation(connection)
        finally:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

    def save(self, session: TestSession) -> None:
        if self._new_session_id is not None:
            if session.session_id != self._new_session_id:
                raise RepositoryError("session ID does not match the requested new session")
            if session.test_id != self._specification.test_id:
                raise RepositoryError("session test ID does not match saved specification")
            spec_json = json.dumps(self._specification_payload(self._specification), ensure_ascii=False)
            questions_json = json.dumps(
                [self._question_payload(question) for question in self._questions],
                ensure_ascii=False,
            )
            state_json = json.dumps(self._session_payload(session), ensure_ascii=False)
            now = datetime.now(timezone.utc)

            def insert(connection):
                with connection.transaction():
                    row = connection.execute(
                        """
                        SELECT status FROM preparation_test_requests
                        WHERE request_id = %s AND learner_id = %s
                        FOR UPDATE
                        """,
                        (self._preparation_request_id, self.learner_id),
                    ).fetchone()
                    if row is None or str(row[0]) != "ACTIVE":
                        raise RepositoryError("saved preparation request is not active")
                    connection.execute(
                        """
                        INSERT INTO preparation_test_sessions (
                            session_id, learner_id, preparation_request_id, test_id,
                            specification, question_snapshot, session_state,
                            session_status, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s)
                        """,
                        (
                            session.session_id, self.learner_id, self._preparation_request_id,
                            session.test_id, spec_json, questions_json, state_json,
                            session.status.value, now, now,
                        ),
                    )
            try:
                self._run(insert)
                self._new_session_id = None
                return
            except RepositoryError:
                raise
            except Exception as exc:
                raise RepositoryError("failed to create preparation test session") from exc

        state_json = json.dumps(self._session_payload(session), ensure_ascii=False)
        now = datetime.now(timezone.utc)

        def update(connection):
            with connection.transaction():
                row = connection.execute(
                    """
                    UPDATE preparation_test_sessions
                    SET session_state = %s::jsonb, session_status = %s, updated_at = %s
                    WHERE learner_id = %s AND session_id = %s
                    RETURNING session_id
                    """,
                    (state_json, session.status.value, now, self.learner_id, session.session_id),
                ).fetchone()
                if row is None:
                    raise KeyError(f"test session not found: {session.session_id}")
        try:
            self._run(update)
        except (KeyError, RepositoryError):
            raise
        except Exception as exc:
            raise RepositoryError("failed to persist test session state") from exc

    def get(self, session_id: str) -> TestSession:
        if not session_id.strip():
            raise ValueError("session_id is required")
        def query(connection):
            return connection.execute(
                """
                SELECT session_state FROM preparation_test_sessions
                WHERE learner_id = %s AND session_id = %s
                """,
                (self.learner_id, session_id),
            ).fetchone()
        try:
            row = self._run(query)
        except Exception as exc:
            raise RepositoryError("failed to load test session") from exc
        if row is None:
            raise KeyError(f"test session not found: {session_id}")
        return self._session_from_payload(self._json_object(row[0]))

    def get_record_for_learner(self, session_id: str) -> dict[str, Any] | None:
        if not session_id.strip():
            raise ValueError("session_id is required")
        def query(connection):
            return connection.execute(
                """
                SELECT session_id, learner_id, preparation_request_id, test_id,
                       specification, question_snapshot, session_state, created_at, updated_at
                FROM preparation_test_sessions
                WHERE learner_id = %s AND session_id = %s
                """,
                (self.learner_id, session_id),
            ).fetchone()
        try:
            row = self._run(query)
        except Exception as exc:
            raise RepositoryError("failed to load persisted test session") from exc
        if row is None:
            return None
        return {
            "session_id": str(row[0]),
            "learner_id": str(row[1]),
            "preparation_request_id": str(row[2]),
            "test_id": str(row[3]),
            "specification": self._specification_from_payload(self._json_object(row[4])),
            "questions": tuple(self._question_from_payload(item) for item in self._json_list(row[5])),
            "session": self._session_from_payload(self._json_object(row[6])),
            "created_at": row[7],
            "updated_at": row[8],
        }


    def list_for_learner(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: TestSessionStatus | None = None,
        results_only: bool = False,
    ) -> tuple[dict[str, Any], ...]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 101:
            raise ValueError("limit must be between 1 and 101")
        if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 100000:
            raise ValueError("offset must be between 0 and 100000")
        if status is not None and not isinstance(status, TestSessionStatus):
            raise ValueError("status must be a TestSessionStatus")
        query = """
            SELECT s.session_id, s.preparation_request_id, s.test_id,
                   s.specification, s.session_state, s.session_status,
                   s.created_at, s.updated_at, r.mode
            FROM preparation_test_sessions AS s
            JOIN preparation_test_requests AS r
              ON r.request_id = s.preparation_request_id
             AND r.learner_id = s.learner_id
            WHERE s.learner_id = %s
        """
        parameters: list[object] = [self.learner_id]
        if status is not None:
            query += " AND s.session_status = %s"
            parameters.append(status.value)
        if results_only:
            query += """
                AND s.session_status IN ('SUBMITTED', 'EXPIRED')
                AND s.session_state -> 'result' IS NOT NULL
                AND s.session_state -> 'result' <> 'null'::jsonb
            """
        query += " ORDER BY s.created_at DESC, s.session_id DESC LIMIT %s OFFSET %s"
        parameters.extend((limit, offset))
        def read(connection):
            return connection.execute(query, tuple(parameters)).fetchall()
        try:
            rows = self._run(read)
        except Exception as exc:
            raise RepositoryError("failed to list learner preparation sessions") from exc
        return tuple(
            {
                "session_id": str(row[0]),
                "preparation_request_id": str(row[1]),
                "test_id": str(row[2]),
                "specification": self._specification_from_payload(self._json_object(row[3])),
                "session": self._session_from_payload(self._json_object(row[4])),
                "status": TestSessionStatus(str(row[5])),
                "created_at": row[6],
                "updated_at": row[7],
                "mode": str(row[8]),
            }
            for row in rows
        )

    def get_history_summary(self) -> dict[str, int | float]:
        completed = """
            session_status IN ('SUBMITTED', 'EXPIRED')
            AND session_state -> 'result' IS NOT NULL
            AND session_state -> 'result' <> 'null'::jsonb
        """
        query = f"""
            SELECT
                COUNT(*)::BIGINT,
                COUNT(*) FILTER (WHERE {completed})::BIGINT,
                COALESCE(AVG(
                    NULLIF(session_state -> 'result' ->> 'percentage', '')::DOUBLE PRECISION
                ) FILTER (WHERE {completed}), 0.0),
                COALESCE(MAX(
                    NULLIF(session_state -> 'result' ->> 'percentage', '')::DOUBLE PRECISION
                ) FILTER (WHERE {completed}), 0.0),
                COALESCE(SUM(
                    NULLIF(session_state -> 'result' ->> 'total_questions', '')::BIGINT
                ) FILTER (WHERE {completed}), 0)::BIGINT,
                COALESCE(SUM(
                    NULLIF(session_state -> 'result' ->> 'attempted_questions', '')::BIGINT
                ) FILTER (WHERE {completed}), 0)::BIGINT,
                COALESCE(SUM(
                    NULLIF(session_state -> 'result' ->> 'correct_answers', '')::BIGINT
                ) FILTER (WHERE {completed}), 0)::BIGINT,
                COALESCE(SUM(
                    NULLIF(session_state -> 'result' ->> 'incorrect_answers', '')::BIGINT
                ) FILTER (WHERE {completed}), 0)::BIGINT,
                COALESCE(SUM(
                    NULLIF(session_state -> 'result' ->> 'unattempted_questions', '')::BIGINT
                ) FILTER (WHERE {completed}), 0)::BIGINT
            FROM preparation_test_sessions
            WHERE learner_id = %s
        """
        def read(connection):
            return connection.execute(query, (self.learner_id,)).fetchone()
        try:
            row = self._run(read)
        except Exception as exc:
            raise RepositoryError("failed to aggregate learner preparation results") from exc
        if row is None:
            raise RepositoryError("failed to aggregate learner preparation results")
        return {
            "total_session_count": int(row[0]),
            "completed_test_count": int(row[1]),
            "average_percentage": float(row[2]),
            "best_percentage": float(row[3]),
            "total_questions": int(row[4]),
            "attempted_questions": int(row[5]),
            "correct_answers": int(row[6]),
            "incorrect_answers": int(row[7]),
            "unattempted_questions": int(row[8]),
        }

    @staticmethod
    def _json_object(value: object) -> dict[str, Any]:
        result = json.loads(value) if isinstance(value, str) else value
        if not isinstance(result, dict):
            raise ValueError("persisted JSON object expected")
        return result

    @staticmethod
    def _json_list(value: object) -> list[Any]:
        result = json.loads(value) if isinstance(value, str) else value
        if not isinstance(result, list):
            raise ValueError("persisted JSON array expected")
        return result

    @staticmethod
    def _specification_payload(spec: TestSpecification) -> dict[str, Any]:
        return {
            "test_id": spec.test_id, "title": spec.title,
            "question_count": spec.question_count, "duration_seconds": spec.duration_seconds,
            "scoring": {
                "correct_marks": spec.scoring.correct_marks,
                "incorrect_marks": spec.scoring.incorrect_marks,
                "unattempted_marks": spec.scoring.unattempted_marks,
            },
            "shuffle_questions": spec.shuffle_questions, "shuffle_seed": spec.shuffle_seed,
        }

    @staticmethod
    def _specification_from_payload(payload: dict[str, Any]) -> TestSpecification:
        scoring = payload["scoring"]
        return TestSpecification(
            test_id=str(payload["test_id"]), title=str(payload["title"]),
            question_count=int(payload["question_count"]),
            duration_seconds=int(payload["duration_seconds"]),
            scoring=ScoringPolicy(
                correct_marks=float(scoring["correct_marks"]),
                incorrect_marks=float(scoring["incorrect_marks"]),
                unattempted_marks=float(scoring["unattempted_marks"]),
            ),
            shuffle_questions=bool(payload["shuffle_questions"]),
            shuffle_seed=None if payload["shuffle_seed"] is None else int(payload["shuffle_seed"]),
        )

    @staticmethod
    def _question_payload(question: GeneratedMCQ) -> dict[str, Any]:
        return {
            "generated_question_id": question.generated_question_id,
            "generation_id": question.generation_id,
            "material_id": question.material_id,
            "stem": question.stem,
            "options": [{"key": option.key, "text": option.text} for option in question.options],
            "correct_option_key": question.correct_option_key,
            "explanation": question.explanation,
            "fact_ids": list(question.fact_ids),
            "concept_ids": list(question.concept_ids),
            "difficulty": question.difficulty,
            "importance_score": question.importance_score,
            "answer_verification": question.answer_verification.value,
            "answer_verification_evidence": list(question.answer_verification_evidence),
            "status": question.status.value,
            "quality_score": question.quality_score,
            "duplicate_of_master_question_id": question.duplicate_of_master_question_id,
        }

    @classmethod
    def _question_from_payload(cls, payload: dict[str, Any]) -> GeneratedMCQ:
        return GeneratedMCQ(
            generated_question_id=str(payload["generated_question_id"]),
            generation_id=str(payload["generation_id"]),
            material_id=str(payload["material_id"]),
            stem=str(payload["stem"]),
            options=tuple(GeneratedOption(str(item["key"]), str(item["text"])) for item in payload["options"]),
            correct_option_key=str(payload["correct_option_key"]),
            explanation=str(payload["explanation"]),
            fact_ids=tuple(str(item) for item in payload["fact_ids"]),
            concept_ids=tuple(str(item) for item in payload["concept_ids"]),
            difficulty=str(payload["difficulty"]),
            importance_score=float(payload["importance_score"]),
            answer_verification=AnswerVerificationStatus(str(payload["answer_verification"])),
            answer_verification_evidence=tuple(str(item) for item in payload["answer_verification_evidence"]),
            status=GeneratedQuestionStatus(str(payload["status"])),
            quality_score=float(payload["quality_score"]),
            duplicate_of_master_question_id=(
                None if payload["duplicate_of_master_question_id"] is None
                else str(payload["duplicate_of_master_question_id"])
            ),
        )

    @staticmethod
    def _session_payload(session: TestSession) -> dict[str, Any]:
        result = None
        if session.result is not None:
            result = {
                "test_id": session.result.test_id, "session_id": session.result.session_id,
                "status": session.result.status.value,
                "total_questions": session.result.total_questions,
                "attempted_questions": session.result.attempted_questions,
                "correct_answers": session.result.correct_answers,
                "incorrect_answers": session.result.incorrect_answers,
                "unattempted_questions": session.result.unattempted_questions,
                "raw_score": session.result.raw_score, "max_score": session.result.max_score,
                "percentage": session.result.percentage, "accuracy": session.result.accuracy,
                "timed_out": session.result.timed_out,
            }
        return {
            "session_id": session.session_id, "test_id": session.test_id,
            "question_ids": list(session.question_ids), "current_index": session.current_index,
            "answers": [{
                "question_id": answer.question_id,
                "selected_option_key": answer.selected_option_key,
                "answered_at_seconds": answer.answered_at_seconds,
            } for answer in session.answers],
            "review_question_ids": list(session.review_question_ids),
            "status": session.status.value, "started_at": session.started_at,
            "deadline_at": session.deadline_at, "submitted_at": session.submitted_at,
            "result": result,
        }

    @staticmethod
    def _session_from_payload(payload: dict[str, Any]) -> TestSession:
        result_payload = payload.get("result")
        result = None
        if result_payload is not None:
            result = TestResult(
                test_id=str(result_payload["test_id"]),
                session_id=str(result_payload["session_id"]),
                status=TestSessionStatus(str(result_payload["status"])),
                total_questions=int(result_payload["total_questions"]),
                attempted_questions=int(result_payload["attempted_questions"]),
                correct_answers=int(result_payload["correct_answers"]),
                incorrect_answers=int(result_payload["incorrect_answers"]),
                unattempted_questions=int(result_payload["unattempted_questions"]),
                raw_score=float(result_payload["raw_score"]),
                max_score=float(result_payload["max_score"]),
                percentage=float(result_payload["percentage"]),
                accuracy=float(result_payload["accuracy"]),
                timed_out=bool(result_payload["timed_out"]),
            )
        return TestSession(
            session_id=str(payload["session_id"]), test_id=str(payload["test_id"]),
            question_ids=tuple(str(item) for item in payload["question_ids"]),
            current_index=int(payload["current_index"]),
            answers=tuple(TestAnswer(
                question_id=str(item["question_id"]),
                selected_option_key=str(item["selected_option_key"]),
                answered_at_seconds=float(item["answered_at_seconds"]),
            ) for item in payload["answers"]),
            review_question_ids=tuple(str(item) for item in payload["review_question_ids"]),
            status=TestSessionStatus(str(payload["status"])),
            started_at=None if payload["started_at"] is None else float(payload["started_at"]),
            deadline_at=None if payload["deadline_at"] is None else float(payload["deadline_at"]),
            submitted_at=None if payload["submitted_at"] is None else float(payload["submitted_at"]),
            result=result,
        )


__all__ = ["PostgresPreparationTestSessionRepository"]
