import pytest

from ai_comp.master.policy import MasterAssignmentPolicy


def test_master_policy_defaults_are_conservative():
    policy = MasterAssignmentPolicy()
    assert policy.min_rephrased_confidence == 0.90
    assert policy.min_confidence_margin == 0.05


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_rephrased_confidence": -0.01},
        {"min_rephrased_confidence": 1.01},
        {"min_confidence_margin": -0.01},
        {"min_confidence_margin": 1.01},
    ],
)
def test_master_policy_rejects_invalid_thresholds(kwargs):
    with pytest.raises(ValueError):
        MasterAssignmentPolicy(**kwargs)
