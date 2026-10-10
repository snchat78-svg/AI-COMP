from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from typing import Any


class NoAdaptivePracticeSignal(ValueError):
    """Raised when persisted learner outcomes do not support a focused recommendation."""


@dataclass(frozen=True)
class AdaptivePracticeRecommendation:
    """A deterministic focus plan derived only from server-owned learner analytics."""

    learner_id: str
    concept_ids: tuple[str, ...]
    focus_reasons: tuple[tuple[str, tuple[str, ...]], ...]
    revision_question_ids: tuple[str, ...]
    completed_test_count: int
    weak_topic_count: int
    repeated_concept_count: int


class AdaptivePracticeRecommendationPlanner:
    """Select focus concepts without duplicating analytics or question composition.

    The planner intentionally does not select questions. Phase 6.14's adaptive
    composer remains responsible for combining retention, prior mistakes,
    remediation, advancement, and quality-ranked candidates.
    """

    def plan(
        self,
        learner_id: str,
        report: Mapping[str, Any],
        *,
        max_concepts: int = 8,
    ) -> AdaptivePracticeRecommendation:
        if not isinstance(learner_id, str) or not learner_id.strip():
            raise ValueError("learner_id is required")
        if learner_id != learner_id.strip():
            raise ValueError("learner_id must not contain surrounding whitespace")
        if not isinstance(report, Mapping) or report.get("learner_id") != learner_id:
            raise ValueError("analytics report must belong to the requested learner")
        if (
            isinstance(max_concepts, bool)
            or not isinstance(max_concepts, int)
            or not 1 <= max_concepts <= 20
        ):
            raise ValueError("max_concepts must be between 1 and 20")

        topics = _mapping_rows(report.get("topic_performance"))
        weak_topics = _mapping_rows(report.get("weak_topics"))
        revision_candidates = _mapping_rows(report.get("revision_candidates"))
        repeated_alerts = _mapping_rows(report.get("repeated_concept_alerts"))
        summary = report.get("summary")
        summary = summary if isinstance(summary, Mapping) else {}

        topic_by_id: dict[str, Mapping[str, Any]] = {}
        for item in topics:
            concept_id = _identifier(item.get("concept_id"))
            if concept_id is not None:
                topic_by_id[concept_id] = item

        ordered: list[str] = []
        reasons: dict[str, list[str]] = {}

        def add(concept_id: object, reason: str) -> None:
            valid_id = _identifier(concept_id)
            if valid_id is None:
                return
            if valid_id not in reasons:
                reasons[valid_id] = []
                ordered.append(valid_id)
            if reason not in reasons[valid_id]:
                reasons[valid_id].append(reason)

        # First address explicit weak-topic decisions from the canonical history service.
        for item in sorted(weak_topics, key=_priority, reverse=True):
            concept_id = _identifier(item.get("concept_id"))
            add(concept_id, "WEAK_TOPIC")
            topic = topic_by_id.get(concept_id or "", item)
            if _text(topic.get("trend")) == "DECLINING":
                add(concept_id, "DECLINING_TREND")

        # Repeatedly weak concepts are useful when they are not in the weak-topic band.
        for item in sorted(repeated_alerts, key=_priority, reverse=True):
            add(item.get("concept_id"), "REPEATED_CONCEPT")

        # Keep question-level mistake information; the existing composer will decide
        # which of these questions actually enter the test.
        sorted_revisions = sorted(
            revision_candidates,
            key=lambda item: (
                _priority(item),
                _number(item.get("mistake_streak")),
                _text(item.get("last_incorrect_at")) or "",
            ),
            reverse=True,
        )
        for item in sorted_revisions:
            concepts = item.get("concept_ids", ())
            if isinstance(concepts, (list, tuple)):
                for concept_id in concepts:
                    add(concept_id, "PREVIOUS_MISTAKE")

        # Only use fallback topics with evidence of need; never invent a weak area
        # just because a learner has completed tests.
        fallback_topics = [
            item for item in topics
            if _text(item.get("performance")) in {"WEAK", "AVERAGE"}
            or _text(item.get("trend")) == "DECLINING"
        ]
        for item in sorted(fallback_topics, key=_priority, reverse=True):
            concept_id = _identifier(item.get("concept_id"))
            performance = _text(item.get("performance"))
            trend = _text(item.get("trend"))
            add(concept_id, "WEAK_TOPIC" if performance == "WEAK" else "HIGH_PRIORITY_TOPIC")
            if trend == "DECLINING":
                add(concept_id, "DECLINING_TREND")

        selected_ids = tuple(ordered[:max_concepts])
        if not selected_ids:
            raise NoAdaptivePracticeSignal(
                "persisted learner analytics do not contain a weak topic, repeated-concept alert, or previous-mistake signal"
            )

        selected_set = set(selected_ids)
        revision_ids: list[str] = []
        for item in sorted_revisions:
            question_id = _identifier(item.get("question_id"))
            concepts = item.get("concept_ids", ())
            if (
                question_id is not None
                and isinstance(concepts, (list, tuple))
                and selected_set.intersection(
                    concept for concept in concepts if _identifier(concept) is not None
                )
                and question_id not in revision_ids
            ):
                revision_ids.append(question_id)
            if len(revision_ids) >= 50:
                break

        return AdaptivePracticeRecommendation(
            learner_id=learner_id,
            concept_ids=selected_ids,
            focus_reasons=tuple(
                (concept_id, tuple(reasons[concept_id]))
                for concept_id in selected_ids
            ),
            revision_question_ids=tuple(revision_ids),
            completed_test_count=max(0, int(_number(summary.get("completed_test_count")))),
            weak_topic_count=max(0, int(_number(summary.get("weak_topic_count"), len(weak_topics)))),
            repeated_concept_count=max(
                0,
                int(_number(summary.get("repeated_concept_alert_count"), len(repeated_alerts))),
            ),
        )


def _mapping_rows(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _identifier(value: object) -> str | None:
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    return value


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _number(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _priority(item: Mapping[str, Any]) -> float:
    return _number(item.get("priority_score"))


__all__ = [
    "AdaptivePracticeRecommendation",
    "AdaptivePracticeRecommendationPlanner",
    "NoAdaptivePracticeSignal",
]
