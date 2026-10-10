import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner
from ai_comp.database.models import EmbeddingModelRecord, PaperRecord
from ai_comp.database.postgres_appearance import PostgresAppearanceRepository
from ai_comp.database.postgres_answer_key import PostgresAnswerKeyRepository
from ai_comp.database.postgres_answer_resolution import PostgresAnswerResolutionRepository
from ai_comp.database.postgres_embedding import PostgresEmbeddingRepository
from ai_comp.database.postgres_match import PostgresMatchRepository
from ai_comp.database.postgres_material_match import PostgresMaterialQuestionMatchRepository
from ai_comp.database.postgres_master_question import PostgresMasterQuestionRepository
from ai_comp.database.postgres_concept import PostgresConceptRepository
from ai_comp.database.postgres_paper import PostgresPaperRepository
from ai_comp.database.postgres_question import PostgresQuestionRepository
from ai_comp.database.postgres_registry import PostgresRegistryRepository
from ai_comp.database.postgres_research import PostgresResearchRepository
from ai_comp.domain.exams import ConductingBody, Exam, ExamLevel, PaperCategory
from ai_comp.domain.master_questions import MasterAssignmentStatus, MasterMembershipType
from ai_comp.domain.answers import AnswerKeyResolver
from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.matching import ConceptRecord, MatchEvidence, MatchType, QuestionMatch
from ai_comp.domain.material_matching import MaterialProbeType, MaterialQuestionMatch
from ai_comp.domain.questions import (
    AnswerKeyEntry,
    QuestionCandidate,
    QuestionKind,
    QuestionOption,
)
from ai_comp.domain.sources import SourcePriority, SourceRecord, SourceType
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
)
from ai_comp.history.service import HistoryService
from ai_comp.master.maintenance import MasterQuestionMaintenanceService
from ai_comp.master.query import MasterQuestionQuery, MasterQuestionReadService
from ai_comp.master.service import MasterQuestionService
from ai_comp.research.paper import DocumentFormat, FetchedDocument, PaperCandidate
from ai_comp.research.processing import (
    ExtractionMethod,
    NormalizedDocument,
)
from ai_comp.research.metadata import StoredDocumentMetadata


pytestmark = pytest.mark.integration


def database_url() -> str:
    value = os.getenv("AI_COMP_DATABASE_URL", "").strip()
    if not value:
        pytest.skip("AI_COMP_DATABASE_URL is not configured")
    return value


def question(question_id: str, stem: str) -> QuestionCandidate:
    return QuestionCandidate(
        question_id=question_id,
        document_id="doc-1",
        document_sha256="a" * 64,
        question_number=1,
        stem=stem,
        options=(
            QuestionOption("A", "एक"),
            QuestionOption("B", "दो"),
        ),
        kind=QuestionKind.MCQ,
        raw_text=stem,
        start_line=1,
        end_line=3,
    )


def verification(verification_id: str, status=VerificationStatus.VERIFIED):
    return SourceVerification(
        verification_id=verification_id,
        source_id="rssb",
        source_url="https://rssb.example/paper.pdf",
        status=status,
        evidence_type=EvidenceType.OFFICIAL_PAPER,
        checked_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        confidence=1.0,
    )


def appearance(
    appearance_id: str,
    question_id: str,
    *,
    source_url: str,
    match_type: str = "EXACT",
) -> ExamAppearance:
    return ExamAppearance(
        appearance_id=appearance_id,
        question_id=question_id,
        exam_id="cet-2024",
        conducting_body_id="rssb",
        year=2024,
        exam_date="2024-01-10",
        shift="Shift 1",
        question_number=1,
        original_question="राजस्थान का उदाहरण?",
        options=(("A", "एक"), ("B", "दो")),
        correct_answer="A",
        source_url=source_url,
        paper_id="paper-1",
        verification=verification("v1"),
        match_type=match_type,
    )


