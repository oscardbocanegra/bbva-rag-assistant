from __future__ import annotations

import uuid

from app.database.repositories import ConversationRepository


class ConversationMemoryManager:
    """
    Gestiona la memoria conversacional limitada a N mensajes previos.
    """

    def __init__(
        self,
        repository: ConversationRepository,
        max_messages: int,
    ) -> None:
        self.repository = repository
        self.max_messages = max_messages

    def get_history(
        self,
        session_id: uuid.UUID,
    ) -> list[dict[str, str]]:
        """
        Convierte mensajes persistidos a formato compatible con Ollama.
        """
        messages = self.repository.get_recent_messages(
            session_id=session_id,
            limit=self.max_messages,
        )

        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]