from ai_comp.database.models import RegistrySnapshot
from ai_comp.database.repository import RegistryRepository


def test_repository_contract_exposes_required_persistence_methods():
    required = {
        "save_body",
        "save_exam",
        "save_category",
        "save_source",
        "save_verification",
        "get_body",
        "get_exam",
        "get_category",
        "get_source",
        "get_verifications",
        "snapshot",
    }
    assert required.issubset(set(RegistryRepository.__dict__["__annotations__"]) or set())


def test_registry_snapshot_is_database_neutral():
    snapshot = RegistrySnapshot()
    assert snapshot.conducting_bodies == ()
    assert snapshot.sources == ()
    assert snapshot.verifications == ()
