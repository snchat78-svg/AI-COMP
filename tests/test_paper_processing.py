from hashlib import sha256

from ai_comp.domain.sources import CrawlPolicy
from ai_comp.research.paper import DocumentFormat
from ai_comp.research.policy import ResearchPolicyError
from ai_comp.research.paper_processing import process_pending_candidates
from ai_comp.research.safe_downloader import DownloadedPaper
from ai_comp.research.supabase_storage import StoredObject


CANDIDATE_ROW = (
    "RSSB_OFFICIAL:live:example",
    "RSSB_OFFICIAL",
    "https://rssb.rajasthan.gov.in/storage/questionpaper_item/paper.txt",
    "Rajasthan CET Sample Paper 2024",
    "text",
    "RSSB_CET_PAPER",
    "2026-10-16T01:00:00+00:00",
    "DISCOVERED",
    "RSSB Official",
    "https://rssb.rajasthan.gov.in/",
    "OFFICIAL_WEBSITE",
    "OFFICIAL",
    "RSSB",
    [],
    "Official source",
)


class FakeCursor:
    def __init__(self, *, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self, *, existing_hash=False, candidate_rows=(CANDIDATE_ROW,)):
        self.calls = []
        self.existing_hash = existing_hash
        self.candidate_rows = list(candidate_rows)

    def transaction(self):
        class Transaction:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return Transaction()

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        flat = " ".join(sql.split()).lower()
        if "from paper_candidates pc" in flat:
            return FakeCursor(rows=self.candidate_rows)
        if "select 1 from documents where sha256" in flat:
            return FakeCursor(row=(1,) if self.existing_hash else None)
        if "update paper_candidates" in flat and "returning candidate_id" in flat:
            return FakeCursor(row=(params[1],))
        return FakeCursor()


class FakeObjectStorage:
    bucket = "ai-comp-papers"

    def __init__(self):
        self.ensure_count = 0
        self.uploads = []

    def ensure_private_bucket(self):
        self.ensure_count += 1

    def upload(self, digest, payload, content_type):
        self.uploads.append((digest, payload, content_type))
        return StoredObject(
            bucket=self.bucket,
            object_key=f"papers/{digest[:2]}/{digest}",
            storage_uri=f"supabase://{self.bucket}/papers/{digest[:2]}/{digest}",
            duplicate=False,
        )


class FakeDownloader:
    def __init__(self, payload, content_type="text/plain", detected_format=DocumentFormat.TEXT, error=None):
        self.payload = payload
        self.content_type = content_type
        self.detected_format = detected_format
        self.error = error
        self.calls = []

    def download(self, source, url, policy):
        self.calls.append((source.source_id, url, policy))
        if self.error is not None:
            raise self.error
        return DownloadedPaper(
            requested_url=url,
            final_url=url,
            content_type=self.content_type,
            payload=self.payload,
            detected_format=self.detected_format,
        )


def sample_payload():
    return chr(10).join([
        "1. What is the capital of Rajasthan?",
        "A) Jaipur",
        "B) Jodhpur",
        "",
        "Answer Key",
        "1. A",
        "",
    ]).encode("utf-8")


def test_process_pending_candidate_persists_original_text_and_question_candidates():
    connection = FakeConnection()
    object_storage = FakeObjectStorage()
    payload = sample_payload()
    downloader = FakeDownloader(payload)

    summary = process_pending_candidates(
        connection,
        object_storage,
        source_id="RSSB_OFFICIAL",
        limit=5,
        downloader=downloader,
        policy=CrawlPolicy(True, respect_robots=True, respect_terms=True, rate_limit_seconds=0),
    )

    assert summary.selected == 1
    assert summary.processed == 1
    assert summary.question_candidates == 1
    assert summary.answer_key_entries == 1
    assert summary.failed == 0
    assert object_storage.ensure_count == 1
    assert object_storage.uploads == [(sha256(payload).hexdigest(), payload, "text/plain")]
    sql = [stmt.lower() for stmt, _ in connection.calls]
    assert any("insert into documents" in stmt for stmt in sql)
    assert any("insert into normalized_documents" in stmt for stmt in sql)
    assert any("insert into questions" in stmt for stmt in sql)
    assert any("insert into question_options" in stmt for stmt in sql)
    assert any("insert into answer_key_entries" in stmt for stmt in sql)
    assert any("update paper_candidates" in stmt for stmt in sql)
    assert not any("insert into exam_appearances" in stmt for stmt in sql)
    document_insert = next(
        params for stmt, params in connection.calls
        if "INSERT INTO documents" in stmt
    )
    assert document_insert[6].startswith("supabase://ai-comp-papers/")


def test_duplicate_document_is_not_re_extracted_or_uploaded():
    connection = FakeConnection(existing_hash=True)
    object_storage = FakeObjectStorage()
    downloader = FakeDownloader(sample_payload())

    summary = process_pending_candidates(
        connection,
        object_storage,
        downloader=downloader,
        policy=CrawlPolicy(True, respect_robots=True, respect_terms=True, rate_limit_seconds=0),
    )

    assert summary.selected == 1
    assert summary.duplicate_documents == 1
    assert summary.processed == 0
    assert object_storage.uploads == []
    assert not any("INSERT INTO questions" in stmt for stmt, _ in connection.calls)
    assert any("UPDATE paper_candidates" in stmt for stmt, _ in connection.calls)


def test_policy_blocked_candidate_is_rejected_not_verified():
    connection = FakeConnection()
    object_storage = FakeObjectStorage()
    downloader = FakeDownloader(b"", error=ResearchPolicyError("candidate_disallowed_by_robots"))

    summary = process_pending_candidates(
        connection,
        object_storage,
        downloader=downloader,
        policy=CrawlPolicy(True, respect_robots=True, respect_terms=True, rate_limit_seconds=0),
    )

    assert summary.rejected == 1
    assert summary.failed == 0
    assert summary.results[0].status == "REJECTED"
    assert not any("INSERT INTO questions" in stmt for stmt, _ in connection.calls)
    assert any(
        params == ("REJECTED", CANDIDATE_ROW[0])
        for stmt, params in connection.calls
        if "UPDATE paper_candidates" in stmt
    )


def test_no_pending_candidates_does_not_create_storage_bucket():
    connection = FakeConnection(candidate_rows=[])
    object_storage = FakeObjectStorage()

    summary = process_pending_candidates(
        connection,
        object_storage,
        downloader=FakeDownloader(sample_payload()),
    )

    assert summary.selected == 0
    assert object_storage.ensure_count == 0
    assert summary.results == ()
