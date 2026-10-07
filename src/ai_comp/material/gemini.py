from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from threading import RLock
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from ai_comp.domain.material_analysis import (
    ContentUnderstanding,
    ImportantFact,
    ProposedConcept,
)
from ai_comp.domain.materials import NormalizedMaterial


class GeminiMaterialAnalysisError(RuntimeError):
    """Raised when the Gemini provider cannot produce a trusted result."""


@dataclass(frozen=True)
class GeminiMaterialAnalysisConfig:
    """Runtime configuration for the real Gemini material-analysis provider."""

    api_key_env: str = "GEMINI_API_KEY"
    model: str = "gemini-3.8-flash"
    thinking_level: str = "high"
    max_output_tokens: int = 12000
    max_material_characters: int = 2_000_000
    schema_version: str = "phase6.3.v1"

    def __post_init__(self) -> None:
        if not self.api_key_env.strip():
            raise ValueError("api_key_env must not be empty")
        if not self.model.strip():
            raise ValueError("model must not be empty")
        if self.thinking_level not in {"low", "medium", "high"}:
            raise ValueError("thinking_level must be low, medium, or high")
        if self.max_output_tokens < 256:
            raise ValueError("max_output_tokens must be at least 256")
        if self.max_material_characters < 1_000:
            raise ValueError("max_material_characters must be at least 1000")
        if not self.schema_version.strip():
            raise ValueError("schema_version must not be empty")


