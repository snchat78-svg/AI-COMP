import pytest

from ai_comp.database.postgres_appearance import PostgresAppearanceRepository
from ai_comp.database.repository import RepositoryError
from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
)
from datetime import datetime, timezone


class Result:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class Connection:
    def __init__(self):
        self.calls = []

    def transaction(self):
        class Tx:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
        return Tx()

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return Result()


def verification():
    return SourceVerification(
        verification_id="v1",
        source_id="src1",
        source_url="https://example.gov/paper.pdf",
        status=VerificationStatus.VERIFIED,
        evidence_type=EvidenceType.OFFICIAL_PAPER,
        checked_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


def appearance(source_url="https://example.gov/paper.pdf"):
    return ExamAppearance(
        appearance_id="a1",
        question_id="q1",
        exam_id="exam1",
        conducting_body_id="rssb",
        year=2024,
        exam_date="2024-01-01",
        shift="Shift 1",
        question_number=1,
        original_question="Example?",
        options=(("A", "one"), ("B", "two")),
        correct_answer="A",
        source_url=source_url,
        paper_id="paper1",
        verification=verification(),
        match_type="EXACT",
    )


def test_appearance_repository_allows_identical_replay():
    connection = Connection()
    repository = PostgresAppearanceRepository(connection)
    existing = appearance()
    repository._find_by_appearance_id = lambda _: existing

    repository.save(existing)

    assert len(connection.calls) == 2
    assert "INSERT INTO appearance_sources" in connection.calls[1][0]


def test_appearance_repository_rejects_reused_id_with_different_data():
    connection = Connection()
    repository = PostgresAppearanceRepository(connection)
    repository._find_by_appearance_id = lambda _: appearance()

    with pytest.raises(RepositoryError, match="appearance_id already exists"):
        repository.save(
            appearance(source_url="https://secondary.example/copy.pdf")
        )

    assert len(connection.calls) == 1
    assert "INSERT INTO appearance_sources" not in connection.calls[0][0]
