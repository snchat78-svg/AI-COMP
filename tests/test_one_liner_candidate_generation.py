from __future__ import annotations

from dataclasses import replace

import pytest

from ai_comp.application.one_liner_candidate_generation import (
    OneLinerCandidateGenerationService,
    OneLinerDraft,
)
from ai_comp.domain.topic_question_bank import (
    OneLinerVerificationStatus,
    TopicOneLinerQA,
)
from ai_comp.material.gemini_one_liner_generation import (
    GeminiOneLinerGenerationError,
    GeminiOneLinerGenerationProvider,
)


SOURCE = (
    "The Luni River is the largest river system in the Thar Desert region. "
    "It flows southwest and drains into the Rann of Kutch."
)
SOURCE_URL = "https://example.gov.in/rajasthan-geography"
LOCATOR = "Rajasthan geography reference, heading: Rivers"


class _Provider:
    def __init__(self, drafts):
        self.drafts = drafts
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.drafts


class _Repository:
    def __init__(self, duplicate=False, existing_items=None):
        self.items = []
        self.duplicate = duplicate
        self.existing_items = list(existing_items or [])
        self.list_calls = []

    def list_one_liners(
        self, concept_id, *, limit=100, offset=0, verified_only=True, language_code=None
    ):
        self.list_calls.append((concept_id, limit, offset, verified_only, language_code))
        selected = [
            item for item in self.existing_items
            if item.concept_id == concept_id
            and (language_code is None or item.language_code == language_code)
        ]
        return tuple(selected[offset:offset + limit])

    def save_one_liner(self, item):
        if self.duplicate:
            return replace(item, one_liner_id="existing-id")
        self.items.append(item)
        return item


def _draft(
    question="Which river system is the largest in the Thar Desert region?",
    answer="The Luni River system.",
    evidence=SOURCE,
    answer_evidence="The Luni River is the largest river system in the Thar Desert region.",
    importance=0.95,
    coverage_dimension="FACTUAL_DETAIL",
):
    return OneLinerDraft(
        question_text=question,
        answer_text=answer,
        evidence_quote=evidence,
        answer_evidence_quote=answer_evidence,
        importance_score=importance,
        coverage_dimension=coverage_dimension,
    )


def _service(provider, repository, **kwargs):
    return OneLinerCandidateGenerationService(provider, repository, **kwargs)


def _generate(service, **kwargs):
    return service.generate(
        concept_id="catalog.rajasthan_geography_rivers_and_drainage_luni_river",
        concept_label="Luni River",
        source_url=SOURCE_URL,
        source_locator=LOCATOR,
        source_text=SOURCE,
        language_code="hi",
        requested_count=10,
        **kwargs,
    )


def test_candidates_are_saved_as_needs_review_and_never_verified():
    provider = _Provider([_draft()])
    repository = _Repository()

    result = _generate(_service(provider, repository))

    assert result.saved_count == 1
    item = repository.items[0]
    assert item.verification_status is OneLinerVerificationStatus.NEEDS_REVIEW
    assert item.reviewed_at is None
    assert item.source_url == SOURCE_URL
    assert LOCATOR in item.source_evidence
    assert "coverage_dimension=FACTUAL_DETAIL" in item.source_evidence
    assert _draft().evidence_quote in item.source_evidence
    assert item.importance_score == 0.95
    assert item.coverage_dimension == "FACTUAL_DETAIL"
    assert provider.calls[0]["concept_label"] == "Luni River"


def test_importance_ranking_and_minimum_threshold_are_applied():
    low = _draft(question="Low priority question?", importance=0.2)
    high = _draft(
        question="Higher priority question?",
        answer="Luni River.",
        importance=0.99,
    )
    provider = _Provider([low, high])
    repository = _Repository()

    result = _generate(_service(provider, repository))

    assert result.saved_count == 1
    assert repository.items[0].question_text == "Higher priority question?"
    assert result.rejected_count == 1
    assert repository.items[0].importance_score == 0.99


def test_candidate_requires_exact_contiguous_source_and_answer_evidence():
    bad = _draft(
        evidence="The Luni River is a major river.",
        answer_evidence="The Luni River is a major river.",
    )
    repository = _Repository()

    result = _generate(_service(_Provider([bad]), repository))

    assert result.saved_count == 0
    assert result.rejected_count == 1
    assert repository.items == []
    assert any("exact, contiguous" in warning for warning in result.warnings)


def test_answer_evidence_must_be_contained_in_full_evidence_quote():
    bad = _draft(
        evidence="The Luni River is the largest river system in the Thar Desert region.",
        answer_evidence="It flows southwest and drains into the Rann of Kutch.",
    )
    repository = _Repository()

    result = _generate(_service(_Provider([bad]), repository))

    assert result.saved_count == 0
    assert result.rejected_count == 1
    assert repository.items == []


