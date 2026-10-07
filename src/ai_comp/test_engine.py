from __future__ import annotations

import random
import time
from collections.abc import Callable, Sequence
from dataclasses import replace

from ai_comp.domain.material_generation import GeneratedMCQ, GeneratedQuestionStatus
from ai_comp.domain.question_intelligence import RankedQuestionCandidate
from ai_comp.domain.test_engine import (
    InMemoryTestSessionRepository,
    TestAnswer,
    TestResult,
    TestSession,
    TestSessionRepository,
    TestSessionStatus,
    TestSpecification,
)


class TestEngine:
    """Timed MCQ engine consuming only ranked, accepted generated questions."""

    def __init__(
        self,
        *,
        repository: TestSessionRepository | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.repository = repository or InMemoryTestSessionRepository()
        self.clock = clock or time.monotonic
        self._questions: dict[str, GeneratedMCQ] = {}
        self._specifications: dict[str, TestSpecification] = {}

    def create_session(
        self,
        specification: TestSpecification,
        candidates: Sequence[RankedQuestionCandidate],
        questions: Sequence[GeneratedMCQ],
        *,
        session_id: str,
    ) -> TestSession:
        try:
            self.repository.get(session_id)
        except KeyError:
            pass
        else:
            raise ValueError(f"test session already exists: {session_id}")

        questions_by_id: dict[str, GeneratedMCQ] = {}
        for question in questions:
            if question.status is not GeneratedQuestionStatus.ACCEPTED:
                raise ValueError("test engine accepts only accepted generated questions")
            if question.generated_question_id in questions_by_id:
                raise ValueError("duplicate generated question ID")
            questions_by_id[question.generated_question_id] = question

        candidate_ids = [candidate.question_id for candidate in candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("ranked candidates must have unique question IDs")
        if any(candidate.rank < 1 for candidate in candidates):
            raise ValueError("ranked candidate rank must be positive")
        if any(question_id not in questions_by_id for question_id in candidate_ids):
            raise ValueError("every ranked candidate must reference an accepted question")

        ordered = sorted(
            candidates,
            key=lambda candidate: (
                candidate.rank,
                -candidate.score.selection_score,
                question_id_for(candidate),
            ),
        )
        selected = list(ordered[: specification.question_count])
        if len(selected) < specification.question_count:
            raise ValueError("not enough accepted ranked questions for the test")

        question_ids = [candidate.question_id for candidate in selected]
        if specification.shuffle_questions:
            random.Random(specification.shuffle_seed).shuffle(question_ids)

        session = TestSession(
            session_id=session_id,
            test_id=specification.test_id,
            question_ids=tuple(question_ids),
            current_index=0,
            answers=(),
            review_question_ids=(),
            status=TestSessionStatus.CREATED,
            started_at=None,
            deadline_at=None,
            submitted_at=None,
        )
        self._questions.update(questions_by_id)
        self._specifications[specification.test_id] = specification
        self.repository.save(session)
        return session

    def start(self, session_id: str) -> TestSession:
        session = self.repository.get(session_id)
        if session.status is not TestSessionStatus.CREATED:
            raise ValueError("only a created test session can be started")
        now = self.clock()
        started = replace(
            session,
            status=TestSessionStatus.IN_PROGRESS,
            started_at=now,
            deadline_at=now + self._spec(session).duration_seconds,
        )
        self.repository.save(started)
        return started

    def get_session(self, session_id: str) -> TestSession:
        return self._refresh_expiry(self.repository.get(session_id))

    def remaining_seconds(self, session_id: str) -> float:
        session = self._refresh_expiry(self.repository.get(session_id))
        if session.status is not TestSessionStatus.IN_PROGRESS:
            return 0.0
        return max(0.0, (session.deadline_at or 0.0) - self.clock())

    def current_question(self, session_id: str) -> GeneratedMCQ:
        session = self._refresh_expiry(self.repository.get(session_id))
        self._require_in_progress(session)
        return self._questions[session.question_ids[session.current_index]]

    def answer(self, session_id: str, option_key: str) -> TestSession:
        session = self._refresh_expiry(self.repository.get(session_id))
        self._require_in_progress(session)
        question_id = session.question_ids[session.current_index]
        question = self._questions[question_id]
        key = option_key.strip().upper()
        valid_keys = {option.key.strip().upper() for option in question.options}
        if key not in valid_keys:
            raise ValueError("selected option is not valid for the current question")

        elapsed = max(0.0, self.clock() - (session.started_at or self.clock()))
        new_answer = TestAnswer(question_id, key, elapsed)
        answers = tuple(
            answer for answer in session.answers if answer.question_id != question_id
        ) + (new_answer,)
        updated = replace(session, answers=answers)
        self.repository.save(updated)
        return updated

    def next(self, session_id: str) -> TestSession:
        return self._move(session_id, +1)

    def previous(self, session_id: str) -> TestSession:
        return self._move(session_id, -1)

    def goto(self, session_id: str, question_number: int) -> TestSession:
        session = self._refresh_expiry(self.repository.get(session_id))
        self._require_in_progress(session)
        if not 1 <= question_number <= len(session.question_ids):
            raise ValueError("question number is out of range")
        updated = replace(session, current_index=question_number - 1)
        self.repository.save(updated)
        return updated

    def toggle_review(self, session_id: str) -> TestSession:
        session = self._refresh_expiry(self.repository.get(session_id))
        self._require_in_progress(session)
        question_id = session.question_ids[session.current_index]
        reviews = set(session.review_question_ids)
        if question_id in reviews:
            reviews.remove(question_id)
        else:
            reviews.add(question_id)
        updated = replace(
            session,
            review_question_ids=tuple(
                question_id
                for question_id in session.question_ids
                if question_id in reviews
            ),
        )
        self.repository.save(updated)
        return updated

    def submit(self, session_id: str) -> TestResult:
        session = self._refresh_expiry(self.repository.get(session_id))
        if session.result is not None:
            return session.result
        if session.status is not TestSessionStatus.IN_PROGRESS:
            raise ValueError("only an active test session can be submitted")

        now = self.clock()
        result = self._build_result(session, timed_out=False)
        final = replace(
            session,
            status=TestSessionStatus.SUBMITTED,
            submitted_at=now,
            result=result,
        )
        self.repository.save(final)
        return result

    def _move(self, session_id: str, delta: int) -> TestSession:
        session = self._refresh_expiry(self.repository.get(session_id))
        self._require_in_progress(session)
        new_index = session.current_index + delta
        if not 0 <= new_index < len(session.question_ids):
            raise ValueError("cannot move beyond test boundaries")
        updated = replace(session, current_index=new_index)
        self.repository.save(updated)
        return updated

    def _refresh_expiry(self, session: TestSession) -> TestSession:
        if (
            session.status is TestSessionStatus.IN_PROGRESS
            and session.deadline_at is not None
            and self.clock() >= session.deadline_at
        ):
            now = self.clock()
            result = self._build_result(session, timed_out=True)
            expired = replace(
                session,
                status=TestSessionStatus.EXPIRED,
                submitted_at=now,
                result=result,
            )
            self.repository.save(expired)
            return expired
        return session

    def _build_result(self, session: TestSession, *, timed_out: bool) -> TestResult:
        specification = self._spec(session)
        answer_by_id = {answer.question_id: answer for answer in session.answers}
        correct = incorrect = unattempted = 0
        raw_score = 0.0

        for question_id in session.question_ids:
            answer = answer_by_id.get(question_id)
            if answer is None:
                unattempted += 1
                raw_score += specification.scoring.unattempted_marks
                continue
            question = self._questions[question_id]
            if answer.selected_option_key == question.correct_option_key.strip().upper():
                correct += 1
                raw_score += specification.scoring.correct_marks
            else:
                incorrect += 1
                raw_score += specification.scoring.incorrect_marks

        total = len(session.question_ids)
        max_score = total * specification.scoring.correct_marks
        percentage = (raw_score / max_score) * 100.0
        accuracy = (correct / (correct + incorrect)) if (correct + incorrect) else 0.0
        return TestResult(
            test_id=session.test_id,
            session_id=session.session_id,
            status=TestSessionStatus.EXPIRED if timed_out else TestSessionStatus.SUBMITTED,
            total_questions=total,
            attempted_questions=correct + incorrect,
            correct_answers=correct,
            incorrect_answers=incorrect,
            unattempted_questions=unattempted,
            raw_score=raw_score,
            max_score=max_score,
            percentage=percentage,
            accuracy=accuracy,
            timed_out=timed_out,
        )

    def _spec(self, session: TestSession) -> TestSpecification:
        try:
            return self._specifications[session.test_id]
        except KeyError as exc:
            raise KeyError(f"test specification not loaded: {session.test_id}") from exc

    @staticmethod
    def _require_in_progress(session: TestSession) -> None:
        if session.status is not TestSessionStatus.IN_PROGRESS:
            raise ValueError("test session is not in progress")


def question_id_for(candidate: RankedQuestionCandidate) -> str:
    return candidate.question_id
