import json
from typing import Any

from ai_comp.database.models import RegistrySnapshot
from ai_comp.database.repository import RepositoryError
from ai_comp.domain.exams import ConductingBody, Exam, ExamLevel, PaperCategory
from ai_comp.domain.sources import SourcePriority, SourceRecord, SourceType
from ai_comp.domain.verification import (
    EvidenceType,
    SourceVerification,
    VerificationStatus,
)


class PostgresRegistryRepository:
    """PostgreSQL adapter for the Phase 1 registry contracts."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save_body(self, body: ConductingBody) -> None:
        self._execute(
            """
            INSERT INTO conducting_bodies (
                body_id, name, level, country, state, official_domains
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (body_id) DO UPDATE SET
                name = EXCLUDED.name,
                level = EXCLUDED.level,
                country = EXCLUDED.country,
                state = EXCLUDED.state,
                official_domains = EXCLUDED.official_domains
            """,
            (
                body.body_id,
                body.name,
                body.level.value,
                body.country,
                body.state,
                json.dumps(list(body.official_domains), ensure_ascii=False),
            ),
        )

    def save_exam(self, exam: Exam) -> None:
        self._execute(
            """
            INSERT INTO exams (
                exam_id, name, conducting_body_id, level, state, categories, active
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (exam_id) DO UPDATE SET
                name = EXCLUDED.name,
                conducting_body_id = EXCLUDED.conducting_body_id,
                level = EXCLUDED.level,
                state = EXCLUDED.state,
                categories = EXCLUDED.categories,
                active = EXCLUDED.active
            """,
            (
                exam.exam_id,
                exam.name,
                exam.conducting_body_id,
                exam.level.value,
                exam.state,
                json.dumps(list(exam.categories), ensure_ascii=False),
                exam.active,
            ),
        )

    def save_category(self, category: PaperCategory) -> None:
        self._execute(
            """
            INSERT INTO paper_categories (
                category_id, name, exam_id, description, allowed_formats
            )
            VALUES (%s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (category_id) DO UPDATE SET
                name = EXCLUDED.name,
                exam_id = EXCLUDED.exam_id,
                description = EXCLUDED.description,
                allowed_formats = EXCLUDED.allowed_formats
            """,
            (
                category.category_id,
                category.name,
                category.exam_id,
                category.description,
                json.dumps(list(category.allowed_formats), ensure_ascii=False),
            ),
        )

    def save_source(self, source: SourceRecord) -> None:
        self._execute(
            """
            INSERT INTO sources (
                source_id, name, base_url, source_type, priority,
                conducting_body_id, allowed_paths, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (source_id) DO UPDATE SET
                name = EXCLUDED.name,
                base_url = EXCLUDED.base_url,
                source_type = EXCLUDED.source_type,
                priority = EXCLUDED.priority,
                conducting_body_id = EXCLUDED.conducting_body_id,
                allowed_paths = EXCLUDED.allowed_paths,
                notes = EXCLUDED.notes
            """,
            (
                source.source_id,
                source.name,
                source.base_url,
                source.source_type.value,
                source.priority.value,
                source.conducting_body_id,
                json.dumps(list(source.allowed_paths), ensure_ascii=False),
                source.notes,
            ),
        )

    def save_verification(self, verification: SourceVerification) -> None:
        self._execute(
            """
            INSERT INTO source_verifications (
                verification_id, source_id, source_url, status,
                evidence_type, checked_at, confidence, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (verification_id) DO UPDATE SET
                source_id = EXCLUDED.source_id,
                source_url = EXCLUDED.source_url,
                status = EXCLUDED.status,
                evidence_type = EXCLUDED.evidence_type,
                checked_at = EXCLUDED.checked_at,
                confidence = EXCLUDED.confidence,
                notes = EXCLUDED.notes
            """,
            (
                verification.verification_id,
                verification.source_id,
                verification.source_url,
                verification.status.value,
                verification.evidence_type.value,
                verification.checked_at,
                verification.confidence,
                verification.notes,
            ),
        )

    def get_body(self, body_id: str) -> ConductingBody | None:
        row = self._fetchone(
            """
            SELECT body_id, name, level, country, state, official_domains
            FROM conducting_bodies
            WHERE body_id = %s
            """,
            (body_id,),
        )
        if row is None:
            return None
        return ConductingBody(
            body_id=str(row[0]),
            name=str(row[1]),
            level=ExamLevel(str(row[2])),
            country=str(row[3]),
            state=None if row[4] is None else str(row[4]),
            official_domains=self._json_array(row[5]),
        )

    def get_exam(self, exam_id: str) -> Exam | None:
        row = self._fetchone(
            """
            SELECT exam_id, name, conducting_body_id, level, state, categories, active
            FROM exams
            WHERE exam_id = %s
            """,
            (exam_id,),
        )
        if row is None:
            return None
        return Exam(
            exam_id=str(row[0]),
            name=str(row[1]),
            conducting_body_id=str(row[2]),
            level=ExamLevel(str(row[3])),
            state=None if row[4] is None else str(row[4]),
            categories=self._json_array(row[5]),
            active=bool(row[6]),
        )

    def get_category(self, category_id: str) -> PaperCategory | None:
        row = self._fetchone(
            """
            SELECT category_id, name, exam_id, description, allowed_formats
            FROM paper_categories
            WHERE category_id = %s
            """,
            (category_id,),
        )
        if row is None:
            return None
        return PaperCategory(
            category_id=str(row[0]),
            name=str(row[1]),
            exam_id=str(row[2]),
            description=str(row[3]),
            allowed_formats=self._json_array(row[4]),
        )

    def get_source(self, source_id: str) -> SourceRecord | None:
        row = self._fetchone(
            """
            SELECT
                source_id, name, base_url, source_type, priority,
                conducting_body_id, allowed_paths, notes
            FROM sources
            WHERE source_id = %s
            """,
            (source_id,),
        )
        if row is None:
            return None
        return SourceRecord(
            source_id=str(row[0]),
            name=str(row[1]),
            base_url=str(row[2]),
            source_type=SourceType(str(row[3])),
            priority=SourcePriority(str(row[4])),
            conducting_body_id=(
                None if row[5] is None else str(row[5])
            ),
            allowed_paths=self._json_array(row[6]),
            notes=str(row[7]),
        )

    def get_verifications(self, source_id: str) -> tuple[SourceVerification, ...]:
        rows = self._fetchall(
            """
            SELECT
                verification_id, source_id, source_url, status,
                evidence_type, checked_at, confidence, notes
            FROM source_verifications
            WHERE source_id = %s
            ORDER BY checked_at DESC, verification_id
            """,
            (source_id,),
        )
        return tuple(self._verification_from_row(row) for row in rows)

    def snapshot(self) -> RegistrySnapshot:
        bodies = self._fetchall(
            "SELECT body_id FROM conducting_bodies ORDER BY body_id"
        )
        exams = self._fetchall("SELECT exam_id FROM exams ORDER BY exam_id")
        categories = self._fetchall(
            "SELECT category_id FROM paper_categories ORDER BY category_id"
        )
        sources = self._fetchall("SELECT source_id FROM sources ORDER BY source_id")

        return RegistrySnapshot(
            conducting_bodies=tuple(
                self.get_body(str(row[0])) for row in bodies
            ),
            exams=tuple(
                self.get_exam(str(row[0])) for row in exams
            ),
            paper_categories=tuple(
                self.get_category(str(row[0])) for row in categories
            ),
            sources=tuple(
                self.get_source(str(row[0])) for row in sources
            ),
            verifications=tuple(
                verification
                for source_row in sources
                for verification in self.get_verifications(str(source_row[0]))
            ),
        )

    def _execute(self, sql: str, params: tuple[object, ...]) -> None:
        try:
            with self._connection.transaction():
                self._connection.execute(sql, params)
        except Exception as exc:
            raise RepositoryError("failed to persist registry record") from exc

    def _fetchone(self, sql: str, params: tuple[object, ...]):
        try:
            return self._connection.execute(sql, params).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to read registry record") from exc

    def _fetchall(self, sql: str, params: tuple[object, ...] = ()):
        try:
            return self._connection.execute(sql, params).fetchall()
        except Exception as exc:
            raise RepositoryError("failed to read registry collection") from exc

    @staticmethod
    def _json_array(value) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            value = json.loads(value)
        return tuple(str(item) for item in value)

    @staticmethod
    def _verification_from_row(row) -> SourceVerification:
        return SourceVerification(
            verification_id=str(row[0]),
            source_id=str(row[1]),
            source_url=str(row[2]),
            status=VerificationStatus(str(row[3])),
            evidence_type=EvidenceType(str(row[4])),
            checked_at=row[5],
            confidence=None if row[6] is None else float(row[6]),
            notes=str(row[7]),
        )
