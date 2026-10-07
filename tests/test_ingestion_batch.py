from datetime import datetime, timezone

from ai_comp.domain.ingestion import IngestionJobStatus
from ai_comp.domain.ingestion_batch import IngestionBatch, IngestionBatchStatus
from ai_comp.ingestion.batch import (
    InMemoryIngestionBatchStore,
    InMemoryIngestionBatchTransactionBoundary,
    IngestionBatchService,
)
from ai_comp.ingestion.durable import (
    InMemoryIngestionStore,
    IngestionJobService,
)
from ai_comp.ingestion.orchestrator import IngestionResult


class Request:
    def __init__(self, *, paper_id, document_id, sha256, source_url):
        document = type("Document", (), {
            "document_id": document_id,
            "sha256": sha256,
        })()
        self.document = type("NormalizedDocument", (), {
            "document": document,
        })()
        self.exam_id = "exam-1"
        self.paper_id = paper_id
        self.year = 2025
        self.shift = "1"
        self.source_url = source_url


class Processor:
    def __init__(self):
        self.calls = []
        self.fail_once_for = set()

    def ingest(self, request, *, resume_after=None, progress_callback=None):
        self.calls.append(request.paper_id)
        if request.paper_id in self.fail_once_for:
            self.fail_once_for.remove(request.paper_id)
            raise RuntimeError("temporary batch failure")
        return IngestionResult(
            document_id=request.document.document.document_id,
            question_count=1,
            answer_resolution_count=1,
            unresolved_answer_count=0,
            match_count=0,
            appearance_count=0,
            master_assignment_count=1,
            historical_ingestion_allowed=False,
            history_skip_reason="not verified",
            master_assignments=(),
            unresolved_answers=(),
        )


def verification():
    from ai_comp.domain.verification import (
        EvidenceType,
        SourceVerification,
        VerificationStatus,
    )
    return SourceVerification(
        verification_id="v-batch",
        source_id="official",
        source_url="https://example.gov/paper.pdf",
        status=VerificationStatus.VERIFIED,
        evidence_type=EvidenceType.OFFICIAL_PAPER,
        checked_at=datetime.now(timezone.utc),
        confidence=1.0,
    )


def make_request(paper_id, digit):
    digest = digit * 64
    return Request(
        paper_id=paper_id,
        document_id=f"doc-{paper_id}",
        sha256=digest,
        source_url=f"https://example.gov/{paper_id}.pdf",
    )


def make_service(processor=None):
    job_store = InMemoryIngestionStore()
    batch_store = InMemoryIngestionBatchStore()
    from ai_comp.ingestion.durable import InMemoryIngestionTransactionBoundary

    job_boundary = InMemoryIngestionTransactionBoundary(job_store)
    processor = processor or Processor()
    job_service = IngestionJobService(
        boundary=job_boundary,
        processor=processor,
        max_attempts=2,
    )
    batch_boundary = InMemoryIngestionBatchTransactionBoundary(
        batch_store=batch_store,
        job_store=job_store,
    )
    batch_service = IngestionBatchService(
        job_service=job_service,
        boundary=batch_boundary,
    )
    return batch_service, job_store, batch_store, processor


def with_verification(request):
    request.verification = verification()
    return request


def test_batch_is_order_independent_and_deduplicates_mirror_copies():
    batch_service, _, batch_store, _ = make_service()
    r1 = with_verification(make_request("paper-1", "a"))
    r2 = with_verification(make_request("paper-2", "b"))
    r1_mirror = with_verification(
        Request(
            paper_id="paper-1",
            document_id="doc-paper-1",
            sha256="a" * 64,
            source_url="https://mirror.example/paper-1.pdf",
        )
    )

    result = batch_service.run((r2, r1_mirror, r1))
    reverse_key = batch_service.idempotency_key((r1, r2))
    assert result.batch.idempotency_key == reverse_key
    assert result.batch.total_jobs == 2
    assert result.batch.status is IngestionBatchStatus.COMPLETED
    assert len(batch_store.batches_by_id) == 1


def test_partial_failure_resumes_only_retryable_jobs():
    batch_service, _, _, processor = make_service()
    r1 = with_verification(make_request("paper-1", "a"))
    r2 = with_verification(make_request("paper-2", "b"))
    processor.fail_once_for.add("paper-2")

    first = batch_service.run((r1, r2))
    assert first.batch.status is IngestionBatchStatus.PARTIAL_FAILURE
    assert first.batch.completed_jobs == 1
    assert first.batch.retryable_jobs == 1
    assert processor.calls == ["paper-1", "paper-2"]

    second = batch_service.run((r1, r2))
    assert second.batch.status is IngestionBatchStatus.COMPLETED
    assert second.batch.completed_jobs == 2
    assert second.job_results
    assert processor.calls == ["paper-1", "paper-2", "paper-2"]


def test_completed_batch_is_replayed_without_reprocessing_jobs():
    batch_service, _, _, processor = make_service()
    r1 = with_verification(make_request("paper-1", "a"))
    r2 = with_verification(make_request("paper-2", "b"))

    first = batch_service.run((r1, r2))
    second = batch_service.run((r2, r1))

    assert first.batch.status is IngestionBatchStatus.COMPLETED
    assert second.batch.status is IngestionBatchStatus.COMPLETED
    assert second.replayed is True
    assert processor.calls == ["paper-1", "paper-2"]


def test_batch_rollback_keeps_batch_and_outbox_atomic():
    from ai_comp.domain.ingestion import OutboxEvent

    batch_service, job_store, batch_store, _ = make_service()
    now = datetime.now(timezone.utc)
    batch = IngestionBatch.create(
        batch_id="batch:test",
        idempotency_key="c" * 64,
        job_ids=("job-1",),
        now=now,
    )

    def operation(repositories):
        repositories.batches.create_if_absent(batch)
        repositories.outbox.save(
            OutboxEvent.for_batch_update(
                batch=batch,
                previous_status=None,
                event_type="INGESTION_BATCH_CREATED",
                now=now,
            )
        )
        raise RuntimeError("rollback")

    try:
        batch_service.boundary.execute(operation)
    except RuntimeError:
        pass

    assert batch_store.batches_by_id == {}
    assert job_store.outbox_by_id == {}
