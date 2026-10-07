from collections.abc import Iterable
from typing import Protocol

from ai_comp.domain.history import ExamAppearance


class AppearanceRepository(Protocol):
    def save(self, appearance: ExamAppearance) -> None: ...

    def get_for_question(self, question_id: str) -> tuple[ExamAppearance, ...]: ...


class InMemoryAppearanceRepository:
    def __init__(self) -> None:
        self._items: dict[str, ExamAppearance] = {}

    def save(self, appearance: ExamAppearance) -> None:
        if appearance.appearance_id in self._items:
            existing = self._items[appearance.appearance_id]
            if existing != appearance:
                raise ValueError("appearance_id already exists with different data")
            return
        self._items[appearance.appearance_id] = appearance

    def save_many(self, appearances: Iterable[ExamAppearance]) -> None:
        for appearance in appearances:
            self.save(appearance)

    def get_for_question(self, question_id: str) -> tuple[ExamAppearance, ...]:
        return tuple(item for item in self._items.values() if item.question_id == question_id)
