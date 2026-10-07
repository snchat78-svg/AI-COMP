from dataclasses import dataclass


@dataclass(frozen=True)
class MasterAssignmentPolicy:
    """Safety thresholds for automatic master-question assignment."""

    min_rephrased_confidence: float = 0.90
    min_confidence_margin: float = 0.05

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_rephrased_confidence <= 1.0:
            raise ValueError("min_rephrased_confidence must be between 0 and 1")
        if not 0.0 <= self.min_confidence_margin <= 1.0:
            raise ValueError("min_confidence_margin must be between 0 and 1")
