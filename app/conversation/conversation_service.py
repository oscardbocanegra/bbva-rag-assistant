from __future__ import annotations

import time
import uuid

from sqlalchemy.orm import Session

from app.conversation.memory_manager import ConversationMemoryManager
from app.database.repositories import ConversationRepository
from app.rag.rag_service import RAGAnswer, RAGService


class ConversationService:
    """
    Orquesta el flujo conversacional completo:

    session_id
        -> recupera memoria reciente
        -> guarda pregunta
        -> ejecuta RAG
        -> guarda respuesta y métricas
    """

    def __init__(
        self,
        db_session: Session,
        rag_service: RAGService,
        memory_messages: int,
    ) -> None:
        self.repository = ConversationRepository(db_session)
        self.memory_manager = ConversationMemoryManager(
            repository=self.repository,
            max_messages=memory_messages,
        )
        self.rag_service = rag_service

    def ask(
        self,
        question: str,
        session_id: uuid.UUID | None = None,
    ) -> tuple[uuid.UUID, RAGAnswer]:
        conversation_session = self.repository.get_or_create_session(
            session_id=session_id
        )

        history = self.memory_manager.get_history(
            session_id=conversation_session.session_id
        )

        self.repository.add_message(
            session_id=conversation_session.session_id,
            role="user",
            content=question,
        )

        start_time = time.perf_counter()

        rag_answer = self.rag_service.answer_question(
            question=question,
            conversation_history=history,
        )

        latency_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        self.repository.add_message(
            session_id=conversation_session.session_id,
            role="assistant",
            content=rag_answer.answer,
            latency_ms=latency_ms,
            retrieved_chunks=rag_answer.retrieved_chunks,
        )

        return conversation_session.session_id, rag_answer