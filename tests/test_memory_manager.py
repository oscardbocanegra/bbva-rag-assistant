import uuid
from dataclasses import dataclass

from app.conversation.memory_manager import ConversationMemoryManager


@dataclass
class FakeMessage:
    role: str
    content: str


class FakeConversationRepository:
    def get_recent_messages(
        self,
        session_id: uuid.UUID,
        limit: int,
    ) -> list[FakeMessage]:
        messages = [
            FakeMessage(
                role="user",
                content="¿Qué opciones de ahorro existen?",
            ),
            FakeMessage(
                role="assistant",
                content="BBVA menciona herramientas de ahorro.",
            ),
            FakeMessage(
                role="user",
                content="¿Y cómo puedo aprender más?",
            ),
        ]

        return messages[-limit:]


def test_memory_manager_returns_messages_in_ollama_format() -> None:
    repository = FakeConversationRepository()

    memory_manager = ConversationMemoryManager(
        repository=repository,
        max_messages=2,
    )

    history = memory_manager.get_history(
        session_id=uuid.uuid4()
    )

    assert len(history) == 2
    assert history[0]["role"] == "assistant"
    assert history[1]["role"] == "user"
    assert "aprender más" in history[1]["content"]