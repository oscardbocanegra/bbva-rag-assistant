from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: UUID | None = None
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="Pregunta del usuario.",
    )


class SourceResponse(BaseModel):
    title: str
    url: str
    score: float


class ChatResponse(BaseModel):
    session_id: UUID
    answer: str
    sources: list[SourceResponse]
    retrieved_chunks: int
    latency_ms: int | None = None


class ConversationMessageResponse(BaseModel):
    message_id: UUID
    role: str
    content: str
    latency_ms: int | None = None
    retrieved_chunks: int | None = None
    created_at: datetime


class ConversationHistoryResponse(BaseModel):
    session_id: UUID
    messages: list[ConversationMessageResponse]