from __future__ import annotations

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class QdrantIndexer:
    """
    Adaptador para crear colección e indexar chunks en Qdrant.
    """

    def __init__(
        self,
        host: str,
        port: int,
        collection_name: str,
    ) -> None:
        self.collection_name = collection_name
        self.client = QdrantClient(host=host, port=port)

    def ensure_collection(self, vector_size: int) -> None:
        collections = self.client.get_collections().collections
        collection_names = {collection.name for collection in collections}

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def upsert_chunks(self, points: list[PointStruct]) -> None:
        if not points:
            return

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    @staticmethod
    def build_point(
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> PointStruct:
        """
        Qdrant exige UUID o entero como ID. UUID5 permite generar siempre
        el mismo ID para el mismo chunk, dejando el upsert idempotente.
        """
        qdrant_point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                point_id,
            )
        )

        return PointStruct(
            id=qdrant_point_id,
            vector=vector,
            payload=payload,
        )