def test_candidate_coverage_dimension_is_preserved_for_reviewer():
    draft = _draft(coverage_dimension="PLACE_LOCATION")
    repository = _Repository()

    result = _generate(_service(_Provider([draft]), repository))

    assert result.saved_count == 1
    assert "coverage_dimension=PLACE_LOCATION" in repository.items[0].source_evidence
    assert result.coverage_dimension_counts == {"PLACE_LOCATION": 1}
    assert repository.items[0].coverage_dimension == "PLACE_LOCATION"
    assert repository.items[0].verification_status is OneLinerVerificationStatus.NEEDS_REVIEW


def test_unsupported_coverage_dimension_is_rejected():
    with pytest.raises(ValueError, match="coverage_dimension"):
        _draft(coverage_dimension="TOPIC_COMPLETE")


def test_duplicate_drafts_in_same_batch_are_removed_by_normalized_hash():
    first = _draft(question="Which river system is largest?", answer="Luni River.")
    second = _draft(question="Which river   system is largest?", answer="Luni River.")
    repository = _Repository()

    result = _generate(_service(_Provider([first, second]), repository))

    assert result.saved_count == 1
    assert result.duplicate_count == 1
    assert len(repository.items) == 1


def test_database_duplicate_is_counted_without_replacing_existing_item():
    result = _generate(_service(_Provider([_draft()]), _Repository(duplicate=True)))

    assert result.saved_count == 0
    assert result.duplicate_count == 1


def test_invalid_provider_shapes_are_rejected_before_priority_sorting():
    provider = _Provider([object(), _draft()])
    repository = _Repository()

    result = _generate(_service(provider, repository))

    assert result.saved_count == 1
    assert result.rejected_count == 1
    assert repository.items[0].verification_status is OneLinerVerificationStatus.NEEDS_REVIEW


@pytest.mark.parametrize(
    "source_url",
    [
        "http://example.gov.in/facts",
        "https://",
        "https://user:password@example.gov.in/facts",
    ],
)
def test_source_url_must_be_absolute_https_without_userinfo(source_url):
    service = _service(_Provider([_draft()]), _Repository())
    with pytest.raises(ValueError, match="absolute HTTPS"):
        service.generate(
            concept_id="concept-rivers",
            concept_label="Rivers",
            source_url=source_url,
            source_locator=LOCATOR,
            source_text=SOURCE,
        )


def test_source_excerpt_size_and_requested_count_are_bounded():
    service = _service(
        _Provider([_draft()]),
        _Repository(),
        maximum_source_characters=60,
    )
    with pytest.raises(ValueError, match="character limit"):
        _generate(service)

    service = _service(_Provider([_draft()]), _Repository())
    with pytest.raises(ValueError, match="between 1 and 50"):
        service.generate(
            concept_id="concept-rivers",
            concept_label="Rivers",
            source_url=SOURCE_URL,
            source_locator=LOCATOR,
            source_text=SOURCE,
            requested_count=51,
        )


@pytest.mark.parametrize(
    "question,answer",
    [
        ("Which river is largest in the Thar Desert? Where does it drain?", "Luni River."),
        ("Which river is largest in the Thar Desert?", "Luni River.\nIt flows southwest."),
        ("Which river is largest in the Thar Desert?", "A" * 241),
        ("Which river is largest in the Thar Desert?\nName its basin?", "Luni River."),
    ],
)
def test_candidates_must_be_one_concise_question_and_one_line_answer(question, answer):
    repository = _Repository()
    result = _generate(_service(_Provider([_draft(question=question, answer=answer)]), repository))

    assert result.saved_count == 0
    assert result.rejected_count == 1
    assert repository.items == []
    assert any("single-question, concise" in warning for warning in result.warnings)


def test_hindi_one_liner_question_and_concise_answer_are_accepted():
    draft = _draft(
        question="लूणी नदी किस क्षेत्र की सबसे बड़ी नदी प्रणाली है?",
        answer="थार मरुस्थल क्षेत्र की।",
    )
    repository = _Repository()
    result = _generate(_service(_Provider([draft]), repository))

    assert result.saved_count == 1
    assert repository.items[0].question_text == draft.question_text
    assert repository.items[0].answer_text == draft.answer_text
    assert repository.items[0].verification_status is OneLinerVerificationStatus.NEEDS_REVIEW


class _FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class _FakeClient:
    def __init__(self, models):
        self.models = models


class _FakeResponse:
    def __init__(self, parsed):
        self.parsed = parsed
        self.text = None


