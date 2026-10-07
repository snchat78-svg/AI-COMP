from __future__ import annotations

from datetime import datetime, timezone

from ai_comp.domain.history import ExamAppearance
from ai_comp.domain.matching import MatchType
from ai_comp.domain.material_analysis import ProposedConcept
from ai_comp.domain.material_matching import MaterialQuestionProbe
from ai_comp.domain.materials import MaterialFormat, MaterialSource, NormalizedMaterial
from ai_comp.domain.master_questions import (
    MasterMembershipType,
    MasterQuestion,
    MasterQuestionMembership,
)
from ai_comp.domain.questions import QuestionKind, QuestionOption
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
)
from ai_comp.history.repository import InMemoryAppearanceRepository
from ai_comp.master.repository import InMemoryMasterQuestionRepository
from ai_comp.material.matching import (
    MaterialExamMatchingService,
    MaterialMatchingPolicy,
    MaterialQuestionProbeExtractor,
)


def material(text: str) -> NormalizedMaterial:
    return NormalizedMaterial(
        material_id="material:6.4",
        filename="notes.txt",
        source=MaterialSource.USER_NOTE,
        format=MaterialFormat.TEXT,
        content_type="text/plain",
        sha256="d" * 64,
        size_bytes=len(text.encode("utf-8")),
        text=text,
        extraction_method="DIRECT_TEXT",
        storage_key="/tmp/material",
    )


def seed_master(
    master_repo: InMemoryMasterQuestionRepository,
    appearance_repo: InMemoryAppearanceRepository,
    *,
    question_id: str,
    master_id: str,
    stem: str,
    verification_status: VerificationStatus,
    concept_id: str | None = None,
) -> None:
    master_repo.save_master(
        MasterQuestion(
            master_question_id=master_id,
            canonical_question_id=question_id,
            stem=stem,
            options=(QuestionOption("A", "एक"), QuestionOption("B", "दो")),
            kind=QuestionKind.MCQ,
            concept_id=concept_id,
        )
    )
    master_repo.save_membership(
        MasterQuestionMembership(
            master_question_id=master_id,
            question_id=question_id,
            relationship=MasterMembershipType.CANONICAL,
            confidence=1.0,
        )
    )
    appearance_repo.save(
        ExamAppearance(
            appearance_id=f"appearance:{question_id}",
            question_id=question_id,
            exam_id=f"cet-2024-{question_id}",
            conducting_body_id="rssb",
            year=2024,
            exam_date="2024-01-10",
            shift="Shift 1",
            question_number=1,
            original_question=stem,
            options=(("A", "एक"), ("B", "दो")),
            correct_answer="A",
            source_url="https://rssb.example/paper.pdf",
            paper_id=f"paper-{question_id}",
            verification=SourceVerification(
                verification_id=f"verification:{question_id}",
                source_id="rssb",
                source_url="https://rssb.example/paper.pdf",
                status=verification_status,
                evidence_type=EvidenceType.OFFICIAL_PAPER,
                checked_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
                confidence=1.0,
            ),
        )
    )


def test_only_verified_master_questions_are_searchable():
    masters = InMemoryMasterQuestionRepository()
    appearances = InMemoryAppearanceRepository()
    seed_master(
        masters, appearances,
        question_id="q-unverified",
        master_id="m-unverified",
        stem="राजस्थान की राजधानी क्या है?",
        verification_status=VerificationStatus.UNVERIFIED,
    )
    result = MaterialExamMatchingService(masters, appearances).match(
        material("सिर्फ तथ्य।")
    )
    assert result.existing_question_matches == ()
    assert result.warnings == (
        "verified master-question database returned no candidates",
    )


def test_exact_existing_question_detection_requires_question_probe():
    masters = InMemoryMasterQuestionRepository()
    appearances = InMemoryAppearanceRepository()
    seed_master(
        masters, appearances,
        question_id="q1",
        master_id="m1",
        stem="राजस्थान की राजधानी क्या है?",
        verification_status=VerificationStatus.VERIFIED,
    )
    result = MaterialExamMatchingService(masters, appearances).match(
        material("राजस्थान की राजधानी क्या है?\n\nराजस्थान की राजधानी जयपुर है.")
    )
    assert len(result.existing_question_matches) == 1
    assert result.existing_question_matches[0].match_type is MatchType.EXACT
    assert result.existing_question_matches[0].verified_appearance_count == 1


def test_plain_fact_is_not_semantically_declared_as_existing_question():
    masters = InMemoryMasterQuestionRepository()
    appearances = InMemoryAppearanceRepository()
    seed_master(
        masters, appearances,
        question_id="q1",
        master_id="m1",
        stem="राजस्थान की राजधानी क्या है?",
        verification_status=VerificationStatus.VERIFIED,
    )
    result = MaterialExamMatchingService(
        masters,
        appearances,
        embedding=lambda _: (1.0, 0.0),
    ).match(material("राजस्थान की राजधानी जयपुर है।"))
    assert result.existing_question_matches == ()
    assert result.unmatched_question_probe_ids == ()


