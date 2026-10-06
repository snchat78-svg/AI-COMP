from __future__ import annotations

import hashlib
from typing import Any, Sequence

from pydantic import BaseModel, ConfigDict, Field

from ai_comp.domain.material_analysis import ImportantFact, ProposedConcept
from ai_comp.domain.material_generation import (
    AnswerVerificationResult,
    AnswerVerificationStatus,
    GeneratedMCQ,
    GeneratedOption,
    GenerationSpecification,
)
from ai_comp.material.gemini import GeminiMaterialAnalysisConfig, GeminiMaterialAnalysisError


class _GeneratedOption(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    key: str = Field(min_length=1, max_length=2)
    text: str = Field(min_length=1)


class _GeneratedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    stem: str = Field(min_length=10)
    options: list[_GeneratedOption]
    correct_option_key: str = Field(min_length=1, max_length=2)
    explanation: str = Field(min_length=1)
    fact_ids: list[str]
    concept_ids: list[str]
    difficulty: str = Field(min_length=1)
    importance_score: float = Field(ge=0.0, le=1.0)
    quality_score: float = Field(ge=0.0, le=1.0)


class _GeneratedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    questions: list[_GeneratedQuestion]


class _AnswerVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    status: str
    evidence: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class GeminiQuestionGenerationError(RuntimeError):
    pass


class GeminiQuestionGenerationProvider:
    def __init__(self, config: GeminiMaterialAnalysisConfig | None = None, *, client: Any | None = None):
        self.config = config or GeminiMaterialAnalysisConfig()
        self._client = client if client is not None else self._build_client()

    def generate(self, specification, facts, concepts):
        fact_payload = [
            {
                "fact_id": fact.fact_id,
                "fact_text": fact.fact_text,
                "evidence_text": fact.evidence_text,
                "importance_score": fact.importance_score,
                "confidence": fact.confidence,
            }
            for fact in facts
        ]
        concept_payload = [
            {
                "concept_id": concept.concept_candidate_id,
                "label": concept.label,
                "subject": concept.subject,
                "topic": concept.topic,
                "subtopic": concept.subtopic,
            }
            for concept in concepts
        ]
        prompt = (
            "Generate exam-quality MCQs only from the supplied facts/concepts. "
            "Do not use outside knowledge. Never claim a generated question was "
            "asked in an exam. Return exactly the requested count unless the "
            "evidence is insufficient.\n"
            f"specification={specification!r}\n"
            f"facts={fact_payload!r}\n"
            f"concepts={concept_payload!r}"
        )
        try:
            response = self._client.models.generate_content(
                model=self.config.model,
                contents=prompt,
                config={
                    "system_instruction": (
                        "You are a conservative exam-question generator. "
                        "Every generated question must be answerable from the "
                        "supplied source facts. Use exactly four options. "
                        "The correct option must be supported by a supplied fact. "
                        "Do not invent dates, numbers, names, or historical claims. "
                        "Return only structured JSON."
                    ),
                    "response_mime_type": "application/json",
                    "response_schema": _GeneratedResponse,
                    "thinking_config": {"thinking_level": self.config.thinking_level},
                    "max_output_tokens": self.config.max_output_tokens,
                },
            )
        except Exception as exc:
            raise GeminiQuestionGenerationError(
                f"Gemini generation failed: {type(exc).__name__}"
            ) from exc
        try:
            parsed = getattr(response, "parsed", None)
            if isinstance(parsed, _GeneratedResponse):
                result = parsed
            elif isinstance(parsed, dict):
                result = _GeneratedResponse.model_validate(parsed)
            else:
                result = _GeneratedResponse.model_validate_json(response.text)
        except Exception as exc:
            raise GeminiQuestionGenerationError(
                "Gemini generated malformed question schema"
            ) from exc

        output = []
        for item in result.questions:
            output.append(
                GeneratedMCQ(
                    generated_question_id=self._id(specification.generation_id, item.stem),
                    generation_id=specification.generation_id,
                    material_id=specification.material_id,
                    stem=item.stem,
                    options=tuple(
                        GeneratedOption(key=o.key.upper(), text=o.text)
                        for o in item.options
                    ),
                    correct_option_key=item.correct_option_key.upper(),
                    explanation=item.explanation,
                    fact_ids=tuple(item.fact_ids),
                    concept_ids=tuple(item.concept_ids),
                    difficulty=item.difficulty,
                    importance_score=item.importance_score,
                    quality_score=item.quality_score,
                )
            )
        return tuple(output)

    def _build_client(self):
        try:
            from google import genai
            return genai.Client(api_key=__import__("os").environ[self.config.api_key_env])
        except Exception as exc:
            raise GeminiQuestionGenerationError(
                f"Gemini client initialization failed: {type(exc).__name__}"
            ) from exc

    @staticmethod
    def _id(generation_id, stem):
        return "generated:" + hashlib.sha256(
            f"{generation_id}|{stem}".encode("utf-8")
        ).hexdigest()[:24]


class GeminiAnswerVerifier:
    def __init__(self, config: GeminiMaterialAnalysisConfig | None = None, *, client: Any | None = None):
        self.config = config or GeminiMaterialAnalysisConfig()
        self._client = client if client is not None else GeminiQuestionGenerationProvider(self.config)._build_client()

    def verify(self, question, facts, concepts):
        prompt = (
            "Verify the proposed correct answer using ONLY supplied facts. "
            "Do not use outside knowledge. If evidence is insufficient, return "
            "UNCERTAIN. VERIFIED requires exact supporting evidence.\n"
            f"question={question!r}\n"
            f"facts={[fact.fact_text for fact in facts]!r}\n"
        )
        try:
            response = self._client.models.generate_content(
                model=self.config.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": _AnswerVerification,
                    "thinking_config": {"thinking_level": self.config.thinking_level},
                    "max_output_tokens": 2000,
                },
            )
            parsed = getattr(response, "parsed", None)
            if isinstance(parsed, _AnswerVerification):
                result = parsed
            elif isinstance(parsed, dict):
                result = _AnswerVerification.model_validate(parsed)
            else:
                result = _AnswerVerification.model_validate_json(response.text)
        except Exception as exc:
            raise GeminiQuestionGenerationError(
                f"Gemini answer verification failed: {type(exc).__name__}"
            ) from exc

        try:
            status = AnswerVerificationStatus(result.status.upper())
        except ValueError as exc:
            raise GeminiQuestionGenerationError("invalid answer verification status") from exc
        return AnswerVerificationResult(
            status=status,
            evidence=tuple(result.evidence),
            confidence=result.confidence,
        )
