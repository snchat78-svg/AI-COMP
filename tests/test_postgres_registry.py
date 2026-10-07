from datetime import datetime, timezone

from ai_comp.database.postgres_registry import PostgresRegistryRepository
from ai_comp.domain.exams import ConductingBody, Exam, ExamLevel, PaperCategory
from ai_comp.domain.sources import SourcePriority, SourceRecord, SourceType
from ai_comp.domain.verification import EvidenceType, SourceVerification, VerificationStatus


class Result:
    def __init__(self, row=None, rows=()):
        self.row = row
        self.rows = list(rows)

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class Connection:
    def __init__(self):
        self.calls = []
        self.results = []

    def transaction(self):
        class Tx:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
        return Tx()

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return self.results.pop(0) if self.results else Result()


def test_registry_repository_writes_authoritative_source_data():
    conn = Connection()
    repo = PostgresRegistryRepository(conn)

    body = ConductingBody(
        body_id="rssb",
        name="RSSB",
        level=ExamLevel.STATE,
        state="RJ",
        official_domains=("rssb.rajasthan.gov.in",),
    )
    exam = Exam(
        exam_id="exam1",
        name="Exam 1",
        conducting_body_id="rssb",
        level=ExamLevel.STATE,
        state="RJ",
    )
    category = PaperCategory(
        category_id="cat1",
        name="General",
        exam_id="exam1",
    )
    source = SourceRecord(
        source_id="src1",
        name="Official",
        base_url="https://rssb.rajasthan.gov.in",
        source_type=SourceType.OFFICIAL_PAPER,
        priority=SourcePriority.OFFICIAL,
        conducting_body_id="rssb",
    )
    verification = SourceVerification(
        verification_id="v1",
        source_id="src1",
        source_url="https://rssb.rajasthan.gov.in/paper.pdf",
        status=VerificationStatus.VERIFIED,
        evidence_type=EvidenceType.OFFICIAL_PAPER,
        checked_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    repo.save_body(body)
    repo.save_exam(exam)
    repo.save_category(category)
    repo.save_source(source)
    repo.save_verification(verification)

    assert "ON CONFLICT (body_id) DO UPDATE" in conn.calls[0][0]
    assert "ON CONFLICT (exam_id) DO UPDATE" in conn.calls[1][0]
    assert "ON CONFLICT (category_id) DO UPDATE" in conn.calls[2][0]
    assert "ON CONFLICT (source_id) DO UPDATE" in conn.calls[3][0]
    assert "ON CONFLICT (verification_id) DO UPDATE" in conn.calls[4][0]
