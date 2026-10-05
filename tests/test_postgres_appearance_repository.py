from contextlib import contextmanager
from datetime import date, datetime, timezone

from ai_comp.database.postgres_appearance import PostgresAppearanceRepository
from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
)


class FakeResult:
    def __init__(self, row=None, rows=()):
        self.row = row
        self.rows = list(rows)

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    @contextmanager
    def transaction(self):
        yield self

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if self.results:
            return self.results.pop(0)
        return FakeResult()


def verification():
    return SourceVerification(
        verification_id="v1",
        source_id="rssb",
        source_url="https://example.gov/paper.pdf",
        status=VerificationStatus.VERIFIED,
        evidence_type=EvidenceType.OFFICIAL_PAPER,
        checked_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        confidence=1.0,
    )


def appearance(
    appearance_id="a1",
    question_id="q1",
    exam_id="exam-2024",
    question_number=12,
    *,
    source_url="https://example.gov/paper.pdf",
):
    return ExamAppearance(
        appearance_id=appearance_id,
        question_id=question_id,
        exam_id=exam_id,
        conducting_body_id="rssb",
        year=2024,
        exam_date="2024-01-01",
        shift="Shift 1",
        question_number=question_number,
        original_question="राजस्थान का उदाहरण?",
        options=(("A", "एक"), ("B", "दो")),
        correct_answer="A",
        source_url=source_url,
        paper_id="paper-1",
        verification=verification(),
    )


def test_postgres_appearance_repository_inserts_and_records_source_provenance():
    conn = FakeConnection(FakeResult(row=("a1",)))
    repo = PostgresAppearanceRepository(conn)

    repo.save(appearance())

    assert len(conn.calls) == 2
    insert_sql, insert_params = conn.calls[0]
    provenance_sql, provenance_params = conn.calls[1]
    assert "INSERT INTO exam_appearances" in insert_sql
    assert "ON CONFLICT DO NOTHING" in insert_sql
    assert "%s::jsonb" in insert_sql
    assert insert_params[0] == "a1"
    assert "INSERT INTO appearance_sources" in provenance_sql
    assert provenance_params == ("a1", "https://example.gov/paper.pdf", "paper-1", "v1")


def test_postgres_appearance_repository_reuses_canonical_copy_and_only_adds_provenance():
    canonical_row = (
        "canonical-a1",
        "q1",
        "exam-2024",
        "rssb",
        2024,
        date(2024, 1, 1),
        "Shift 1",
        12,
        "राजस्थान का उदाहरण?",
        [["A", "एक"], ["B", "दो"]],
        "A",
        "https://example.gov/paper.pdf",
        "paper-1",
        "EXACT",
        "v1",
        "rssb",
        "https://example.gov/paper.pdf",
        "VERIFIED",
        "OFFICIAL_PAPER",
        datetime(2024, 1, 1, tzinfo=timezone.utc),
        1.0,
        "",
    )
    conn = FakeConnection(
        FakeResult(row=None),
        FakeResult(row=canonical_row),
        FakeResult(),
    )
    repo = PostgresAppearanceRepository(conn)

    copied = appearance(
        appearance_id="copy-a1",
        source_url="https://secondary.example/paper.pdf",
    )
    repo.save(copied)

    assert len(conn.calls) == 3
    assert "SELECT appearance_id" in conn.calls[1][0]
    assert conn.calls[1][1] == ("exam-2024", 2024, "Shift 1", 12)
    assert conn.calls[2][1] == (
        "canonical-a1",
        "https://secondary.example/paper.pdf",
        "paper-1",
        "v1",
    )


def test_postgres_appearance_repository_reads_back_domain_object():
    row = (
        "a1",
        "q1",
        "exam-2024",
        "rssb",
        2024,
        date(2024, 1, 1),
        "Shift 1",
        12,
        "राजस्थान का उदाहरण?",
        [["A", "एक"], ["B", "दो"]],
        "A",
        "https://example.gov/paper.pdf",
        "paper-1",
        "REPHRASED",
        "v1",
        "rssb",
        "https://example.gov/paper.pdf",
        "VERIFIED",
        "OFFICIAL_PAPER",
        datetime(2024, 1, 2, tzinfo=timezone.utc),
        0.99,
        "official paper",
    )
    conn = FakeConnection(FakeResult(rows=[row]))
    repo = PostgresAppearanceRepository(conn)

    result = repo.get_for_question("q1")

    assert len(result) == 1
    loaded = result[0]
    assert loaded.appearance_id == "a1"
    assert loaded.question_id == "q1"
    assert loaded.exam_id == "exam-2024"
    assert loaded.exam_date == "2024-01-01"
    assert loaded.options == (("A", "एक"), ("B", "दो"))
    assert loaded.match_type == "REPHRASED"
    assert loaded.verification.status is VerificationStatus.VERIFIED
    assert loaded.verification.evidence_type is EvidenceType.OFFICIAL_PAPER
