from app.conversation.conversation_service import ConversationService
from app.core.config import get_settings
from app.database.connection import get_db_session
from app.ingestion.embedding_service import get_embedding_service
from app.rag.ollama_client import OllamaClient
from app.rag.rag_service import RAGService
from app.rag.retriever import QdrantRetriever


def build_rag_service() -> RAGService:
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

    return RAGService(
        retriever=retriever,
        llm_client=llm_client,
        top_k=3,
    )


def main() -> None:
    settings = get_settings()
    rag_service = build_rag_service()

    with next(get_db_session()) as db_session:
        conversation_service = ConversationService(
            db_session=db_session,
            rag_service=rag_service,
            memory_messages=settings.conversation_memory_messages,
        )

        session_id, first_answer = conversation_service.ask(
            question="¿Qué menciona BBVA sobre ahorro?"
        )

        print(f"\nSession ID: {session_id}")
        print("\nPregunta 1:")
        print("¿Qué menciona BBVA sobre ahorro?")

        print("\nRespuesta 1:")
        print(first_answer.answer)

        _, second_answer = conversation_service.ask(
            session_id=session_id,
            question="¿Y cómo puedo aprender más sobre ese tema?"
        )

        print("\nPregunta 2:")
        print("¿Y cómo puedo aprender más sobre ese tema?")

        print("\nRespuesta 2:")
        print(second_answer.answer)

        print("\nChunks recuperados:")
        print(second_answer.retrieved_chunks)


if __name__ == "__main__":
    main()