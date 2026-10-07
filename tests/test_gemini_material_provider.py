from __future__ import annotations

from types import SimpleNamespace

import pytest

from ai_comp.domain.materials import (
    MaterialFormat,
    MaterialSource,
    NormalizedMaterial,
)
from ai_comp.material.gemini import (
    GeminiMaterialAnalysisConfig,
    GeminiMaterialAnalysisError,
    GeminiMaterialAnalysisProvider,
    _GeminiMaterialAnalysis,
)


TEXT = (
    "राजस्थान का क्षेत्रफल 342239 वर्ग किमी है। "
    "राजधानी जयपुर है। यह तथ्य परीक्षा की दृष्टि से महत्वपूर्ण है।"
)


def material() -> NormalizedMaterial:
    return NormalizedMaterial(
        material_id="material:test",
        filename="notes.txt",
        source=MaterialSource.USER_NOTE,
        format=MaterialFormat.TEXT,
        content_type="text/plain",
        sha256="b" * 64,
        size_bytes=len(TEXT.encode("utf-8")),
        text=TEXT,
        extraction_method="DIRECT_TEXT",
        storage_key="/tmp/material",
    )


class FakeModels:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[dict] = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response: object) -> None:
        self.models = FakeModels(response)


def structured_response() -> _GeminiMaterialAnalysis:
    return _GeminiMaterialAnalysis(
        language="hi",
        summary="राजस्थान के सामान्य ज्ञान से संबंधित सामग्री",
        key_points=["क्षेत्रफल", "राजधानी"],
        subject_hints=["Geography", "General Knowledge"],
        topic_hints=["Rajasthan"],
        confidence=0.97,
        concepts=[
            {
                "label": "राजस्थान का क्षेत्रफल",
                "subject": "Geography",
                "topic": "Rajasthan",
                "subtopic": "Area",
                "evidence_text": "राजस्थान का क्षेत्रफल 342239 वर्ग किमी है।",
                "confidence": 0.96,
            }
        ],
        facts=[
            {
                "fact_text": "राजधानी जयपुर है।",
                "evidence_text": "राजधानी जयपुर है।",
                "importance_score": 0.93,
                "confidence": 0.98,
                "fact_type": "STATIC_FACT",
            }
        ],
    )


def test_gemini_provider_uses_one_structured_call_for_full_pipeline():
    response = SimpleNamespace(parsed=structured_response(), text="")
    client = FakeClient(response)
    provider = GeminiMaterialAnalysisProvider(
        GeminiMaterialAnalysisConfig(max_material_characters=100_000),
        client=client,
    )

    understanding = provider.understand(material())
    concepts = provider.extract_concepts(material(), understanding)
    facts = provider.extract_facts(material(), understanding, concepts)

    assert len(client.models.calls) == 1
    request = client.models.calls[0]
    assert request["model"] == "gemini-3.8-flash"
    assert request["config"]["response_mime_type"] == "application/json"
    assert request["config"]["response_schema"] is _GeminiMaterialAnalysis
    assert request["config"]["thinking_config"]["thinking_level"] == "high"
    assert concepts[0].label == "राजस्थान का क्षेत्रफल"
    assert facts[0].fact_text == "राजधानी जयपुर है।"
    assert concepts[0].concept_candidate_id.startswith("concept:")
    assert facts[0].fact_id.startswith("fact:")


def test_gemini_provider_reuses_structured_result_without_second_request():
    response = SimpleNamespace(parsed=structured_response(), text="")
    client = FakeClient(response)
    provider = GeminiMaterialAnalysisProvider(client=client)

    first = provider.understand(material())
    second = provider.understand(material())

    assert first == second
    assert len(client.models.calls) == 1


def test_gemini_provider_rejects_non_grounded_evidence():
    result = _GeminiMaterialAnalysis(
        language="hi",
        summary="summary",
        key_points=[],
        subject_hints=[],
        topic_hints=[],
        confidence=0.8,
        concepts=[
            {
                "label": "असमर्थित",
                "subject": None,
                "topic": None,
                "subtopic": None,
                "evidence_text": "यह सामग्री में नहीं है",
                "confidence": 0.8,
            }
        ],
        facts=[],
    )
    client = FakeClient(SimpleNamespace(parsed=result, text=""))
    provider = GeminiMaterialAnalysisProvider(client=client)

    with pytest.raises(
        GeminiMaterialAnalysisError,
        match="exact source substring",
    ):
        provider.understand(material())


def test_gemini_provider_rejects_malformed_output():
    client = FakeClient(
        SimpleNamespace(
            parsed=None,
            text='{"language": "hi", "broken": true}',
        )
    )
    provider = GeminiMaterialAnalysisProvider(client=client)

    with pytest.raises(
        GeminiMaterialAnalysisError,
        match="malformed structured output",
    ):
        provider.understand(material())


def test_gemini_provider_rejects_oversized_material_without_calling_model():
    response = SimpleNamespace(parsed=structured_response(), text="")
    client = FakeClient(response)
    provider = GeminiMaterialAnalysisProvider(
        GeminiMaterialAnalysisConfig(max_material_characters=1000),
        client=client,
    )

    oversized = NormalizedMaterial(
        material_id="material:large",
        filename="large.txt",
        source=MaterialSource.USER_NOTE,
        format=MaterialFormat.TEXT,
        content_type="text/plain",
        sha256="c" * 64,
        size_bytes=2000,
        text="x" * 1001,
        extraction_method="DIRECT_TEXT",
        storage_key="/tmp/large-material",
    )

    with pytest.raises(
        GeminiMaterialAnalysisError,
        match="material exceeds max_material_characters",
    ):
        provider.understand(oversized)

    assert client.models.calls == []


def test_config_validates_thinking_level():
    with pytest.raises(ValueError, match="thinking_level"):
        GeminiMaterialAnalysisConfig(thinking_level="minimal")