def test_gemini_provider_returns_strict_structured_source_quotes():
    batch = {
        "items": [
            {
                "question_text": "लूणी नदी किस मरुस्थलीय क्षेत्र की प्रमुख नदी प्रणाली है?",
                "answer_text": "थार मरुस्थल क्षेत्र की।",
                "evidence_quote": SOURCE,
                "answer_evidence_quote": "The Luni River is the largest river system in the Thar Desert region.",
                "importance_score": 0.95,
                "coverage_dimension": "PLACE_LOCATION",
            }
        ]
    }
    models = _FakeModels(response=_FakeResponse(batch))
    provider = GeminiOneLinerGenerationProvider(
        model="test-model",
        client=_FakeClient(models),
    )

    result = provider.generate(
        source_text=SOURCE,
        concept_label="Luni River",
        language_code="hi",
        requested_count=5,
    )

    assert len(result) == 1
    assert result[0].question_text.startswith("लूणी नदी")
    assert result[0].answer_evidence_quote in result[0].evidence_quote
    assert result[0].coverage_dimension == "PLACE_LOCATION"
    assert models.calls[0]["model"] == "test-model"
    assert "Return only structured JSON" in models.calls[0]["config"]["system_instruction"]


def test_gemini_provider_wraps_provider_failures_without_exposing_secrets():
    provider = GeminiOneLinerGenerationProvider(
        model="test-model",
        client=_FakeClient(_FakeModels(error=RuntimeError("private provider detail"))),
    )

    with pytest.raises(GeminiOneLinerGenerationError, match="RuntimeError") as error:
        provider.generate(
            source_text=SOURCE,
            concept_label="Luni River",
            language_code="hi",
            requested_count=5,
        )
    assert "private provider detail" not in str(error.value)


def _existing_item(
    *,
    question="Which river system is the largest in the Thar Desert region?",
    answer="The Luni River system.",
    concept_id="catalog.rajasthan_geography_rivers_and_drainage_luni_river",
    language_code="hi",
):
    return TopicOneLinerQA(
        one_liner_id="existing-one-liner",
        concept_id=concept_id,
        question_text=question,
        answer_text=answer,
        language_code=language_code,
        source_url=SOURCE_URL,
        source_evidence=LOCATOR,
        verification_status=OneLinerVerificationStatus.NEEDS_REVIEW,
        importance_score=0.9,
    )


def test_near_duplicate_against_existing_topic_item_is_not_saved():
    repository = _Repository(existing_items=[_existing_item()])
    near_duplicate = _draft(
        question="Which is the largest river system in the Thar Desert region?",
        answer="The Luni River system.",
    )

    result = _generate(_service(_Provider([near_duplicate]), repository))

    assert result.saved_count == 0
    assert result.duplicate_count == 1
    assert repository.items == []
    assert repository.list_calls == [
        (
            "catalog.rajasthan_geography_rivers_and_drainage_luni_river",
            500,
            0,
            False,
            "hi",
        )
    ]


def test_near_duplicate_comparison_is_scoped_to_same_concept_and_language():
    repository = _Repository(
        existing_items=[
            _existing_item(concept_id="another-concept"),
            _existing_item(language_code="en"),
        ]
    )

    result = _generate(_service(_Provider([_draft()]), repository))

    assert result.saved_count == 1
    assert result.duplicate_count == 0


def test_same_batch_near_duplicates_are_removed_even_when_wording_varies():
    first = _draft(
        question="Which river system is largest in the Thar Desert region?",
        answer="The Luni River system.",
    )
    second = _draft(
        question="Which is the largest river system in the Thar Desert region?",
        answer="The Luni River system.",
    )
    repository = _Repository()

    result = _generate(_service(_Provider([first, second]), repository))

    assert result.saved_count == 1
    assert result.duplicate_count == 1
    assert len(repository.items) == 1


def test_batch_audit_separates_generated_rejected_duplicate_pending_and_verified():
    duplicate = _draft(
        question="Which is the largest river system in the Thar Desert region?",
        answer="The Luni River system.",
    )
    malformed = _draft(
        question="Which river is largest? Where does it drain?",
        answer="The Luni River system.",
    )
    repository = _Repository()
    result = _generate(_service(_Provider([_draft(), duplicate, malformed]), repository))

    assert result.generated_count == 3
    assert result.saved_count == 1
    assert result.rejected_count == 1
    assert result.duplicate_count == 1
    assert result.pending_review_count == 1
    assert result.verified_count == 0
    assert all(
        item.verification_status is OneLinerVerificationStatus.NEEDS_REVIEW
        for item in result.saved_items
    )


def test_duplicate_scan_failure_fails_closed_before_any_candidate_is_saved():
    class BrokenRepository(_Repository):
        def list_one_liners(self, *args, **kwargs):
            raise RuntimeError("database detail must not be exposed")

    repository = BrokenRepository()
    with pytest.raises(RuntimeError):
        _generate(_service(_Provider([_draft()]), repository))
    assert repository.items == []
