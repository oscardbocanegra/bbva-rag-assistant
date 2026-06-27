from app.core.config import get_settings
from app.ingestion.embedding_service import get_embedding_service
from app.rag.retriever import QdrantRetriever


def main() -> None:
    settings = get_settings()

    embedding_service = get_embedding_service(
        model_name=settings.embedding_model
    )

    retriever = QdrantRetriever(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.qdrant_collection,
        embedding_service=embedding_service,
    )

    query = "¿Qué información tiene BBVA sobre ahorro y productos financieros?"

    results = retriever.retrieve(
        query=query,
        limit=3,
    )

    print(f"\nConsulta: {query}\n")

    for index, item in enumerate(results, start=1):
        print(f"[{index}] Score: {item.score:.4f}")
        print(f"Title: {item.title}")
        print(f"URL: {item.url}")
        print(f"Text: {item.text[:500]}")
        print("-" * 80)


if __name__ == "__main__":
    main()