def test_full_phase4_postgres_round_trip():
    dsn = database_url()
    with connect_postgres(dsn) as connection:
        migrations_dir = Path(__file__).resolve().parents[1] / "database" / "migrations"
        migration_runner = MigrationRunner(migrations_dir)
        expected_versions = tuple(item.version for item in migration_runner.discover())
        assert expected_versions == tuple(f"{version:04d}" for version in range(1, 17))
        # Earlier integration tests may already have applied the migrations.
        assert set(migration_runner.apply(connection)).issubset(expected_versions)
        assert migration_runner.apply(connection) == ()

        registry = PostgresRegistryRepository(connection)
        registry.save_body(
            ConductingBody(
                body_id="rssb",
                name="RSSB",
                level=ExamLevel.STATE,
                state="RJ",
                official_domains=("rssb.rajasthan.gov.in",),
            )
        )
        registry.save_exam(
            Exam(
                exam_id="cet-2024",
                name="CET 2024",
                conducting_body_id="rssb",
                level=ExamLevel.STATE,
                state="RJ",
            )
        )
        registry.save_category(
            PaperCategory(
                category_id="cet-general",
                name="General",
                exam_id="cet-2024",
            )
        )
        registry.save_source(
            SourceRecord(
                source_id="rssb-source",
                name="RSSB Official",
                base_url="https://rssb.rajasthan.gov.in",
                source_type=SourceType.OFFICIAL_PAPER,
                priority=SourcePriority.OFFICIAL,
                conducting_body_id="rssb",
            )
        )

        verification_record = SourceVerification(
            verification_id="v1",
            source_id="rssb-source",
            source_url="https://rssb.rajasthan.gov.in/paper.pdf",
            status=VerificationStatus.VERIFIED,
            evidence_type=EvidenceType.OFFICIAL_PAPER,
            checked_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
            confidence=1.0,
        )
        registry.save_verification(verification_record)

        research = PostgresResearchRepository(connection)
        candidate = PaperCandidate(
            candidate_id="candidate-1",
            source_id="rssb-source",
            url="https://rssb.rajasthan.gov.in/paper.pdf",
            title="CET 2024",
            format=DocumentFormat.PDF,
            category_id="cet-general",
            discovered_at="2024-01-01T00:00:00+00:00",
        )
        research.save_candidate(candidate)

        PostgresPaperRepository(connection).save(
            PaperRecord(
                paper_id="paper-1",
                candidate_id="candidate-1",
                title="CET 2024",
                exam_id="cet-2024",
                category_id="cet-general",
                source_id="rssb-source",
                canonical_url=candidate.url,
                year=2024,
                shift="Shift 1",
            )
        )

        document = FetchedDocument(
            document_id="doc-1",
            candidate_id="candidate-1",
            source_url=candidate.url,
            content_type="application/pdf",
            sha256="a" * 64,
            size_bytes=10,
            storage_key="a" * 64,
            format=DocumentFormat.PDF,
        )
        research.save_document(document)

        normalized = NormalizedDocument(
            document=document,
            metadata=StoredDocumentMetadata(
                document_id="doc-1",
                candidate_id="candidate-1",
                source_url=candidate.url,
                content_type="application/pdf",
                sha256="a" * 64,
                size_bytes=10,
                storage_key="a" * 64,
                declared_format=DocumentFormat.PDF,
                detected_format=DocumentFormat.PDF,
            ),
            text="""1. राजस्थान का उदाहरण?
A. एक
B. दो""",
            extraction_method=ExtractionMethod.PDF_TEXT,
        )
        research.save_normalized_document(normalized)

        q_repo = PostgresQuestionRepository(connection)
        q_repo.save(question("q1", "राजस्थान का उदाहरण?"))
        q_repo.save(question("q2", "राजस्थान का उदाहरण?"))
        answer_repo = PostgresAnswerKeyRepository(connection)
        answer_entries = (AnswerKeyEntry(1, "A", "1-A", 10),)
        answer_repo.save_many("doc-1", answer_entries)

        resolution = AnswerKeyResolver().resolve(q_repo.get("q1"), answer_entries[0])
        answer_resolution_repo = PostgresAnswerResolutionRepository(connection)
        answer_resolution_repo.save(resolution)

        PostgresConceptRepository(connection).save(
            ConceptRecord(
                concept_id="C1",
                label="Rajasthan Example",
                subject="General",
                topic="Rajasthan",
            )
        )

        PostgresConceptRepository(connection).link_question("q1", "C1")

        match_repo = PostgresMatchRepository(connection)
        match_repo.save(
            QuestionMatch(
                "q1",
                "q2",
                MatchType.EXACT,
                1.0,
                (MatchEvidence("normalized_text_sha256"),),
            )
        )
        match_repo.save(
            QuestionMatch(
                "q2",
                "q1",
                MatchType.EXACT,
                1.0,
            )
        )

        appearance_repo = PostgresAppearanceRepository(connection)
        appearance_repo.save(
            appearance(
                "a1",
                "q1",
                source_url="https://rssb.rajasthan.gov.in/paper.pdf",
            )
        )
        appearance_repo.save(
            appearance(
                "a2",
                "q2",
                source_url="https://secondary.example/paper.pdf",
            )
        )

        history = HistoryService(
            appearance_repo,
            match_repository=match_repo,
        ).get_history_view("q1")

        assert history.verified_appearance_count == 1
        assert len(history.exact_appearances) == 1

        master_repo = PostgresMasterQuestionRepository(connection)
        master_service = MasterQuestionService(master_repo)
        created = master_service.assign(q_repo.get("q1"))
        assigned = master_service.assign(
            q_repo.get("q2"),
            (QuestionMatch("q2", "q1", MatchType.EXACT, 1.0),),
        )

        assert created.status is MasterAssignmentStatus.CREATED
        assert assigned.status is MasterAssignmentStatus.ASSIGNED
        assert assigned.master_question_id == created.master_question_id

        material_match_repo = PostgresMaterialQuestionMatchRepository(connection)
        material_match_repo.save(
            MaterialQuestionMatch(
                material_id="material:phase64",
                probe_id="probe:integration",
                probe_type=MaterialProbeType.QUESTION_TEXT,
                master_question_id=created.master_question_id,
                match_type=MatchType.EXACT,
                confidence=1.0,
                verified_appearance_count=1,
                evidence=(MatchEvidence("normalized_question_text", 1.0),),
            )
        )
        assert len(material_match_repo.get_for_material("material:phase64")) == 1
        assert len(master_repo.get_memberships_for_master(created.master_question_id)) == 2
        loaded_master = master_repo.get_master(created.master_question_id)
        assert loaded_master is not None
        assert loaded_master.canonical_question_id == "q1"

        q3 = question("q3", "अलग प्रश्न?")
        q3_repo = PostgresQuestionRepository(connection)
        q3_repo.save(q3)
        created_second = master_service.assign(q3)

        maintenance = MasterQuestionMaintenanceService(master_repo)
        merged = maintenance.merge(
            created.master_question_id,
            created_second.master_question_id,
            reason="verified duplicate review",
        )

        assert merged.moved_question_count == 2
        merged_source = master_repo.get_master(created.master_question_id)
        assert merged_source is not None
        assert merged_source.status.value == "MERGED"
        assert (
            master_repo.get_master_for_question("q1").master_question_id
            == created_second.master_question_id
        )
        assert len(
            master_repo.get_memberships_for_master(
                created_second.master_question_id
            )
        ) == 3

        q4 = question("q4", "चौथा अलग प्रश्न?")
        q3_repo.save(q4)
        created_third = master_service.assign(q4)

        repaired = maintenance.repair(
            "q2",
            created_third.master_question_id,
            relationship=MasterMembershipType.REPHRASED,
            confidence=0.93,
            reason="manual assignment correction",
        )
        assert repaired.source_master_id == created_second.master_question_id
        assert repaired.target_master_id == created_third.master_question_id
        assert master_repo.get_membership_for_question("q2").master_question_id == created_third.master_question_id

        views = MasterQuestionReadService(master_repo).list_views(
            MasterQuestionQuery(status=merged_source.status)
        )
        assert [view.master_question_id for view in views] == [
            created.master_question_id
        ]

        embeddings = PostgresEmbeddingRepository(connection)
        embeddings.save_model(
            EmbeddingModelRecord(
                model_id="model-v1",
                provider="test",
                model_name="test-embedding",
                dimensions=3,
                version="1",
            )
        )
        embeddings.save_embedding("q1", "model-v1", (0.1, 0.2, 0.3))
        embeddings.save_embedding("q2", "model-v1", (0.1, 0.2, 0.31))
        assert embeddings.get_embedding("q1", "model-v1") == (0.1, 0.2, 0.3)
        neighbors = embeddings.nearest_neighbors(
            "model-v1",
            (0.1, 0.2, 0.3),
            limit=1,
            exclude_question_id="q1",
        )
        assert neighbors[0][0] == "q2"
        assert neighbors[0][1] > 0.99

        source = registry.get_source("rssb-source")
        assert source is not None
        assert registry.get_exam("cet-2024") is not None
        assert len(registry.get_verifications("rssb-source")) == 1
        assert q_repo.get("q1") is not None
        assert len(answer_repo.get_for_document("doc-1")) == 1
        assert answer_resolution_repo.get_for_question("q1")[0].selected_option_key == "A"
        assert PostgresConceptRepository(connection).get("C1") is not None
        assert len(match_repo.get_for_question("q1")) == 1
        assert PostgresPaperRepository(connection).get("paper-1") is not None
