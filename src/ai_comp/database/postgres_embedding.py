from typing import Any

from ai_comp.database.models import EmbeddingModelRecord
from ai_comp.database.repository import RepositoryError


class PostgresEmbeddingRepository:
    """PostgreSQL/pgvector persistence for model-versioned question embeddings."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def save_model(self, model: EmbeddingModelRecord) -> None:
        try:
            with self._connection.transaction():
                self._connection.execute(
                    """
                    INSERT INTO embedding_models (
                        model_id, provider, model_name, dimensions, version, active
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (model_id) DO UPDATE SET
                        provider = EXCLUDED.provider,
                        model_name = EXCLUDED.model_name,
                        dimensions = EXCLUDED.dimensions,
                        version = EXCLUDED.version,
                        active = EXCLUDED.active
                    """,
                    (
                        model.model_id,
                        model.provider,
                        model.model_name,
                        model.dimensions,
                        model.version,
                        model.active,
                    ),
                )
        except Exception as exc:
            raise RepositoryError("failed to persist embedding model") from exc

    def save_embedding(
        self,
        question_id: str,
        model_id: str,
        embedding: tuple[float, ...],
    ) -> None:
        if not embedding:
            raise ValueError("embedding must not be empty")
        vector_literal = "[" + ",".join(format(value, ".12g") for value in embedding) + "]"
        try:
            with self._connection.transaction():
                row = self._connection.execute(
                    """
                    SELECT dimensions
                    FROM embedding_models
                    WHERE model_id = %s
                    """,
                    (model_id,),
                ).fetchone()
                if row is None:
                    raise RepositoryError(
                        f"embedding model not found: {model_id}"
                    )
                if int(row[0]) != len(embedding):
                    raise ValueError(
                        "embedding dimension does not match model dimensions"
                    )

                self._connection.execute(
                    """
                    INSERT INTO question_embeddings (
                        question_id, model_id, embedding
                    )
                    VALUES (%s, %s, %s::vector)
                    ON CONFLICT (question_id, model_id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        created_at = NOW()
                    """,
                    (question_id, model_id, vector_literal),
                )
        except (RepositoryError, ValueError):
            raise
        except Exception as exc:
            raise RepositoryError("failed to persist question embedding") from exc

    def get_embedding(
        self,
        question_id: str,
        model_id: str,
    ) -> tuple[float, ...] | None:
        try:
            row = self._connection.execute(
                """
                SELECT embedding::text
                FROM question_embeddings
                WHERE question_id = %s
                  AND model_id = %s
                """,
                (question_id, model_id),
            ).fetchone()
        except Exception as exc:
            raise RepositoryError("failed to read question embedding") from exc

        if row is None:
            return None

        raw = str(row[0]).strip()
        if not (raw.startswith("[") and raw.endswith("]")):
            raise RepositoryError("database returned an invalid vector literal")
        values = raw[1:-1].strip()
        if not values:
            return ()
        return tuple(float(item.strip()) for item in values.split(","))
