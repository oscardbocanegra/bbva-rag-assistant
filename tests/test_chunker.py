from app.ingestion.chunker import RecursiveTextChunker


def test_chunker_splits_long_text_with_overlap() -> None:
    chunker = RecursiveTextChunker(
        chunk_size=50,
        chunk_overlap=10,
    )

    text = (
        "BBVA ofrece herramientas para cuidar las finanzas personales. "
        "También dispone de contenidos sobre ahorro, crédito y educación financiera. "
        "Los usuarios pueden consultar información institucional en línea."
    )

    chunks = chunker.split_text(
        document_id="document_001",
        text=text,
    )

    assert len(chunks) > 1
    assert chunks[0].chunk_id == "document_001_0"
    assert chunks[1].chunk_id == "document_001_1"

    assert all(chunk.text for chunk in chunks)
    assert all(len(chunk.text) <= 50 for chunk in chunks)


def test_chunker_returns_empty_list_for_empty_text() -> None:
    chunker = RecursiveTextChunker()

    chunks = chunker.split_text(
        document_id="document_001",
        text="   ",
    )

    assert chunks == []