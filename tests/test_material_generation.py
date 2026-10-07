from __future__ import annotations

from ai_comp.domain.material_analysis import ImportantFact, ProposedConcept
from ai_comp.domain.material_generation import (
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GeneratedQuestionStatus,
)
from ai_comp.domain.material_matching import MaterialMatchingResult
from ai_comp.domain.materials import MaterialFormat, MaterialSource, NormalizedMaterial
from ai_comp.material.generation import (
    FactGroundedAnswerVerifier,
    GeneratedQuestionService,
    GenerationQualityPolicy,
    MasterQuestionDuplicateFinder,
    StaticQuestionGenerationProvider,
)


def fact():
    return ImportantFact(
        fact_id="fact-1",
        material_id="material:6.5",
        fact_text="राजस्थान की राजधानी जयपुर है।",
        evidence_text="राजस्थान की राजधानी जयपुर है।",
        importance_score=0.95,
        confidence=0.98,
        fact_type="FACT",
    )


def concept():
    return ProposedConcept(
        concept_candidate_id="concept-1",
        material_id="material:6.5",
        label="राजस्थान की राजधानी",
        subject="Geography",
        topic="Rajasthan",
        subtopic="Capital",
        evidence_text="राजस्थान की राजधानी जयपुर है।",
        confidence=0.95,
    )


def question(stem="राजस्थान की राजधानी क्या है?", correct="B", quality=0.95):
    return GeneratedMCQ(
        generated_question_id="generated:1",
        generation_id="generation:1",
        material_id="material:6.5",
        stem=stem,
        options=(
            GeneratedOption("A", "उदयपुर"),
            GeneratedOption("B", "जयपुर"),
            GeneratedOption("C", "कोटा"),
            GeneratedOption("D", "अजमेर"),
        ),
        correct_option_key=correct,
        explanation="स्रोत तथ्य में जयपुर दिया गया है।",
        fact_ids=("fact-1",),
        concept_ids=("concept-1",),
        difficulty="MEDIUM",
        importance_score=0.95,
        quality_score=quality,
    )


def matching():
    return MaterialMatchingResult(
        material_id="material:6.5",
        existing_question_matches=(),
        same_concept_matches=(),
        related_topic_matches=(),
    )


def test_generation_spec_excludes_verified_existing_questions_from_new_question_identity():
    service = GeneratedQuestionService(
        StaticQuestionGenerationProvider(()),
        FactGroundedAnswerVerifier(),
    )
    spec = service.build_specification(
        material_id="material:6.5",
        facts=(fact(),),
        concepts=(concept(),),
        matching=matching(),
    )
    assert spec.material_id == "material:6.5"
    assert spec.fact_ids == ("fact-1",)
    assert spec.concept_ids == ("concept-1",)
    assert spec.existing_master_question_ids == ()


def test_fact_grounded_answer_verifier_verifies_only_source_supported_answer():
    result = FactGroundedAnswerVerifier().verify(question(), (fact(),), (concept(),))
    assert result.status is AnswerVerificationStatus.VERIFIED
    assert result.confidence >= 0.98
    assert result.evidence == (fact().evidence_text,)


def test_generation_accepts_only_verified_high_quality_question():
    generated = question()
    result = GeneratedQuestionService(
        StaticQuestionGenerationProvider((generated,)),
        FactGroundedAnswerVerifier(),
    ).generate(
        __import__("ai_comp.domain.material_generation", fromlist=["GenerationSpecification"]).GenerationSpecification(
            generation_id="generation:1",
            material_id="material:6.5",
            fact_ids=("fact-1",),
            concept_ids=("concept-1",),
        ),
        facts=(fact(),),
        concepts=(concept(),),
    )
    assert len(result.questions) == 1
    assert result.questions[0].status is GeneratedQuestionStatus.ACCEPTED
    assert result.questions[0].answer_verification is AnswerVerificationStatus.VERIFIED


def test_generation_rejects_answer_verification_evidence_not_in_source():
    class BadVerifier:
        def verify(self, question, facts, concepts):
            from ai_comp.domain.material_generation import AnswerVerificationResult
            return AnswerVerificationResult(
                status=AnswerVerificationStatus.VERIFIED,
                evidence=("बाहर की invented evidence",),
                confidence=0.99,
            )

    result = GeneratedQuestionService(
        StaticQuestionGenerationProvider((question(),)),
        BadVerifier(),
    ).generate(
        __import__("ai_comp.domain.material_generation", fromlist=["GenerationSpecification"]).GenerationSpecification(
            generation_id="generation:1",
            material_id="material:6.5",
            fact_ids=("fact-1",),
            concept_ids=("concept-1",),
        ),
        facts=(fact(),),
        concepts=(concept(),),
    )
    assert result.questions == ()
    assert result.rejected_question_ids == ("generated:1",)


def test_generation_rejects_duplicate_master_question():
    class Repo:
        def list_masters(self, **kwargs):
            from ai_comp.domain.master_questions import MasterQuestion, MasterQuestionStatus
            from ai_comp.domain.questions import QuestionKind, QuestionOption
            return (
                MasterQuestion(
                    master_question_id="master:1",
                    canonical_question_id="q:1",
                    stem="राजस्थान की राजधानी क्या है?",
                    options=(QuestionOption("A", "उदयपुर"), QuestionOption("B", "जयपुर")),
                    kind=QuestionKind.MCQ,
                    status=MasterQuestionStatus.ACTIVE,
                ),
            )

    result = GeneratedQuestionService(
        StaticQuestionGenerationProvider((question(),)),
        FactGroundedAnswerVerifier(),
        duplicate_finder=MasterQuestionDuplicateFinder(Repo()),
    ).generate(
        __import__("ai_comp.domain.material_generation", fromlist=["GenerationSpecification"]).GenerationSpecification(
            generation_id="generation:1",
            material_id="material:6.5",
            fact_ids=("fact-1",),
            concept_ids=("concept-1",),
        ),
        facts=(fact(),),
        concepts=(concept(),),
    )
    assert result.questions == ()
    assert result.rejected_question_ids == ("generated:1",)


def test_bad_option_keys_are_rejected_by_quality_gate():
    bad = GeneratedMCQ(
        **{**question().__dict__, "options": (
            GeneratedOption("A", "उदयपुर"),
            GeneratedOption("B", "जयपुर"),
            GeneratedOption("C", "कोटा"),
            GeneratedOption("E", "अजमेर"),
        )}
    )
    result = GeneratedQuestionService(
        StaticQuestionGenerationProvider((bad,)),
        FactGroundedAnswerVerifier(),
    ).generate(
        __import__("ai_comp.domain.material_generation", fromlist=["GenerationSpecification"]).GenerationSpecification(
            generation_id="generation:1",
            material_id="material:6.5",
            fact_ids=("fact-1",),
            concept_ids=("concept-1",),
        ),
        facts=(fact(),),
        concepts=(concept(),),
    )
    assert result.questions == ()
    assert result.rejected_question_ids == ("generated:1",)
