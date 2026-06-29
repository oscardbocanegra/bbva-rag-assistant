from __future__ import annotations

from fastapi import FastAPI

from app.api.routes_chat import router as chat_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Sistema RAG con contenido institucional de BBVA, "
        "Qdrant, PostgreSQL y Ollama."
    ),
)

app.include_router(chat_router)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {
        "message": "BBVA RAG Assistant API is running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "service": settings.app_name,
    }