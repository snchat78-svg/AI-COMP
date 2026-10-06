from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol

from ai_comp.domain.matching import MatchEvidence, MatchType
from ai_comp.domain.material_analysis import ProposedConcept
from ai_comp.domain.material_matching import (
    MaterialMatchingResult,
    MaterialProbeType,
    MaterialQuestionMatch,
    MaterialQuestionProbe,
)
from ai_comp.domain.materials import NormalizedMaterial
from ai_comp.domain.master_questions import MasterQuestionStatus
from ai_comp.domain.verification import VerificationStatus
from ai_comp.history.dedup import AppearanceDeduplicator
from ai_comp.master.repository import MasterQuestionRepository


class MaterialQuestionEmbedding(Protocol):
    def __call__(self, text: str) -> tuple[float, ...]: ...


MaterialConceptResolver = Callable[[ProposedConcept], str | None]
RelatedTopicResolver = Callable[[ProposedConcept, object], float | None]


@dataclass(frozen=True)
class MaterialMatchingPolicy:
    """Conservative thresholds for verified exam matching."""

    min_rephrased_confidence: float = 0.94
    min_confidence_margin: float = 0.05
    min_related_topic_confidence: float = 0.85
    max_master_candidates: int = 5000

    def __post_init__(self) -> None:
        if not 0.0 < self.min_rephrased_confidence <= 1.0:
            raise ValueError("min_rephrased_confidence must be between 0 and 1")
        if not 0.0 <= self.min_confidence_margin <= 1.0:
            raise ValueError("min_confidence_margin must be between 0 and 1")
        if not 0.0 < self.min_related_topic_confidence <= 1.0:
            raise ValueError("min_related_topic_confidence must be between 0 and 1")
        if self.max_master_candidates < 1:
            raise ValueError("max_master_candidates must be positive")


class MaterialQuestionProbeExtractor:
    """Extracts only explicitly marked question text; it never turns a fact into a question."""

    _QUESTION_MARK = re.compile(r"[?？]")

    def extract(self, material: NormalizedMaterial) -> tuple[MaterialQuestionProbe, ...]:
        probes: list[MaterialQuestionProbe] = []

        for paragraph in re.split(r"\n\s*\n", material.text):
            for raw in re.split(r"(?<=[?？])", paragraph):
                candidate = raw.strip()
                if not candidate or not self._QUESTION_MARK.search(candidate):
                    continue
                if len(candidate) > 1200:
                    continue
                probe_id = self._stable_id(material.material_id, candidate)
                probes.append(
                    MaterialQuestionProbe(
                        probe_id=probe_id,
                        material_id=material.material_id,
                        text=candidate,
                        evidence_text=candidate,
                        probe_type=MaterialProbeType.QUESTION_TEXT,
                    )
                )

        seen: set[str] = set()
        result = []
        for probe in probes:
            if probe.probe_id in seen:
                continue
            seen.add(probe.probe_id)
            result.append(probe)
        return tuple(result)

    @staticmethod
    def _stable_id(material_id: str, text: str) -> str:
        digest = hashlib.sha256(
            f"{material_id}|{text}".encode("utf-8")
        ).hexdigest()[:24]
        return f"probe:{digest}"


@dataclass(frozen=True)
class _VerifiedMaster:
    master: object
    verified_appearance_count: int


