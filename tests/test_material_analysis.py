import pytest

from ai_comp.domain.material_analysis import (
    ContentUnderstanding,
    ImportantFact,
    ProposedConcept,
)
from ai_comp.domain.materials import (
    MaterialFormat,
    MaterialSource,
    NormalizedMaterial,
)
from ai_comp.material.analysis import StaticMaterialAnalysisProvider


def material() -> NormalizedMaterial:
    return NormalizedMaterial(
        material_id="material:abc",
        filename="notes.txt",
        source=MaterialSource.USER_NOTE,
        format=MaterialFormat.TEXT,
        content_type="text/plain",
        sha256="a" * 64,
        size_bytes=20,
        text="राजस्थान का क्षेत्रफल 342239 वर्ग किमी है।",
        extraction_method="DIRECT_TEXT",
        storage_key="/tmp/material",
    )


def test_material_analysis_returns_understanding_concepts_and_facts():
    item = material()
    understanding = ContentUnderstanding(
        material_id=item.material_id,
        language="hi",
        summary="राजस्थान के क्षेत्रफल से संबंधित नोट",
        key_points=("राजस्थान का क्षेत्रफल",),
        subject_hints=("Geography",),
        topic_hints=("Rajasthan Geography",),
        confidence=0.95,
    )
    concept = ProposedConcept(
        concept_candidate_id="concept-candidate-1",
        material_id=item.material_id,
        label="राजस्थान का क्षेत्रफल",
        subject="Geography",
        topic="Rajasthan Geography",
        subtopic="Area",
        evidence_text="राजस्थान का क्षेत्रफल 342239 वर्ग किमी है।",
        confidence=0.9,
    )
    fact = ImportantFact(
        fact_id="fact-1",
        material_id=item.material_id,
        fact_text="राजस्थान का क्षेत्रफल 342239 वर्ग किमी है।",
        evidence_text="राजस्थान का क्षेत्रफल 342239 वर्ग किमी है।",
        importance_score=0.95,
        confidence=0.98,
        fact_type="STATISTIC",
    )

    result = StaticMaterialAnalysisProvider(
        understanding=understanding,
        concepts=(concept,),
        facts=(fact,),
    ).analyze(item)

    assert result.material_id == item.material_id
    assert result.understanding.summary
    assert result.concepts[0].label == "राजस्थान का क्षेत्रफल"
    assert result.facts[0].importance_score == 0.95
    assert result.warnings == ()


def test_static_provider_is_exposed_through_pipeline():
    item = material()
    understanding = ContentUnderstanding(
        material_id=item.material_id,
        language="hi",
        summary="summary",
        key_points=(),
        subject_hints=(),
        topic_hints=(),
        confidence=0.8,
    )

    result = StaticMaterialAnalysisProvider(
        understanding=understanding
    ).analyze(item)

    assert result.concepts == ()
    assert result.facts == ()
    assert result.warnings == (
        "no concepts were extracted",
        "no important facts were extracted",
    )


def test_analysis_rejects_hallucinated_concept_evidence():
    item = material()
    understanding = ContentUnderstanding(
        material_id=item.material_id,
        language="hi",
        summary="summary",
        key_points=(),
        subject_hints=(),
        topic_hints=(),
        confidence=0.8,
    )
    bad_concept = ProposedConcept(
        concept_candidate_id="concept-candidate-1",
        material_id=item.material_id,
        label="भारत का सर्वोच्च पर्वत",
        subject="Geography",
        topic=None,
        subtopic=None,
        evidence_text="यह वाक्य material में नहीं है",
        confidence=0.8,
    )

    with pytest.raises(
        ValueError,
        match="concept evidence_text must be grounded",
    ):
        StaticMaterialAnalysisProvider(
            understanding=understanding,
            concepts=(bad_concept,),
        ).analyze(item)


def test_analysis_rejects_fact_for_different_material():
    item = material()
    understanding = ContentUnderstanding(
        material_id=item.material_id,
        language="hi",
        summary="summary",
        key_points=(),
        subject_hints=(),
        topic_hints=(),
        confidence=0.8,
    )
    bad_fact = ImportantFact(
        fact_id="fact-1",
        material_id="material:other",
        fact_text="दूसरा तथ्य",
        evidence_text="राजस्थान का क्षेत्रफल 342239 वर्ग किमी है।",
        importance_score=0.5,
        confidence=0.5,
    )

    with pytest.raises(
        ValueError,
        match="fact material_id does not match",
    ):
        StaticMaterialAnalysisProvider(
            understanding=understanding,
            facts=(bad_fact,),
        ).analyze(item)