class _GeminiConcept(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    label: str = Field(min_length=1)
    subject: str | None = None
    topic: str | None = None
    subtopic: str | None = None
    evidence_text: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class _GeminiFact(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    fact_text: str = Field(min_length=1)
    evidence_text: str = Field(min_length=1)
    importance_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    fact_type: str = Field(default="GENERAL", min_length=1)


class _GeminiMaterialAnalysis(BaseModel):
    """Closed-world structured response expected from Gemini."""

    model_config = ConfigDict(extra="forbid", strict=True)

    language: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    key_points: list[str]
    subject_hints: list[str]
    topic_hints: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    concepts: list[_GeminiConcept]
    facts: list[_GeminiFact]


_SYSTEM_INSTRUCTION = """
You are the material-analysis component of an exam-preparation system.

Use ONLY the supplied material as evidence. Do not use outside knowledge, memory,
web knowledge, or assumptions to add facts.

Your tasks:
1. Understand the supplied material and identify its language, concise summary,
   key points, subject hints, and topic hints.
2. Extract useful concepts that are explicitly supported by the material.
3. Extract important facts that are explicitly supported by the material.

Grounding rules:
- Every concept evidence_text MUST be copied exactly and contiguously from the
  supplied material.
- Every fact evidence_text MUST be copied exactly and contiguously from the
  supplied material.
- Do not invent, repair, extrapolate, calculate, or silently correct facts.
- When the material is unclear, omit the item rather than guessing.
- Confidence expresses confidence in the extraction, not truth beyond the source.
- importance_score expresses exam/study importance based only on the material's
  content and explicit emphasis; it is not proof that an item appeared in an exam.
- Keep extracted items focused on exam-relevant information.
- Do not create previous-exam claims, exam appearances, official-source claims,
  answer keys, or historical evidence.

Return only the requested structured response.
""".strip()


class GeminiMaterialAnalysisProvider:
    """Provider-neutral contract implemented with the current Google Gen AI SDK.

    The provider performs one model call per material and caches that single
    structured response for the three protocol operations used by the pipeline.
    """

    provider_name = "google-gemini"

    def __init__(
        self,
        config: GeminiMaterialAnalysisConfig | None = None,
        *,
        client: Any | None = None,
    ) -> None:
        self.config = config or GeminiMaterialAnalysisConfig()
        self._client = client if client is not None else self._build_client()
        self._cache: dict[str, _GeminiMaterialAnalysis] = {}
        self._lock = RLock()

    def understand(self, material: NormalizedMaterial) -> ContentUnderstanding:
        result = self._analysis_for(material)
        return ContentUnderstanding(
            material_id=material.material_id,
            language=result.language,
            summary=result.summary,
            key_points=tuple(result.key_points),
            subject_hints=tuple(result.subject_hints),
            topic_hints=tuple(result.topic_hints),
            confidence=result.confidence,
        )

    def extract_concepts(
        self,
        material: NormalizedMaterial,
        understanding: ContentUnderstanding,
    ) -> tuple[ProposedConcept, ...]:
        del understanding
        result = self._analysis_for(material)
        items: list[ProposedConcept] = []
        seen: set[tuple[str, str]] = set()

        for item in result.concepts:
            key = (item.label, item.evidence_text)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                ProposedConcept(
                    concept_candidate_id=self._stable_id(
                        "concept",
                        material.material_id,
                        item.label,
                        item.evidence_text,
                    ),
                    material_id=material.material_id,
                    label=item.label,
                    subject=item.subject,
                    topic=item.topic,
                    subtopic=item.subtopic,
                    evidence_text=item.evidence_text,
                    confidence=item.confidence,
                )
            )

        return tuple(items)

    def extract_facts(
        self,
        material: NormalizedMaterial,
        understanding: ContentUnderstanding,
        concepts: tuple[ProposedConcept, ...],
    ) -> tuple[ImportantFact, ...]:
        del understanding, concepts
        result = self._analysis_for(material)
        items: list[ImportantFact] = []
        seen: set[tuple[str, str]] = set()

        for item in result.facts:
            key = (item.fact_text, item.evidence_text)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                ImportantFact(
                    fact_id=self._stable_id(
                        "fact",
                        material.material_id,
                        item.fact_text,
                        item.evidence_text,
                    ),
                    material_id=material.material_id,
                    fact_text=item.fact_text,
                    evidence_text=item.evidence_text,
                    importance_score=item.importance_score,
                    confidence=item.confidence,
                    fact_type=item.fact_type,
                )
            )

        return tuple(items)

    def _analysis_for(self, material: NormalizedMaterial) -> _GeminiMaterialAnalysis:
        if not material.text.strip():
            raise GeminiMaterialAnalysisError("material text is empty")

        if len(material.text) > self.config.max_material_characters:
            raise GeminiMaterialAnalysisError(
                "material exceeds max_material_characters; "
                "material was not truncated"
            )

        cache_key = f"{material.material_id}:{material.sha256}"
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        prompt = (
            "Analyze the following study material. Preserve source wording in "
            "all evidence_text fields.\n\n"
            "<material>\n"
            f"{material.text}"
            "\n</material>"
        )

        try:
            response = self._client.models.generate_content(
                model=self.config.model,
                contents=prompt,
                config={
                    "system_instruction": _SYSTEM_INSTRUCTION,
                    "response_mime_type": "application/json",
                    "response_schema": _GeminiMaterialAnalysis,
                    "thinking_config": {
                        "thinking_level": self.config.thinking_level
                    },
                    "max_output_tokens": self.config.max_output_tokens,
                },
            )
        except Exception as exc:
            raise GeminiMaterialAnalysisError(
                f"Gemini request failed: {type(exc).__name__}"
            ) from exc

        parsed = getattr(response, "parsed", None)
        try:
            if isinstance(parsed, _GeminiMaterialAnalysis):
                result = parsed
            elif isinstance(parsed, Mapping):
                result = _GeminiMaterialAnalysis.model_validate(parsed)
            else:
                raw_text = getattr(response, "text", None)
                if not isinstance(raw_text, str) or not raw_text.strip():
                    raise GeminiMaterialAnalysisError(
                        "Gemini returned no structured result"
                    )
                result = _GeminiMaterialAnalysis.model_validate_json(raw_text)
        except GeminiMaterialAnalysisError:
            raise
        except Exception as exc:
            raise GeminiMaterialAnalysisError(
                "Gemini returned malformed structured output"
            ) from exc

        self._validate_source_grounding(material, result)

        with self._lock:
            self._cache[cache_key] = result
        return result

    @staticmethod
    def _validate_source_grounding(
        material: NormalizedMaterial,
        result: _GeminiMaterialAnalysis,
    ) -> None:
        for concept in result.concepts:
            if concept.evidence_text not in material.text:
                raise GeminiMaterialAnalysisError(
                    "Gemini concept evidence is not an exact source substring"
                )

        for fact in result.facts:
            if fact.evidence_text not in material.text:
                raise GeminiMaterialAnalysisError(
                    "Gemini fact evidence is not an exact source substring"
                )

    def _build_client(self) -> Any:
        api_key = os.getenv(self.config.api_key_env)
        if not api_key or not api_key.strip():
            raise GeminiMaterialAnalysisError(
                f"Gemini API key is missing in environment variable "
                f"{self.config.api_key_env}"
            )

        try:
            from google import genai
        except ImportError as exc:
            raise GeminiMaterialAnalysisError(
                "google-genai package is not installed"
            ) from exc

        try:
            return genai.Client(api_key=api_key)
        except Exception as exc:
            raise GeminiMaterialAnalysisError(
                f"Gemini client initialization failed: {type(exc).__name__}"
            ) from exc

    @staticmethod
    def _stable_id(prefix: str, material_id: str, text: str, evidence: str) -> str:
        digest = hashlib.sha256(
            f"{material_id}|{text}|{evidence}".encode("utf-8")
        ).hexdigest()[:24]
        return f"{prefix}:{digest}"
