from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Genera embeddings para documentos y consultas usando un modelo local
    compatible con sentence-transformers.
    """

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Genera embeddings para fragmentos de documentos.

        E5 recomienda prefijar documentos con 'passage: '.
        """
        if not texts:
            return []

        prefixed_texts = [f"passage: {text}" for text in texts]

        embeddings = self.model.encode(
            prefixed_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return np.asarray(embeddings, dtype=float).tolist()

    def embed_query(self, query: str) -> list[float]:
        """
        Genera embedding para una consulta del usuario.

        E5 recomienda prefijar consultas con 'query: '.
        """
        embedding = self.model.encode(
            f"query: {query}",
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return np.asarray(embedding, dtype=float).tolist()


@lru_cache
def get_embedding_service(model_name: str) -> EmbeddingService:
    """
    Reutiliza una sola instancia del modelo por nombre.
    """
    return EmbeddingService(model_name=model_name)