def test_rephrased_detection_requires_margin():
    masters = InMemoryMasterQuestionRepository()
    appearances = InMemoryAppearanceRepository()
    seed_master(
        masters, appearances,
        question_id="q1",
        master_id="m1",
        stem="राजस्थान की राजधानी क्या है?",
        verification_status=VerificationStatus.VERIFIED,
    )
    seed_master(
        masters, appearances,
        question_id="q2",
        master_id="m2",
        stem="राजस्थान का सबसे बड़ा जिला कौन सा है?",
        verification_status=VerificationStatus.VERIFIED,
    )

    def embed(text: str):
        if "राजधानी" in text:
            return (1.0, 0.0)
        return (0.99, 0.01)

    service = MaterialExamMatchingService(
        masters,
        appearances,
        embedding=embed,
        policy=MaterialMatchingPolicy(
            min_rephrased_confidence=0.90,
            min_confidence_margin=0.05,
        ),
    )
    probe = MaterialQuestionProbe(
        probe_id="probe:manual",
        material_id="material:6.4",
        text="राजस्थान की राजधानी किसे कहा जाता है?",
        evidence_text="राजस्थान की राजधानी किसे कहा जाता है?",
    )
    result = service.match(material(probe.text), question_probes=(probe,))
    assert result.existing_question_matches == ()
    assert result.unmatched_question_probe_ids == ("probe:manual",)


def test_rephrased_detection_accepts_clear_winner():
    masters = InMemoryMasterQuestionRepository()
    appearances = InMemoryAppearanceRepository()
    seed_master(
        masters, appearances,
        question_id="q1",
        master_id="m1",
        stem="राजस्थान की राजधानी क्या है?",
        verification_status=VerificationStatus.VERIFIED,
    )
    seed_master(
        masters, appearances,
        question_id="q2",
        master_id="m2",
        stem="भारतीय संविधान का अनुच्छेद 21 किससे संबंधित है?",
        verification_status=VerificationStatus.VERIFIED,
    )

    def embed(text: str):
        if "राजधानी" in text:
            return (1.0, 0.0)
        return (0.0, 1.0)

    service = MaterialExamMatchingService(masters, appearances, embedding=embed)
    probe = MaterialQuestionProbe(
        probe_id="probe:clear",
        material_id="material:6.4",
        text="राजस्थान की राजधानी किसे कहा जाता है?",
        evidence_text="राजस्थान की राजधानी किसे कहा जाता है?",
    )
    result = service.match(material(probe.text), question_probes=(probe,))
    assert len(result.existing_question_matches) == 1
    assert result.existing_question_matches[0].match_type is MatchType.REPHRASED
    assert result.existing_question_matches[0].master_question_id == "m1"


def test_same_concept_is_separate_from_existing_question_detection():
    masters = InMemoryMasterQuestionRepository()
    appearances = InMemoryAppearanceRepository()
    seed_master(
        masters, appearances,
        question_id="q1",
        master_id="m1",
        stem="राजस्थान की राजधानी क्या है?",
        verification_status=VerificationStatus.VERIFIED,
        concept_id="RJ-CAPITAL",
    )
    concept = ProposedConcept(
        concept_candidate_id="concept:1",
        material_id="material:6.4",
        label="राजस्थान की राजधानी",
        subject="Geography",
        topic="Rajasthan",
        subtopic="Capital",
        evidence_text="राजस्थान की राजधानी",
        confidence=0.91,
    )
    result = MaterialExamMatchingService(
        masters,
        appearances,
        concept_resolver=lambda _: "RJ-CAPITAL",
    ).match(
        material("राजस्थान की राजधानी जयपुर है।"),
        concepts=(concept,),
    )
    assert result.existing_question_matches == ()
    assert len(result.same_concept_matches) == 1
    assert result.same_concept_matches[0].match_type is MatchType.SAME_CONCEPT


def test_related_topic_can_be_returned_but_never_promoted_to_existing_question():
    masters = InMemoryMasterQuestionRepository()
    appearances = InMemoryAppearanceRepository()
    seed_master(
        masters, appearances,
        question_id="q1",
        master_id="m1",
        stem="राजस्थान की राजधानी क्या है?",
        verification_status=VerificationStatus.VERIFIED,
    )
    concept = ProposedConcept(
        concept_candidate_id="concept:2",
        material_id="material:6.4",
        label="राजस्थान के शहर",
        subject="Geography",
        topic="Rajasthan",
        subtopic="Cities",
        evidence_text="राजस्थान के शहर",
        confidence=0.88,
    )
    result = MaterialExamMatchingService(
        masters,
        appearances,
        related_topic_resolver=lambda _, __: 0.90,
    ).match(
        material("राजस्थान के शहर"),
        concepts=(concept,),
    )
    assert result.existing_question_matches == ()
    assert len(result.related_topic_matches) == 1
    assert result.related_topic_matches[0].match_type is MatchType.RELATED_TOPIC


def test_question_probe_extractor_is_deduplicated_and_grounded():
    item = material(
        "नोट्स\n\n1. राजस्थान की राजधानी क्या है?\n\n"
        "1. राजस्थान की राजधानी क्या है?\n"
    )
    probes = MaterialQuestionProbeExtractor().extract(item)
    assert len(probes) == 1
    assert len({p.probe_id for p in probes}) == 1
    assert all(p.evidence_text in item.text for p in probes)
