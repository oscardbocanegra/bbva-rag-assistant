from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import ConversationMessage, ConversationSession


class ConversationRepository:
    """
    Repository Pattern para encapsular acceso a sesiones y mensajes.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_session(
        self,
        session_id: uuid.UUID | None = None,
    ) -> ConversationSession:
        """
        Recupera una sesión existente o crea una nueva.
        """
        if session_id is not None:
            conversation_session = self.session.get(
                ConversationSession,
                session_id,
            )

            if conversation_session is not None:
                return conversation_session

        conversation_session = ConversationSession(
            session_id=session_id or uuid.uuid4()
        )

        self.session.add(conversation_session)
        self.session.commit()
        self.session.refresh(conversation_session)

        return conversation_session

    def add_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        latency_ms: int | None = None,
        retrieved_chunks: int | None = None,
    ) -> ConversationMessage:
        """
        Persiste un mensaje de usuario o asistente.
        """
        message = ConversationMessage(
            session_id=session_id,
            role=role,
            content=content,
            latency_ms=latency_ms,
            retrieved_chunks=retrieved_chunks,
        )

        self.session.add(message)

        conversation_session = self.session.get(
            ConversationSession,
            session_id,
        )

        if conversation_session is not None:
            conversation_session.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(message)

        return message

    def get_recent_messages(
        self,
        session_id: uuid.UUID,
        limit: int,
    ) -> list[ConversationMessage]:
        """
        Devuelve los últimos N mensajes ordenados cronológicamente.
        """
        statement = (
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )

        messages: Sequence[ConversationMessage] = (
            self.session.execute(statement)
            .scalars()
            .all()
        )

        return list(reversed(messages))

    def get_all_messages(
        self,
        session_id: uuid.UUID,
    ) -> list[ConversationMessage]:
        """
        Devuelve todo el historial de una sesión.
        """
        statement = (
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at.asc())
        )

        return list(
            self.session.execute(statement)
            .scalars()
            .all()
        )
    
    def get_session(
        self,
        session_id: uuid.UUID,
    ) -> ConversationSession | None:
        """
        Busca una sesión existente por su UUID.
        """
        return self.session.get(
            ConversationSession,
            session_id,
        )