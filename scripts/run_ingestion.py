from app.core.config import get_settings
from app.ingestion.chunker import RecursiveTextChunker
from app.ingestion.document_processor import DocumentProcessor
from app.ingestion.embedding_service import get_embedding_service
from app.ingestion.qdrant_indexer import QdrantIndexer


def main() -> None:
    settings = get_settings()

    chunker = RecursiveTextChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    embedding_service = get_embedding_service(
        model_name=settings.embedding_model
    )

    qdrant_indexer = QdrantIndexer(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.qdrant_collection,
    )

    processor = DocumentProcessor(
        processed_data_path="data/processed",
        chunker=chunker,
        embedding_service=embedding_service,
        qdrant_indexer=qdrant_indexer,
    )

    result = processor.process_all()

    print("\nIngestion completed")
    print(f"Documents processed: {result['documents_processed']}")
    print(f"Chunks indexed: {result['chunks_indexed']}")
    print(f"Collection: {result['collection_name']}")


if __name__ == "__main__":
    main()