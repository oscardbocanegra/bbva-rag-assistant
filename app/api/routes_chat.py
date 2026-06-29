from __future__ import annotations

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    ConversationMessageResponse,
    SourceResponse,
)
from app.conversation.conversation_service import ConversationService
from app.core.config import get_settings
from app.database.connection import get_db_session
from app.database.repositories import ConversationRepository
from app.ingestion.embedding_service import get_embedding_service
from app.rag.ollama_client import OllamaClient
from app.rag.rag_service import RAGService
from app.rag.retriever import QdrantRetriever

router = APIRouter(
    prefix="/api/v1",
    tags=["Chat"],
)


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


def build_conversation_service(
    db_session: Session,
) -> ConversationService:
    settings = get_settings()

    return ConversationService(
        db_session=db_session,
        rag_service=build_rag_service(),
        memory_messages=settings.conversation_memory_messages,
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
def chat(
    request: ChatRequest,
    db_session: Session = Depends(get_db_session),
) -> ChatResponse:
    question = request.message.strip()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El mensaje no puede estar vacío.",
        )

    conversation_service = build_conversation_service(db_session)

    try:
        start_time = time.perf_counter()

        session_id, rag_answer = conversation_service.ask(
            question=question,
            session_id=request.session_id,
        )

        latency_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        return ChatResponse(
            session_id=session_id,
            answer=rag_answer.answer,
            sources=[
                SourceResponse(
                    title=str(source["title"]),
                    url=str(source["url"]),
                    score=float(source["score"]),
                )
                for source in rag_answer.sources
            ],
            retrieved_chunks=rag_answer.retrieved_chunks,
            latency_ms=latency_ms,
        )

    except Exception as exc:
        import logging

        logger = logging.getLogger(__name__)

        logger.exception(
            "chat_generation_failed session_id=%s error=%s",
            request.session_id,
            str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "No fue posible generar una respuesta en este momento. "
                "Verifica que los servicios estén disponibles."
            ),
        ) from exc


@router.get(
    "/conversations/{session_id}",
    response_model=ConversationHistoryResponse,
)
def get_conversation_history(
    session_id: UUID,
    db_session: Session = Depends(get_db_session),
) -> ConversationHistoryResponse:
    repository = ConversationRepository(db_session)

    conversation_session = repository.get_session(session_id)

    if conversation_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la sesión solicitada.",
        )

    messages = repository.get_all_messages(session_id)

    return ConversationHistoryResponse(
        session_id=session_id,
        messages=[
            ConversationMessageResponse(
                message_id=message.message_id,
                role=message.role,
                content=message.content,
                latency_ms=message.latency_ms,
                retrieved_chunks=message.retrieved_chunks,
                created_at=message.created_at,
            )
            for message in messages
        ],
    )