class MaterialExamMatchingService:
    """Matches user material only against verified, active master-question identities."""

    def __init__(
        self,
        master_repository: MasterQuestionRepository,
        appearance_repository,
        *,
        embedding: MaterialQuestionEmbedding | None = None,
        concept_resolver: MaterialConceptResolver | None = None,
        related_topic_resolver: RelatedTopicResolver | None = None,
        policy: MaterialMatchingPolicy | None = None,
    ) -> None:
        self.master_repository = master_repository
        self.appearance_repository = appearance_repository
        self.embedding = embedding
        self.concept_resolver = concept_resolver
        self.related_topic_resolver = related_topic_resolver
        self.policy = policy or MaterialMatchingPolicy()

    def match(
        self,
        material: NormalizedMaterial,
        *,
        concepts: Iterable[ProposedConcept] = (),
        question_probes: Iterable[MaterialQuestionProbe] | None = None,
    ) -> MaterialMatchingResult:
        masters = self._verified_masters()
        warnings: list[str] = []

        if not masters:
            warnings.append("verified master-question database returned no candidates")

        probes = (
            tuple(question_probes)
            if question_probes is not None
            else MaterialQuestionProbeExtractor().extract(material)
        )
        for probe in probes:
            if probe.material_id != material.material_id:
                raise ValueError("question probe material_id does not match material")
            if probe.evidence_text not in material.text:
                raise ValueError("question probe evidence is not grounded in material")

        concepts_tuple = tuple(concepts)
        for concept in concepts_tuple:
            if concept.material_id != material.material_id:
                raise ValueError("concept material_id does not match material")
            if concept.evidence_text not in material.text:
                raise ValueError("concept evidence is not grounded in material")

        existing, unmatched = self._match_existing_questions(probes, masters)
        same_concept, related_topic = self._match_concepts(
            concepts_tuple, masters
        )

        return MaterialMatchingResult(
            material_id=material.material_id,
            existing_question_matches=tuple(existing),
            same_concept_matches=tuple(same_concept),
            related_topic_matches=tuple(related_topic),
            unmatched_question_probe_ids=tuple(unmatched),
            warnings=tuple(warnings),
        )

    def _verified_masters(self) -> tuple[_VerifiedMaster, ...]:
        masters = self.master_repository.list_masters(
            status=MasterQuestionStatus.ACTIVE,
            limit=self.policy.max_master_candidates,
        )
        result: list[_VerifiedMaster] = []
        for master in masters:
            count = self._verified_appearance_count(master.master_question_id)
            if count > 0:
                result.append(
                    _VerifiedMaster(
                        master=master,
                        verified_appearance_count=count,
                    )
                )
        return tuple(result)

    def _verified_appearance_count(self, master_id: str) -> int:
        deduplicator = AppearanceDeduplicator()
        count = 0
        memberships = self.master_repository.get_memberships_for_master(master_id)
        for membership in memberships:
            for appearance in self.appearance_repository.get_for_question(
                membership.question_id
            ):
                if appearance.verification.status is not VerificationStatus.VERIFIED:
                    continue
                if not deduplicator.seen(appearance):
                    count += 1
        return count

    def _match_existing_questions(
        self,
        probes: tuple[MaterialQuestionProbe, ...],
        masters: tuple[_VerifiedMaster, ...],
    ) -> tuple[list[MaterialQuestionMatch], list[str]]:
        accepted: list[MaterialQuestionMatch] = []
        unmatched: list[str] = []

        for probe in probes:
            exact = self._exact_matches(probe, masters)
            if exact:
                accepted.extend(exact)
                continue

            if self.embedding is None:
                unmatched.append(probe.probe_id)
                continue

            probe_vector = self.embedding(probe.text)
            scored = []
            for candidate in masters:
                score = self._cosine(
                    probe_vector,
                    self.embedding(candidate.master.stem),
                )
                scored.append((score, candidate))

            scored.sort(
                key=lambda item: (-item[0], item[1].master.master_question_id)
            )
            eligible = [
                item for item in scored
                if item[0] >= self.policy.min_rephrased_confidence
            ]
            if not eligible:
                unmatched.append(probe.probe_id)
                continue

            best_score, best = eligible[0]
            second_score = eligible[1][0] if len(eligible) > 1 else 0.0
            if (
                len(eligible) > 1
                and best_score - second_score < self.policy.min_confidence_margin
            ):
                unmatched.append(probe.probe_id)
                continue

            accepted.append(
                MaterialQuestionMatch(
                    material_id=probe.material_id,
                    probe_id=probe.probe_id,
                    probe_type=probe.probe_type,
                    master_question_id=best.master.master_question_id,
                    match_type=MatchType.REPHRASED,
                    confidence=max(0.0, min(1.0, best_score)),
                    verified_appearance_count=best.verified_appearance_count,
                    evidence=(
                        MatchEvidence(
                            method="material_question_embedding",
                            score=best_score,
                            notes="matched only against verified active master",
                        ),
                    ),
                )
            )

        return accepted, unmatched

    @staticmethod
    def _exact_matches(
        probe: MaterialQuestionProbe,
        masters: tuple[_VerifiedMaster, ...],
    ) -> list[MaterialQuestionMatch]:
        from ai_comp.matching.normalization import normalize_question_text

        probe_key = normalize_question_text(probe.text)
        matches = []
        for candidate in masters:
            if probe_key == normalize_question_text(candidate.master.stem):
                matches.append(
                    MaterialQuestionMatch(
                        material_id=probe.material_id,
                        probe_id=probe.probe_id,
                        probe_type=probe.probe_type,
                        master_question_id=candidate.master.master_question_id,
                        match_type=MatchType.EXACT,
                        confidence=1.0,
                        verified_appearance_count=candidate.verified_appearance_count,
                        evidence=(
                            MatchEvidence(
                                method="normalized_question_text",
                                score=1.0,
                                notes="exact normalized stem match",
                            ),
                        ),
                    )
                )
        return matches

    def _match_concepts(
        self,
        concepts: tuple[ProposedConcept, ...],
        masters: tuple[_VerifiedMaster, ...],
    ) -> tuple[list[MaterialQuestionMatch], list[MaterialQuestionMatch]]:
        if not concepts:
            return [], []

        same_concept: list[MaterialQuestionMatch] = []
        related_topic: list[MaterialQuestionMatch] = []
        if self.concept_resolver is not None:
            for concept in concepts:
                concept_id = self.concept_resolver(concept)
                if not concept_id:
                    continue
                for candidate in masters:
                    if candidate.master.concept_id != concept_id:
                        continue
                    same_concept.append(
                        MaterialQuestionMatch(
                            material_id=concept.material_id,
                            probe_id=concept.concept_candidate_id,
                            probe_type=MaterialProbeType.CONCEPT,
                            master_question_id=candidate.master.master_question_id,
                            match_type=MatchType.SAME_CONCEPT,
                            confidence=concept.confidence,
                            verified_appearance_count=candidate.verified_appearance_count,
                            evidence=(
                                MatchEvidence(
                                    method="canonical_concept_id",
                                    score=1.0,
                                    notes=f"concept_id:{concept_id}",
                                ),
                            ),
                        )
                    )

        if self.related_topic_resolver is not None:
            same_pairs = {
                (item.probe_id, item.master_question_id)
                for item in same_concept
            }
            for concept in concepts:
                for candidate in masters:
                    if (concept.concept_candidate_id, candidate.master.master_question_id) in same_pairs:
                        continue
                    score = self.related_topic_resolver(concept, candidate.master)
                    if score is None or score < self.policy.min_related_topic_confidence:
                        continue
                    related_topic.append(
                        MaterialQuestionMatch(
                            material_id=concept.material_id,
                            probe_id=concept.concept_candidate_id,
                            probe_type=MaterialProbeType.CONCEPT,
                            master_question_id=candidate.master.master_question_id,
                            match_type=MatchType.RELATED_TOPIC,
                            confidence=max(0.0, min(1.0, score)),
                            verified_appearance_count=candidate.verified_appearance_count,
                            evidence=(
                                MatchEvidence(
                                    method="explicit_related_topic_resolver",
                                    score=score,
                                    notes="topic relationship is not historical equivalence",
                                ),
                            ),
                        )
                    )

        return same_concept, related_topic

    @staticmethod
    def _cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
        if not a or not b or len(a) != len(b):
            raise ValueError("embedding vectors must be non-empty and same length")
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)
