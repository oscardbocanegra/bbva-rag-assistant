from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Sistema RAG con web scraping para contenido institucional.",
)


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "service": settings.app_name,
    }


@app.get("/", tags=["Health"])
def root() -> dict:
    return {
        "message": "BBVA RAG Assistant API is running",
        "docs": "/docs",
    }