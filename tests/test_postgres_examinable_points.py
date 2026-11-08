from __future__ import annotations

from ai_comp.database.postgres_examinable_points import PostgresExaminablePointRepository


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class _Connection:
    def __init__(self, *, source=None, summary=None, details=()):
        self.source = source
        self.summary = summary
        self.details = list(details)
        self.calls = []
        self.closed = False

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if "FROM exam_syllabus_documents" in query:
            return _Cursor([] if self.source is None else [self.source])
        if "AS total_points" in query:
            return _Cursor([self.summary])
        if "SELECT point_id, unit_id" in query:
            return _Cursor(self.details)
        raise AssertionError(f"unexpected SQL: {query}")

    def close(self):
        self.closed = True


def test_incomplete_inventory_never_emits_coverage_percentage():
    connection = _Connection(
        source=("TEST_EXAM", "REVIEW_PENDING", False, False, None, None, ""),
        summary=(3, 1, 0, 2, 2, 2, 2, 0, 0, 1),
        details=(
            ("point-1", "unit-1", "FACT", "Synthetic point", 2, "p. 2", "NEEDS_REVIEW",
             "NEEDS_REVIEW", "author", None, 1, 0, 4, 1, 0, 1),
        ),
    )

    report = PostgresExaminablePointRepository(connection).get_gap_report("test-syllabus")

    assert report is not None
    assert report["coverage_status"] == "COVERAGE_UNKNOWN_INVENTORY_INCOMPLETE"
    assert report["coverage_label"] == "COVERAGE UNKNOWN — INVENTORY INCOMPLETE"
    assert report["coverage_percentage"] is None
    assert report["summary"]["total_points"] == 3
    assert report["summary"]["mapping_gap_points"] == 2
    assert report["summary"]["points_with_missing_dimensions"] == 2
    assert report["summary"]["points_without_verified_learning_items"] == 2
    assert report["summary"]["verified_history_question_count"] is None
    assert report["summary"]["historical_question_linking"] == "NOT_IMPLEMENTED"
    assert len(report["items"]) == 1
    assert report["items"][0]["point_id"] == "point-1"

    report_sql = connection.calls[1][0]
    assert "link.review_status = 'VERIFIED'" in report_sql
    assert "one_liner.verification_status = 'VERIFIED'" in report_sql
    assert "COUNT(DISTINCT one_liner.content_hash)" in report_sql
    assert "mapping_status <> 'MAPPED'" in report_sql
    assert connection.calls[0][1] == ("test-syllabus",)


def test_complete_inventory_reports_only_verified_point_coverage():
    connection = _Connection(
        source=("TEST_EXAM", "VERIFIED", True, True, None, "independent-reviewer", "All points reconciled"),
        summary=(4, 0, 0, 1, 1, 1, 4, 2, 5, 0),
        details=(),
    )

    report = PostgresExaminablePointRepository(connection).get_gap_report(
        "test-syllabus", limit=25, offset=50
    )

    assert report is not None
    assert report["coverage_status"] == "READY_FOR_COVERAGE_PERCENTAGE"
    assert report["coverage_percentage"] == 50.0
    assert report["summary"]["reviewed_in_scope_points"] == 4
    assert report["summary"]["fully_covered_points"] == 2
    assert report["summary"]["verified_one_liner_count"] == 5
    assert connection.calls[2][1] == ("test-syllabus", 25, 50)


def test_zero_reviewed_point_denominator_does_not_divide_or_claim_coverage():
    connection = _Connection(
        source=("TEST_EXAM", "VERIFIED", True, True, None, "reviewer", "No points reviewed"),
        summary=(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    )

    report = PostgresExaminablePointRepository(connection).get_gap_report("test-syllabus")

    assert report is not None
    assert report["coverage_percentage"] is None
    assert report["coverage_status"] == "COVERAGE_UNKNOWN_INVENTORY_INCOMPLETE"


def test_missing_syllabus_returns_none_without_running_point_queries():
    connection = _Connection()

    assert PostgresExaminablePointRepository(connection).get_gap_report("missing") is None
    assert len(connection.calls) == 1


def test_gap_report_validates_syllabus_and_page_bounds_before_database_access():
    connection = _Connection()
    repository = PostgresExaminablePointRepository(connection)

    for kwargs in (
        {"syllabus_id": " padded "},
        {"syllabus_id": "test", "limit": 0},
        {"syllabus_id": "test", "limit": 101},
        {"syllabus_id": "test", "offset": -1},
        {"syllabus_id": "test", "offset": 100001},
    ):
        try:
            repository.get_gap_report(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid report arguments were accepted: {kwargs}")
    assert connection.calls == []
