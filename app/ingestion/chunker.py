from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    text: str
    chunk_index: int


class RecursiveTextChunker:
    """
    Divide documentos extensos conservando solapamiento entre chunks.
    """

    def __init__(
        self,
        chunk_size: int = 700,
        chunk_overlap: int = 120,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(
        self,
        document_id: str,
        text: str,
    ) -> list[TextChunk]:
        normalized_text = " ".join(text.split())

        if not normalized_text:
            return []

        chunks: list[TextChunk] = []
        start = 0
        chunk_index = 0
        text_length = len(normalized_text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            if end < text_length:
                boundary = normalized_text.rfind(" ", start, end)

                if boundary > start + (self.chunk_size // 2):
                    end = boundary

            chunk_text = normalized_text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        chunk_id=f"{document_id}_{chunk_index}",
                        text=chunk_text,
                        chunk_index=chunk_index,
                    )
                )

            if end >= text_length:
                break

            start = max(end - self.chunk_overlap, start + 1)
            chunk_index += 1

        return chunks