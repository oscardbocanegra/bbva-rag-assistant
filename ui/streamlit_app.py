from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000",
).rstrip("/")

REQUEST_TIMEOUT_SECONDS = 180


def initialize_session_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []


def call_chat_api(message: str) -> dict[str, Any]:
    payload: dict[str, str] = {
        "message": message,
    }

    if st.session_state.session_id:
        payload["session_id"] = st.session_state.session_id

    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = client.post(
            f"{API_BASE_URL}/api/v1/chat",
            json=payload,
        )

        response.raise_for_status()

        return response.json()


def load_conversation_history(session_id: str) -> list[dict[str, Any]]:
    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = client.get(
            f"{API_BASE_URL}/api/v1/conversations/{session_id}"
        )

        response.raise_for_status()

        data = response.json()

    return data.get("messages", [])


def start_new_conversation() -> None:
    st.session_state.session_id = None
    st.session_state.chat_messages = []


def render_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        return

    with st.expander("Fuentes consultadas"):
        for source in sources:
            title = source.get("title", "Fuente sin título")
            url = source.get("url", "")
            score = source.get("score", 0)

            st.markdown(
                f"**{title}**  \n"
                f"Score: `{score}`  \n"
                f"{url}"
            )


def main() -> None:
    st.set_page_config(
        page_title="BBVA RAG Assistant",
        page_icon="💬",
        layout="wide",
    )

    initialize_session_state()

    st.title("BBVA RAG Assistant")
    st.caption(
        "Asistente conversacional basado en contenido institucional "
        "de BBVA Colombia."
    )

    with st.sidebar:
        st.header("Sesión")

        if st.session_state.session_id:
            st.success("Sesión activa")
            st.code(st.session_state.session_id)
        else:
            st.info("Aún no hay una sesión activa.")

        if st.button("Nueva conversación", use_container_width=True):
            start_new_conversation()
            st.rerun()

        st.divider()

        st.header("Estado")

        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(f"{API_BASE_URL}/health")

            if response.status_code == 200:
                st.success("API disponible")
            else:
                st.warning("API respondió con estado inesperado.")

        except httpx.HTTPError:
            st.error("No fue posible conectar con la API.")

        st.caption(f"API: {API_BASE_URL}")

    for item in st.session_state.chat_messages:
        role = item["role"]

        with st.chat_message(role):
            st.markdown(item["content"])

            if role == "assistant":
                render_sources(item.get("sources", []))

                latency_ms = item.get("latency_ms")

                if latency_ms is not None:
                    st.caption(f"Latencia: {latency_ms} ms")

    user_question = st.chat_input(
        "Escribe una pregunta sobre el contenido de BBVA..."
    )

    if not user_question:
        return

    st.session_state.chat_messages.append(
        {
            "role": "user",
            "content": user_question,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Consultando contenido institucional..."):
            try:
                response_data = call_chat_api(user_question)

                st.session_state.session_id = response_data["session_id"]

                answer = response_data["answer"]
                sources = response_data.get("sources", [])
                latency_ms = response_data.get("latency_ms")

                st.markdown(answer)
                render_sources(sources)

                if latency_ms is not None:
                    st.caption(f"Latencia: {latency_ms} ms")

                st.session_state.chat_messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "latency_ms": latency_ms,
                    }
                )

            except httpx.HTTPStatusError as exc:
                error_detail = exc.response.text

                st.error(
                    "La API respondió con un error. "
                    f"Detalle: {error_detail}"
                )

            except httpx.HTTPError as exc:
                st.error(
                    "No fue posible conectar con el servicio RAG. "
                    f"Detalle: {str(exc)}"
                )


if __name__ == "__main__":
    main()