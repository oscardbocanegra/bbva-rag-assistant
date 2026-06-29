from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.analytics.routes_analytics import router as analytics_router
from app.api.routes_chat import router as chat_router
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()

logger = logging.getLogger(__name__)

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
app.include_router(analytics_router)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        latency_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        logger.info(
            "request_id=%s method=%s path=%s status=%s latency_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
        )

        response.headers["X-Request-ID"] = request_id

        return response

    except Exception:
        logger.exception(
            "request_id=%s method=%s path=%s unexpected_error",
            request_id,
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": (
                    "Ocurrió un error interno al procesar la solicitud."
                ),
                "request_id": request_id,
            },
        )


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