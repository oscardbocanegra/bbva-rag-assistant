from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.ingestion.chunker import RecursiveTextChunker
from app.ingestion.embedding_service import EmbeddingService
from app.ingestion.qdrant_indexer import QdrantIndexer


class DocumentProcessor:
    """
    Lee documentos procesados, genera chunks, embeddings y los indexa en Qdrant.
    """

    def __init__(
        self,
        processed_data_path: str,
        chunker: RecursiveTextChunker,
        embedding_service: EmbeddingService,
        qdrant_indexer: QdrantIndexer,
    ) -> None:
        self.processed_data_path = Path(processed_data_path)
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.qdrant_indexer = qdrant_indexer

    def process_all(self) -> dict[str, Any]:
        documents = self._load_documents()

        if not documents:
            raise FileNotFoundError(
                f"No se encontraron documentos JSON en: {self.processed_data_path}"
            )

        total_documents = 0
        total_chunks = 0

        for document in documents:
            chunk_count = self._process_document(document)

            total_documents += 1
            total_chunks += chunk_count

            print(
                f"OK - {document['document_id']} | "
                f"{chunk_count} chunks indexados"
            )

        return {
            "documents_processed": total_documents,
            "chunks_indexed": total_chunks,
            "collection_name": self.qdrant_indexer.collection_name,
        }

    def _process_document(self, document: dict[str, Any]) -> int:
        document_id = document["document_id"]
        content = document.get("content", "")

        chunks = self.chunker.split_text(
            document_id=document_id,
            text=content,
        )

        if not chunks:
            return 0

        embeddings = self.embedding_service.embed_documents(
            [chunk.text for chunk in chunks]
        )

        vector_size = len(embeddings[0])
        self.qdrant_indexer.ensure_collection(vector_size=vector_size)

        points = []

        for chunk, embedding in zip(chunks, embeddings, strict=True):
            payload = {
                "document_id": document_id,
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "title": document.get("title", ""),
                "url": document.get("url", ""),
                "domain": document.get("domain", ""),
                "source_type": document.get("source_type", ""),
                "source_file": document.get("source_file", ""),
                "content_hash": document.get("content_hash", ""),
            }

            points.append(
                self.qdrant_indexer.build_point(
                    point_id=chunk.chunk_id,
                    vector=embedding,
                    payload=payload,
                )
            )

        self.qdrant_indexer.upsert_chunks(points)

        return len(points)

    def _load_documents(self) -> list[dict[str, Any]]:
        document_files = sorted(
            self.processed_data_path.glob("*.json")
        )

        documents: list[dict[str, Any]] = []

        for document_file in document_files:
            with document_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                document = json.load(file)

            if "document_id" not in document:
                continue

            if not document.get("content"):
                continue

            documents.append(document)

        return documents