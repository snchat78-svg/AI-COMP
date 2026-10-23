from __future__ import annotations

from ai_comp.database.postgres_exam_syllabus import PostgresExamSyllabusRepository
from ai_comp.domain.topic_question_bank import QuestionBankTopic


class _Cursor:
    def __init__(self, rows):
        self._rows = list(rows)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _Connection:
    def __init__(self, *results):
        self._results = list(results)
        self.calls = []
        self.closed = False

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if not self._results:
            raise AssertionError("unexpected database query")
        return _Cursor(self._results.pop(0))

    def close(self):
        self.closed = True


def test_pending_syllabus_profile_reports_every_concept_unmapped() -> None:
    connection = _Connection([
        (
            "TEST_EXAM_001",
            "Example recruitment exam",
            "TEST_EXAM_001_ADVT_09_2026",
            "Example test syllabus",
            "https://official.example/test-syllabus.pdf",
            "TEST/001",
            "REVIEW_PENDING",
            False,
            340,
            0,
            0,
            False,
        )
    ])

    profiles = PostgresExamSyllabusRepository(connection).list_profiles()

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile["exam_id"] == "TEST_EXAM_001"
    assert profile["source_status"] == "REVIEW_PENDING"
    assert profile["syllabus_inventory_complete"] is False
    assert profile["concept_count"] == 340
    assert profile["mapped_concept_count"] == 0
    assert profile["excluded_concept_count"] == 0
    assert profile["unmapped_concept_count"] == 340
    assert profile["selection_ready"] is False
    query, params = connection.calls[0]
    assert "exam_syllabus_documents" in query
    assert "applicability_status = 'IN_SCOPE'" in query
    assert "d.source_status = 'VERIFIED'" in query
    assert "d.syllabus_inventory_complete = TRUE" in query
    assert "exam_syllabus_inventory_units" in query
    assert "exam_syllabus_unit_concepts" in query
    assert params == (100,)


def test_profile_is_ready_only_after_inventory_and_all_concepts_are_reviewed() -> None:
    connection = _Connection([
        (
            "TEST_EXAM_001",
            "Example recruitment exam",
            "TEST_EXAM_001_ADVT_09_2026",
            "CET 2026 full official syllabus inventory reviewed",
            "https://official.example/test-syllabus.pdf",
            "TEST/001",
            "VERIFIED",
            True,
            340,
            300,
            40,
            True,
        )
    ])

    profile = PostgresExamSyllabusRepository(connection).list_profiles()[0]

    assert profile["syllabus_inventory_complete"] is True
    assert profile["mapped_concept_count"] == 300
    assert profile["excluded_concept_count"] == 40
    assert profile["unmapped_concept_count"] == 0
    assert profile["selection_ready"] is True


def test_exam_subject_query_requires_verified_in_scope_mappings() -> None:
    connection = _Connection([])

    subjects = PostgresExamSyllabusRepository(connection).list_subjects(
        "TEST_EXAM_001"
    )

    assert subjects == ()
    query, params = connection.calls[0]
    assert "exam_concept_applicability" in query
    assert "d.source_status = 'VERIFIED'" in query
    assert "m.applicability_status = 'IN_SCOPE'" in query
    assert "m.source_locator" in query
    assert "NOT EXISTS" in query
    assert "required_map.applicability_status NOT IN ('IN_SCOPE', 'OUT_OF_SCOPE')" in query
    assert params == ("TEST_EXAM_001", 100)


def test_exam_topic_query_filters_profile_and_preserves_verified_one_liner_count() -> None:
    connection = _Connection([
        (
            "catalog.rajasthan_geography_rivers_and_drainage_luni_river",
            "Luni River",
            "Rajasthan Geography",
            "Rivers and Drainage",
            "Luni River",
            3,
        )
    ])

    topics = PostgresExamSyllabusRepository(connection).list_topics(
        "TEST_EXAM_001",
        "Rajasthan Geography",
        limit=10,
        offset=20,
    )

    assert topics == (
        QuestionBankTopic(
            concept_id="catalog.rajasthan_geography_rivers_and_drainage_luni_river",
            label="Luni River",
            subject="Rajasthan Geography",
            topic="Rivers and Drainage",
            subtopic="Luni River",
            verified_one_liner_count=3,
        ),
    )
    query, params = connection.calls[0]
    assert "d.exam_id = %s" in query
    assert "d.source_status = 'VERIFIED'" in query
    assert "m.applicability_status = 'IN_SCOPE'" in query
    assert "ol.verification_status = 'VERIFIED'" in query
    assert "NOT EXISTS" in query
    assert "required_map.source_evidence" in query
    assert "exam_syllabus_inventory_units" in query
    assert "exam_syllabus_unit_concepts" in query
    assert params == ("TEST_EXAM_001", "Rajasthan Geography", 10, 20)


def test_exam_profile_exists_requires_active_exam_and_current_syllabus() -> None:
    connection = _Connection([(1,)])

    assert PostgresExamSyllabusRepository(connection).profile_exists(
        "TEST_EXAM_001"
    )
    query, params = connection.calls[0]
    assert "d.is_current = TRUE" in query
    assert "e.active = TRUE" in query
    assert params == ("TEST_EXAM_001",)
