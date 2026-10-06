# Phase 6.4 PostgreSQL integration test is kept separate so the core test stays readable.

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ai_comp.database.connection import connect_postgres
from ai_comp.database.migrations import MigrationRunner
from ai_comp.database.postgres_material_match import (
    PostgresMaterialQuestionMatchRepository,
)
from ai_comp.database.postgres_question import PostgresQuestionRepository
from ai_comp.database.postgres_appearance import PostgresAppearanceRepository
from ai_comp.database.postgres_master_question import PostgresMasterQuestionRepository
from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.matching import MatchEvidence, MatchType
from ai_comp.domain.material_matching import MaterialProbeType, MaterialQuestionMatch
from ai_comp.domain.master_questions import MasterMembershipType, MasterQuestion, MasterQuestionMembership
from ai_comp.domain.questions import QuestionCandidate, QuestionKind, QuestionOption
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
)
from ai_comp.material.matching import MaterialExamMatchingService
from ai_comp.history.repository import InMemoryAppearanceRepository


pytestmark = pytest.mark.integration


def database_url() -> str:
    value = os.getenv("AI_COMP_DATABASE_URL", "").strip()
    if not value:
        pytest.skip("AI_COMP_DATABASE_URL is not configured")
    return value


def question() -> QuestionCandidate:
    return QuestionCandidate(
        question_id="phase64-q1",
        document_id="phase64-doc",
        document_sha256="e" * 64,
        question_number=1,
        stem="राजस्थान की राजधानी क्या है?",
        options=(
            QuestionOption("A", "जयपुर"),
            QuestionOption("B", "उदयपुर"),
        ),
        kind=QuestionKind.MCQ,
        raw_text="राजस्थान की राजधानी क्या है?",
        start_line=1,
        end_line=3,
    )


def test_phase64_material_match_repository_round_trip():
    with connect_postgres(database_url()) as connection:
        migrations_dir = Path(__file__).resolve().parents[1] / "database" / "migrations"
        MigrationRunner(migrations_dir).apply(connection)

        question_repo = PostgresQuestionRepository(connection)
        question_repo.save(question())

        master_repo = PostgresMasterQuestionRepository(connection)
        master_repo.save_master(
            MasterQuestion(
                master_question_id="phase64-m1",
                canonical_question_id="phase64-q1",
                stem=question().stem,
                options=question().options,
                kind=question().kind,
                concept_id="RJ-CAPITAL",
            )
        )
        master_repo.save_membership(
            MasterQuestionMembership(
                master_question_id="phase64-m1",
                question_id="phase64-q1",
                relationship=MasterMembershipType.CANONICAL,
                confidence=1.0,
            )
        )

        appearance_repo = PostgresAppearanceRepository(connection)
        appearance_repo.save(
            ExamAppearance(
                appearance_id="phase64-a1",
                question_id="phase64-q1",
                exam_id="phase64-exam",
                conducting_body_id=None,
                year=2024,
                exam_date="2024-01-01",
                shift="Shift 1",
                question_number=1,
                original_question=question().stem,
                options=(("A", "जयपुर"), ("B", "उदयपुर")),
                correct_answer="A",
                source_url="https://example.gov/paper.pdf",
                paper_id="phase64-paper",
                verification=SourceVerification(
                    verification_id="phase64-v1",
                    source_id="phase64-source",
                    source_url="https://example.gov/paper.pdf",
                    status=VerificationStatus.VERIFIED,
                    evidence_type=EvidenceType.OFFICIAL_PAPER,
                    checked_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
                    confidence=1.0,
                ),
            )
        )

        match = MaterialQuestionMatch(
            material_id="material:phase64",
            probe_id="probe:1",
            probe_type=MaterialProbeType.QUESTION_TEXT,
            master_question_id="phase64-m1",
            match_type=MatchType.EXACT,
            confidence=1.0,
            verified_appearance_count=1,
            evidence=(MatchEvidence("normalized_question_text", 1.0),),
        )
        repo = PostgresMaterialQuestionMatchRepository(connection)
        repo.save(match)
        repo.save(match)

        rows = repo.get_for_material("material:phase64")
        assert rows == (match,)
