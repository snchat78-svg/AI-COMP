from typing import Any

from ai_comp.database.models import PaperRecord
from ai_comp.database.repository import RepositoryError


class PostgresPaperRepository:
    """PostgreSQL adapter for canonical paper metadata."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, paper: PaperRecord) -> None:
        if paper.year is not None and paper.year < 1900:
            raise ValueError("paper year must be a realistic exam year")
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO papers (
                        paper_id,
                        candidate_id,
                        title,
                        exam_id,
                        category_id,
                        source_id,
                        canonical_url,
                        year,
                        shift
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (paper_id) DO UPDATE SET
                        candidate_id = EXCLUDED.candidate_id,
                        title = EXCLUDED.title,
                        exam_id = EXCLUDED.exam_id,
                        category_id = EXCLUDED.category_id,
                        source_id = EXCLUDED.source_id,
                        canonical_url = EXCLUDED.canonical_url,
                        year = EXCLUDED.year,
                        shift = EXCLUDED.shift
                    """,
                    (
                        paper.paper_id,
                        paper.candidate_id,
                        paper.title,
                        paper.exam_id,
                        paper.category_id,
                        paper.source_id,
                        paper.canonical_url,
                        paper.year,
                        paper.shift,
                    ),
                )
        except Exception as exc:
            raise RepositoryError("failed to persist paper") from exc

    def get(self, paper_id: str) -> PaperRecord | None:
        try:
            row = self._connection.execute(
                """
                SELECT
                    paper_id,
                    candidate_id,
                    title,
                    exam_id,
                    category_id,
                    source_id,
                    canonical_url,
                    year,
                    shift
                FROM papers
                WHERE paper_id = %s
                """,
                (paper_id,),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to read paper") from exc

        if row is None:
            return None

        return PaperRecord(
            paper_id=str(row[0]),
            candidate_id=None if row[1] is None else str(row[1]),
            title=None if row[2] is None else str(row[2]),
            exam_id=None if row[3] is None else str(row[3]),
            category_id=None if row[4] is None else str(row[4]),
            source_id=None if row[5] is None else str(row[5]),
            canonical_url=None if row[6] is None else str(row[6]),
            year=None if row[7] is None else int(row[7]),
            shift=None if row[8] is None else str(row[8]),
        )
