"""Conservative exam metadata resolution for official paper candidates.

This module only extracts explicit metadata from official archive labels/URLs.
It deliberately does not use an LLM's memory to invent an exam, year, or shift.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from urllib.parse import unquote, urlparse

from ai_comp.domain.exams import Exam, PaperCategory
from ai_comp.domain.sources import SourceRecord
from ai_comp.research.paper import PaperCandidate
from ai_comp.research.source_registry import SourceRegistry


class PaperArtifactRole(str, Enum):
    QUESTION_PAPER = "QUESTION_PAPER"
    ANSWER_KEY = "ANSWER_KEY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ResolvedPaperMetadata:
    candidate_id: str
    role: PaperArtifactRole
    exam_id: str | None
    year: int | None
    shift: str | None
    category_id: str | None
    ready_for_pairing: bool
    reason: str


_EXAM_ALIASES: dict[str, tuple[str, ...]] = {
    "RSSB_CET": (r"\bCET\b", r"common eligibility test"),
    "RSSB_PATWAR": (r"\bpatwar(?:i)?\b",),
    "RSSB_LDC": (r"\bLDC\b", r"lower division clerk"),
    "RSSB_VDO": (r"\bVDO\b", r"village development officer"),
    "RSSB_JUNIOR_ASSISTANT": (r"junior assistant",),
    "RSSB_LAB_ASSISTANT": (r"lab(?:oratory)? assistant",),
    "RPSC_RAS": (
        r"\bRAS\b",
        r"rajasthan state and subordinate services",
    ),
    "RPSC_SI": (
        r"\bsub[\s-]*inspector\b",
        r"\bSI combined\b",
    ),
    "RPSC_SCHOOL_LECTURER": (r"school lecturer",),
    "RPSC_SENIOR_TEACHER": (r"senior teacher", r"sr\.?\s*teacher"),
    "RPSC_ASSISTANT_PROFESSOR": (r"assistant professor",),
}


class PaperMetadataResolver:
    """Resolves only registered, explicit exam/year labels from trusted candidates."""

    def __init__(self, registry: SourceRegistry) -> None:
        self._registry = registry

    def resolve(
        self,
        candidate: PaperCandidate,
        source: SourceRecord,
        *,
        question_count: int,
        answer_key_entry_count: int,
    ) -> ResolvedPaperMetadata:
        if question_count < 0 or answer_key_entry_count < 0:
            raise ValueError("extraction counts cannot be negative")

        title = (candidate.title or "").strip()
        path = unquote(urlparse(candidate.url).path)
        text = f"{title} {path}".lower()
        role = self._resolve_role(
            text,
            question_count=question_count,
            answer_key_entry_count=answer_key_entry_count,
        )

        exam_matches: list[Exam] = []
        for exam in self._registry.exams():
            if exam.conducting_body_id != source.conducting_body_id:
                continue
            if exam.exam_id.endswith("_GENERIC"):
                continue
            patterns = _EXAM_ALIASES.get(exam.exam_id, ())
            if not patterns:
                patterns = (re.escape(exam.name.lower()),)
            if any(re.search(pattern, text, flags=re.I) for pattern in patterns):
                exam_matches.append(exam)

        # Prefer the one most specific registered alias. If a title matches
        # two registered exams, do not guess which exam generated the paper.
        exam_id: str | None = None
        exam_reason = "exam label was not explicit or did not match this source registry"
        if len(exam_matches) == 1:
            exam_id = exam_matches[0].exam_id
            exam_reason = "one explicit exam alias matched a registered exam"
        elif len(exam_matches) > 1:
            ranked = sorted(
                exam_matches,
                key=lambda exam: max(
                    (len(pattern.replace(r"\b", "")) for pattern in _EXAM_ALIASES.get(exam.exam_id, ())),
                    default=0,
                ),
                reverse=True,
            )
            top_score = max(
                (len(pattern.replace(r"\b", "")) for pattern in _EXAM_ALIASES.get(ranked[0].exam_id, ())),
                default=0,
            )
            second_score = max(
                (len(pattern.replace(r"\b", "")) for pattern in _EXAM_ALIASES.get(ranked[1].exam_id, ())),
                default=0,
            )
            if top_score > second_score:
                exam_id = ranked[0].exam_id
                exam_reason = "most-specific explicit exam alias matched"
            else:
                exam_reason = "title matches multiple registered exams; manual review required"

        years = {
            int(match.group(1))
            for match in re.finditer(r"(?<!\d)(19\d{2}|20\d{2}|2100)(?!\d)", text)
            if 1900 <= int(match.group(1)) <= 2100
        }
        year = next(iter(years)) if len(years) == 1 else None
        if len(years) > 1:
            year_reason = "multiple year values found; manual review required"
        elif not years:
            year_reason = "exam year is not explicit in the archive title/URL"
        else:
            year_reason = "one explicit year found in the archive title/URL"

        shifts = self._resolve_shifts(text)
        shift = shifts[0] if len(shifts) == 1 else None
        shift_reason = (
            "one explicit shift found"
            if len(shifts) == 1
            else "multiple shift values found; manual review required"
            if len(shifts) > 1
            else "shift not specified; pairing requires a unique exam-year candidate"
        )

        category_id = self._category_id(exam_id, role)
        ready = role is not PaperArtifactRole.UNKNOWN and exam_id is not None and year is not None
        reasons = [role.value, exam_reason, year_reason, shift_reason]
        if not ready:
            reasons.append("not eligible for automatic official-history ingestion")
        return ResolvedPaperMetadata(
            candidate_id=candidate.candidate_id,
            role=role,
            exam_id=exam_id,
            year=year,
            shift=shift,
            category_id=category_id,
            ready_for_pairing=ready,
            reason="; ".join(reasons),
        )

    @staticmethod
    def _resolve_role(
        text: str,
        *,
        question_count: int,
        answer_key_entry_count: int,
    ) -> PaperArtifactRole:
        if question_count > 0:
            return PaperArtifactRole.QUESTION_PAPER
        if answer_key_entry_count > 0:
            return PaperArtifactRole.ANSWER_KEY
        answer_markers = (
            "answer key", "answer-key", "answer_key", "answerkey",
            "final key", "model key", "उत्तर कुंजी", "उत्तरकुंजी",
        )
        question_markers = (
            "question paper", "question-paper", "question_paper",
            "previous question", "old paper", "प्रश्न पत्र", "प्रश्नपत्र",
        )
        has_answer_marker = any(token in text for token in answer_markers)
        has_question_marker = any(token in text for token in question_markers)
        if has_question_marker and not has_answer_marker:
            return PaperArtifactRole.QUESTION_PAPER
        if has_answer_marker and not has_question_marker:
            return PaperArtifactRole.ANSWER_KEY
        return PaperArtifactRole.UNKNOWN

    @staticmethod
    def _resolve_shifts(text: str) -> tuple[str, ...]:
        found: set[str] = set()
        for match in re.finditer(r"\bshift[\s:_-]*(\d{1,2})\b", text, flags=re.I):
            found.add(str(int(match.group(1))))
        named = (
            (r"\b(first|morning)\s+shift\b", "1"),
            (r"\b(second|afternoon)\s+shift\b", "2"),
            (r"\b(third|evening)\s+shift\b", "3"),
        )
        for pattern, value in named:
            if re.search(pattern, text, flags=re.I):
                found.add(value)
        return tuple(sorted(found, key=int))

    def _category_id(
        self,
        exam_id: str | None,
        role: PaperArtifactRole,
    ) -> str | None:
        if exam_id is None or role is PaperArtifactRole.UNKNOWN:
            return None
        expected = "answer key" if role is PaperArtifactRole.ANSWER_KEY else "question paper"
        matching = [
            category.category_id
            for category in self._registry.categories()
            if category.exam_id == exam_id and expected in category.name.lower()
        ]
        return matching[0] if len(matching) == 1 else None


__all__ = [
    "PaperArtifactRole",
    "PaperMetadataResolver",
    "ResolvedPaperMetadata",
]
