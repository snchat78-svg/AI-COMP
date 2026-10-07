from ai_comp.domain.history import ExamAppearance


def appearance_identity(appearance: ExamAppearance) -> tuple[str, int, str | None, int]:
    """Identity of an exam occurrence, independent of copied web sources."""
    return (
        appearance.exam_id,
        appearance.year,
        appearance.shift,
        appearance.question_number,
    )


class AppearanceDeduplicator:
    """Prevents the same exam occurrence from being counted twice."""

    def __init__(self) -> None:
        self._identities: set[tuple[str, int, str | None, int]] = set()

    def seen(self, appearance: ExamAppearance) -> bool:
        identity = appearance_identity(appearance)
        if identity in self._identities:
            return True
        self._identities.add(identity)
        return False
