"""Idempotent persistence of the trusted Phase 1 source/exam registry."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from ai_comp.research.seed_registry import build_initial_registry
from ai_comp.research.source_registry import SourceRegistry


@dataclass(frozen=True)
class RegistrySyncCounts:
    conducting_bodies: int
    exams: int
    paper_categories: int
    sources: int


def sync_source_registry(
    connection: Any,
    registry: SourceRegistry | None = None,
) -> RegistrySyncCounts:
    """Upsert registry contracts to PostgreSQL without deleting existing rows.

    This is deliberately additive/idempotent: future source registry additions
    update rows with the same stable ID, while papers and historical appearances
    already stored in the database are left untouched.
    """
    active_registry = registry or build_initial_registry()

    with connection.transaction():
        for body in active_registry.bodies():
            connection.execute(
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
                    json.dumps(list(body.official_domains)),
                ),
            )

        for exam in active_registry.exams():
            connection.execute(
                """
                INSERT INTO exams (
                    exam_id, name, conducting_body_id, level, state,
                    categories, active
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
                    json.dumps(list(exam.categories)),
                    exam.active,
                ),
            )

        for category in active_registry.categories():
            connection.execute(
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
                    json.dumps(list(category.allowed_formats)),
                ),
            )

        for source in active_registry.sources():
            connection.execute(
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
                    json.dumps(list(source.allowed_paths)),
                    source.notes,
                ),
            )

    return RegistrySyncCounts(
        conducting_bodies=len(active_registry.bodies()),
        exams=len(active_registry.exams()),
        paper_categories=len(active_registry.categories()),
        sources=len(active_registry.sources()),
    )
