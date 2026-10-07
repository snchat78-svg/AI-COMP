import pytest

from ai_comp.domain.exams import ConductingBody, Exam, ExamLevel
from ai_comp.domain.sources import SourcePriority, SourceRecord, SourceType
from ai_comp.research.seed_registry import build_initial_registry
from ai_comp.research.source_registry import RegistryError, SourceRegistry


def test_exam_requires_known_conducting_body():
    registry = SourceRegistry()
    with pytest.raises(RegistryError):
        registry.add_exam(Exam("E1", "Exam", "UNKNOWN", ExamLevel.STATE))


def test_registry_rejects_duplicate_ids():
    registry = SourceRegistry()
    body = ConductingBody("B1", "Body", ExamLevel.STATE)
    registry.add_body(body)
    with pytest.raises(RegistryError):
        registry.add_body(body)


def test_seed_registry_contains_rajasthan_official_sources():
    registry = build_initial_registry()
    source_ids = {source.source_id for source in registry.sources()}
    assert {"RSSB_OFFICIAL", "RPSC_OFFICIAL"} <= source_ids
    assert all(source.priority is SourcePriority.OFFICIAL for source in registry.sources())


def test_unverified_source_is_not_official():
    source = SourceRecord(
        "S1", "Unknown", "https://example.invalid",
        SourceType.UNVERIFIED, SourcePriority.UNVERIFIED
    )
    assert source.priority is SourcePriority.UNVERIFIED
