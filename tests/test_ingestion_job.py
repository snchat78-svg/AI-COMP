from datetime import datetime, timezone

import pytest

from ai_comp.domain.ingestion import IngestionJobStatus
from ai_comp.ingestion.durable import (
    InMemoryIngestionStore,
    InMemoryIngestionTransactionBoundary,
    IngestionJobService,
)
from ai_comp.ingestion.orchestrator import IngestionResult


class Document:
    sha256 = "a" * 64
    document_id = "doc-1"


class NormalizedDocument:
    document = Document()


class Request:
    document = NormalizedDocument()
    exam_id = "exam-1"
    paper_id = "paper-1"
    year = 2025
    shift = "1"
    source_url = "https://example.gov/paper.pdf"


class FakeProcessor:
    def __init__(self):
        self.calls = 0
        self.fail_times = 0

    def ingest(self, request, *, resume_after=None, progress_callback=None):
        self.calls += 1
        if self.fail_times:
            self.fail_times -= 1
            raise RuntimeError("temporary failure")
        return IngestionResult(
            document_id=request.document.document.document_id,
            question_count=10,
            answer_resolution_count=9,
            unresolved_answer_count=1,
            match_count=8,
            appearance_count=0,
            master_assignment_count=10,
            historical_ingestion_allowed=False,
            history_skip_reason="not verified",
            master_assignments=(),
            unresolved_answers=(),
        )


class StageAwareProcessor(FakeProcessor):
    def __init__(self):
        super().__init__()
        self.resume_markers = []

    def ingest(self, request, *, resume_after=None, progress_callback=None):
        self.calls += 1
        self.resume_markers.append(resume_after)
        if progress_callback is not None:
            progress_callback(
                IngestionJobStatus.EXTRACTED,
                {"question_count": 10},
            )
            progress_callback(
                IngestionJobStatus.MATCHED,
                {"match_count": 8},
            )
            if self.fail_times:
                self.fail_times -= 1
                raise RuntimeError("failure after MATCHED")
            progress_callback(
                IngestionJobStatus.MASTERED,
                {"master_assignment_count": 10},
            )
        return IngestionResult(
            document_id=request.document.document.document_id,
            question_count=10,
            answer_resolution_count=9,
            unresolved_answer_count=1,
            match_count=8,
            appearance_count=0,
            master_assignment_count=10,
            historical_ingestion_allowed=False,
            history_skip_reason="not verified",
            master_assignments=(),
            unresolved_answers=(),
        )


def make_service(processor=None):
    store = InMemoryIngestionStore()
    boundary = InMemoryIngestionTransactionBoundary(store)
    processor = processor or FakeProcessor()
    return (
        IngestionJobService(
            boundary=boundary,
            processor=processor,
            max_attempts=2,
        ),
        store,
        processor,
    )


def test_idempotency_key_is_stable_and_source_independent():
    service, _, _ = make_service()

    key1 = service.idempotency_key(Request())
    Request.source_url = "https://mirror.example/paper.pdf"
    key2 = service.idempotency_key(Request())

    assert key1 == key2
    assert len(key1) == 64


def test_completed_job_is_processed_only_once():
    service, store, processor = make_service()

    first = service.run(Request())
    second = service.run(Request())

    assert processor.calls == 1
    assert first.job.status is IngestionJobStatus.COMPLETED
    assert second.job.status is IngestionJobStatus.COMPLETED
    assert second.replayed is True
    assert len(store.jobs_by_id) == 1

    events = tuple(store.outbox_by_id.values())
    assert [event.event_type for event in events].count(
        "INGESTION_JOB_CREATED"
    ) == 1


def test_failure_is_durable_and_can_be_retried():
    processor = FakeProcessor()
    processor.fail_times = 1
    service, store, processor = make_service(processor)

    first = service.run(Request())

    assert first.job.status is IngestionJobStatus.RETRYABLE
    assert first.error is not None
    assert processor.calls == 1

    second = service.run(Request())

    assert second.job.status is IngestionJobStatus.COMPLETED
    assert processor.calls == 2
    assert second.job.attempt_count == 2


def test_partial_failure_resumes_from_last_durable_stage():
    processor = StageAwareProcessor()
    processor.fail_times = 1
    service, _, processor = make_service(processor)

    first = service.run(Request())

    assert first.job.status is IngestionJobStatus.RETRYABLE
    assert first.job.checkpoint["resume_after"] == "MATCHED"

    second = service.run(Request())

    assert second.job.status is IngestionJobStatus.COMPLETED
    assert processor.resume_markers == [
        None,
        IngestionJobStatus.MATCHED,
    ]
    assert second.job.attempt_count == 2


def test_failed_transaction_rolls_back_job_and_outbox_together():
    store = InMemoryIngestionStore()
    boundary = InMemoryIngestionTransactionBoundary(store)

    def operation(repositories):
        from ai_comp.domain.ingestion import IngestionJob

        now = datetime.now(timezone.utc)
        job = IngestionJob.create(
            job_id="ingestion:test",
            idempotency_key="b" * 64,
            document_id="doc-2",
            document_sha256="b" * 64,
            paper_id="paper-2",
            exam_id="exam-2",
            year=2025,
            shift=None,
            source_url="https://example.gov/paper.pdf",
            now=now,
        )
        repositories.jobs.create_if_absent(job)
        raise RuntimeError("rollback")

    with pytest.raises(RuntimeError, match="rollback"):
        boundary.execute(operation)

    assert store.jobs_by_id == {}
    assert store.jobs_by_key == {}
    assert store.outbox_by_id == {}
