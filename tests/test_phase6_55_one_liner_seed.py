from __future__ import annotations

import re
from pathlib import Path

from ai_comp.domain.topic_question_bank import OneLinerVerificationStatus, TopicOneLinerQA


SEED_PATH = Path("database/migrations/0022_phase6_55_seed_one_liner_candidates.sql")
CATALOGUE_PATH = Path("database/migrations/0020_phase6_53_starter_topic_catalogue.sql")


def test_phase_655_seed_has_source_backed_pending_candidates_with_valid_hashes() -> None:
    sql = SEED_PATH.read_text(encoding="utf-8")
    catalogue = CATALOGUE_PATH.read_text(encoding="utf-8")
    row_pattern = re.compile(
        r"\(\s*'([^']+)',\s*'([^']+)',\s*'((?:''|[^'])*)',\s*'((?:''|[^'])*)',"
        r"\s*'([^']*)',\s*'([^']*)',\s*'((?:''|[^'])*)',\s*'NEEDS_REVIEW',"
        r"\s*([0-9.]+),\s*'([0-9a-f]{64})',\s*NULL\s*\)",
        re.DOTALL,
    )
    rows = row_pattern.findall(sql)

    assert len(rows) == 10
    ids = set()
    for (
        one_liner_id,
        concept_id,
        raw_question,
        raw_answer,
        language_code,
        source_url,
        raw_evidence,
        importance,
        stored_hash,
    ) in rows:
        question_text = raw_question.replace("''", "'")
        answer_text = raw_answer.replace("''", "'")
        source_evidence = raw_evidence.replace("''", "'")
        assert one_liner_id not in ids
        ids.add(one_liner_id)
        assert concept_id in catalogue
        assert source_url.startswith("https://")
        assert source_evidence.strip()
        candidate = TopicOneLinerQA(
            one_liner_id=one_liner_id,
            concept_id=concept_id,
            question_text=question_text,
            answer_text=answer_text,
            language_code=language_code,
            source_url=source_url,
            source_evidence=source_evidence,
            verification_status=OneLinerVerificationStatus.NEEDS_REVIEW,
            importance_score=float(importance),
        )
        assert candidate.content_hash == stored_hash
        assert candidate.reviewed_at is None

    assert "ON CONFLICT (concept_id, language_code, content_hash) DO NOTHING" in sql
    assert "'VERIFIED'" not in sql
