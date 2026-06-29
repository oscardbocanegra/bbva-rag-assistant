from __future__ import annotations

from dataclasses import dataclass

from app.rag.ollama_client import OllamaClient
from app.rag.retriever import QdrantRetriever, RetrievedChunk


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    sources: list[dict[str, str | float]]
    retrieved_chunks: int
    total_duration_ns: int | None


class RAGService:
    """
    Orquesta recuperación semántica, memoria conversacional
    y generación grounded con Ollama.
    """

    def __init__(
        self,
        retriever: QdrantRetriever,
        llm_client: OllamaClient,
        top_k: int = 3,
    ) -> None:
        self.retriever = retriever
        self.llm_client = llm_client
        self.top_k = top_k

    def answer_question(
        self,
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> RAGAnswer:
        chunks = self.retriever.retrieve(
            query=question,
            limit=self.top_k,
        )

        if not chunks:
            return RAGAnswer(
                answer=(
                    "No encontré información relevante en el contenido "
                    "institucional disponible de BBVA."
                ),
                sources=[],
                retrieved_chunks=0,
                total_duration_ns=None,
            )

        context = self._build_context(chunks)

        system_message = {
            "role": "system",
            "content": (
                "Eres un asistente interno de BBVA Colombia. "
                "Responde únicamente con base en el contexto suministrado. "
                "No inventes productos, condiciones, cifras ni políticas. "
                "Si el contexto no contiene evidencia suficiente, dilo claramente. "
                "Usa el historial conversacional solo para comprender referencias "
                "como 'eso', 'lo anterior' o 'esa opción'. "
                "Responde en español de forma clara y concisa."
            ),
        }

        context_message = {
            "role": "user",
            "content": (
                f"Contexto recuperado:\n\n{context}\n\n"
                f"Pregunta actual del usuario: {question}"
            ),
        }

        messages = [system_message]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append(context_message)

        response = self.llm_client.chat(messages)

        return RAGAnswer(
            answer=response.content,
            sources=self._build_sources(chunks),
            retrieved_chunks=len(chunks),
            total_duration_ns=response.total_duration_ns,
        )

    @staticmethod
    def _build_context(chunks: list[RetrievedChunk]) -> str:
        sections: list[str] = []

        for index, chunk in enumerate(chunks, start=1):
            sections.append(
                f"[Fuente {index}]\n"
                f"Título: {chunk.title}\n"
                f"URL: {chunk.url}\n"
                f"Contenido: {chunk.text}"
            )

        return "\n\n".join(sections)

    @staticmethod
    def _build_sources(
        chunks: list[RetrievedChunk],
    ) -> list[dict[str, str | float]]:
        unique_sources: dict[str, dict[str, str | float]] = {}

        for chunk in chunks:
            if chunk.url not in unique_sources:
                unique_sources[chunk.url] = {
                    "title": chunk.title,
                    "url": chunk.url,
                    "score": round(chunk.score, 4),
                }

        return list(unique_sources.values())