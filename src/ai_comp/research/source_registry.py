from ai_comp.domain.exams import ConductingBody, Exam, PaperCategory
from ai_comp.domain.sources import SourceRecord


class RegistryError(ValueError):
    pass


class SourceRegistry:
    """In-memory Phase 1 registry; persistence is intentionally deferred."""

    def __init__(self) -> None:
        self._bodies: dict[str, ConductingBody] = {}
        self._exams: dict[str, Exam] = {}
        self._categories: dict[str, PaperCategory] = {}
        self._sources: dict[str, SourceRecord] = {}

    def add_body(self, body: ConductingBody) -> None:
        self._ensure_new(self._bodies, body.body_id, "conducting body")
        self._bodies[body.body_id] = body

    def add_exam(self, exam: Exam) -> None:
        if exam.conducting_body_id not in self._bodies:
            raise RegistryError(f"Unknown conducting body: {exam.conducting_body_id}")
        self._ensure_new(self._exams, exam.exam_id, "exam")
        self._exams[exam.exam_id] = exam

    def add_category(self, category: PaperCategory) -> None:
        if category.exam_id not in self._exams:
            raise RegistryError(f"Unknown exam: {category.exam_id}")
        self._ensure_new(self._categories, category.category_id, "paper category")
        self._categories[category.category_id] = category

    def add_source(self, source: SourceRecord) -> None:
        if source.conducting_body_id and source.conducting_body_id not in self._bodies:
            raise RegistryError(f"Unknown conducting body: {source.conducting_body_id}")
        self._ensure_new(self._sources, source.source_id, "source")
        self._sources[source.source_id] = source

    def get_exam(self, exam_id: str) -> Exam:
        return self._exams[exam_id]

    def get_source(self, source_id: str) -> SourceRecord:
        return self._sources[source_id]

    def exams(self) -> tuple[Exam, ...]:
        return tuple(self._exams.values())

    def sources(self) -> tuple[SourceRecord, ...]:
        return tuple(self._sources.values())

    @staticmethod
    def _ensure_new(store: dict, key: str, kind: str) -> None:
        if key in store:
            raise RegistryError(f"Duplicate {kind} id: {key}")
