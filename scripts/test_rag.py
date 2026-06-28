from app.core.config import get_settings
from app.ingestion.embedding_service import get_embedding_service
from app.rag.ollama_client import OllamaClient
from app.rag.rag_service import RAGService
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

    llm_client = OllamaClient(
        base_url=settings.ollama_host,
        model_name=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )

    rag_service = RAGService(
        retriever=retriever,
        llm_client=llm_client,
        top_k=3,
    )

    question = "¿Qué información ofrece BBVA sobre ahorro y educación financiera?"

    print("Procesando pregunta...", flush=True)

    result = rag_service.answer_question(question)

    print("\nPregunta:")
    print(question)

    print("\nRespuesta:")
    print(result.answer)

    print("\nFuentes:")
    for source in result.sources:
        print(
            f"- {source['title']} | "
            f"{source['url']} | "
            f"score={source['score']}"
        )

    print(f"\nChunks recuperados: {result.retrieved_chunks}")
    print(f"Duración total ns: {result.total_duration_ns}")


if __name__ == "__main__":
    main()