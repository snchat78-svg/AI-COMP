from dataclasses import dataclass
from typing import Any

from ai_comp.database.postgres_answer_key import PostgresAnswerKeyRepository
from ai_comp.database.postgres_answer_resolution import PostgresAnswerResolutionRepository
from ai_comp.database.postgres_appearance import PostgresAppearanceRepository
from ai_comp.database.postgres_concept import PostgresConceptRepository
from ai_comp.database.postgres_embedding import PostgresEmbeddingRepository
from ai_comp.database.postgres_match import PostgresMatchRepository
from ai_comp.database.postgres_paper import PostgresPaperRepository
from ai_comp.database.postgres_question import PostgresQuestionRepository
from ai_comp.database.postgres_registry import PostgresRegistryRepository
from ai_comp.database.postgres_research import PostgresResearchRepository


@dataclass(frozen=True)
class PostgresRepositories:
    registry: PostgresRegistryRepository
    research: PostgresResearchRepository
    papers: PostgresPaperRepository
    questions: PostgresQuestionRepository
    answer_keys: PostgresAnswerKeyRepository
    answer_resolutions: PostgresAnswerResolutionRepository
    concepts: PostgresConceptRepository
    matches: PostgresMatchRepository
    appearances: PostgresAppearanceRepository
    embeddings: PostgresEmbeddingRepository


class PostgresUnitOfWork:
    """Groups Phase 4 repository operations into one database transaction."""

    def __init__(self, connection: Any) -> None:
        self.connection = connection
        self.repositories = PostgresRepositories(
            registry=PostgresRegistryRepository(connection),
            research=PostgresResearchRepository(connection),
            papers=PostgresPaperRepository(connection),
            questions=PostgresQuestionRepository(connection),
            answer_keys=PostgresAnswerKeyRepository(connection),
            answer_resolutions=PostgresAnswerResolutionRepository(connection),
            concepts=PostgresConceptRepository(connection),
            matches=PostgresMatchRepository(connection),
            appearances=PostgresAppearanceRepository(connection),
            embeddings=PostgresEmbeddingRepository(connection),
        )
        self._transaction = None

    def __enter__(self) -> PostgresRepositories:
        self._transaction = self.connection.transaction()
        self._transaction.__enter__()
        return self.repositories

    def __exit__(self, exc_type, exc_value, traceback):
        if self._transaction is None:
            return False
        return self._transaction.__exit__(exc_type, exc_value, traceback)
