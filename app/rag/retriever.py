from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient

from app.ingestion.embedding_service import EmbeddingService


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    score: float
    text: str
    title: str
    url: str
    metadata: dict[str, Any]


class QdrantRetriever:
    """
    Recupera chunks relevantes desde Qdrant usando similitud coseno.
    """

    def __init__(
        self,
        host: str,
        port: int,
        collection_name: str,
        embedding_service: EmbeddingService,
    ) -> None:
        self.collection_name = collection_name
        self.embedding_service = embedding_service
        self.client = QdrantClient(host=host, port=port)

    def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedChunk]:
        query_vector = self.embedding_service.embed_query(query)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )

        retrieved_chunks: list[RetrievedChunk] = []

        for result in results:
            payload = result.payload or {}

            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=str(payload.get("chunk_id", result.id)),
                    score=float(result.score),
                    text=str(payload.get("text", "")),
                    title=str(payload.get("title", "")),
                    url=str(payload.get("url", "")),
                    metadata=dict(payload),
                )
            )

        return retrieved_chunks