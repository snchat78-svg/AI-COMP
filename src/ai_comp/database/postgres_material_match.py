import json
from typing import Any

from ai_comp.database.repository import RepositoryError
from ai_comp.domain.matching import MatchEvidence, MatchType
from ai_comp.domain.material_matching import (
    MaterialProbeType,
    MaterialQuestionMatch,
)


class PostgresMaterialQuestionMatchRepository:
    """Persists Phase 6.4 material-to-verified-exam match decisions."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save(self, match: MaterialQuestionMatch) -> None:
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO material_question_matches (
                        material_id,
                        probe_id,
                        probe_type,
                        master_question_id,
                        match_type,
                        confidence,
                        verified_appearance_count,
                        evidence
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (
                        material_id, probe_id, master_question_id, match_type
                    )
                    DO UPDATE SET
                        confidence = EXCLUDED.confidence,
                        verified_appearance_count = EXCLUDED.verified_appearance_count,
                        evidence = EXCLUDED.evidence
                    """,
                    (
                        match.material_id,
                        match.probe_id,
                        match.probe_type.value,
                        match.master_question_id,
                        match.match_type.value,
                        match.confidence,
                        match.verified_appearance_count,
                        json.dumps(
                            [
                                {
                                    "method": item.method,
                                    "score": item.score,
                                    "notes": item.notes,
                                }
                                for item in match.evidence
                            ],
                            ensure_ascii=False,
                        ),
                    ),
                )
        except Exception as exc:
            raise RepositoryError(
                "failed to persist material question match"
            ) from exc

    def save_many(self, matches) -> None:
        for match in matches:
            self.save(match)

    def get_for_material(
        self,
        material_id: str,
    ) -> tuple[MaterialQuestionMatch, ...]:
        try:
            rows = self._connection.execute(
                """
                SELECT
                    material_id,
                    probe_id,
                    probe_type,
                    master_question_id,
                    match_type,
                    confidence,
                    verified_appearance_count,
                    evidence
                FROM material_question_matches
                WHERE material_id = %s
                ORDER BY probe_id, master_question_id, match_type
                """,
                (material_id,),
            ).fetchall()
        except Exception as exc:
            raise RepositoryError(
                "failed to read material question matches"
            ) from exc

        result = []
        for row in rows:
            evidence = row[7]
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            result.append(
                MaterialQuestionMatch(
                    material_id=str(row[0]),
                    probe_id=str(row[1]),
                    probe_type=MaterialProbeType(str(row[2])),
                    master_question_id=str(row[3]),
                    match_type=MatchType(str(row[4])),
                    confidence=float(row[5]),
                    verified_appearance_count=int(row[6]),
                    evidence=tuple(
                        MatchEvidence(
                            method=str(item["method"]),
                            score=(
                                None
                                if item.get("score") is None
                                else float(item["score"])
                            ),
                            notes=str(item.get("notes", "")),
                        )
                        for item in (evidence or ())
                    ),
                )
            )
        return tuple(result)
