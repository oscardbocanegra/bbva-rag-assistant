from app.database.connection import get_db_session
from app.database.repositories import ConversationRepository
from app.conversation.memory_manager import ConversationMemoryManager


def main() -> None:
    with next(get_db_session()) as db_session:
        repository = ConversationRepository(db_session)

        conversation = repository.get_or_create_session()

        repository.add_message(
            session_id=conversation.session_id,
            role="user",
            content="¿Qué opciones de ahorro menciona BBVA?",
        )

        repository.add_message(
            session_id=conversation.session_id,
            role="assistant",
            content="BBVA menciona herramientas para ahorrar y planear gastos.",
            latency_ms=1200,
            retrieved_chunks=3,
        )

        memory_manager = ConversationMemoryManager(
            repository=repository,
            max_messages=6,
        )

        history = memory_manager.get_history(
            session_id=conversation.session_id
        )

        print(f"Session ID: {conversation.session_id}")
        print("History:")

        for message in history:
            print(f"- {message['role']}: {message['content']}")


if __name__ == "__main__":
    main()