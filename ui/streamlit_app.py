from __future__ import annotations

import os
from typing import Any

import httpx
import pandas as pd
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


def get_api_data(endpoint: str) -> Any:
    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = client.get(
            f"{API_BASE_URL}{endpoint}"
        )
        response.raise_for_status()

        return response.json()


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


def render_chat() -> None:
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
                st.error(
                    "La API respondió con un error. "
                    f"Detalle: {exc.response.text}"
                )

            except httpx.HTTPError as exc:
                st.error(
                    "No fue posible conectar con el servicio RAG. "
                    f"Detalle: {str(exc)}"
                )


def render_analytics() -> None:
    st.subheader("Analítica conversacional")
    st.caption(
        "Métricas calculadas a partir del historial persistido "
        "en PostgreSQL."
    )

    try:
        summary = get_api_data("/api/v1/analytics/summary")
        daily_activity = get_api_data("/api/v1/analytics/daily-activity")
        recent_sessions = get_api_data("/api/v1/analytics/recent-sessions")
        recent_questions = get_api_data("/api/v1/analytics/recent-questions")

    except httpx.HTTPError as exc:
        st.error(
            "No fue posible cargar las métricas. "
            f"Detalle: {str(exc)}"
        )
        return

    metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)

    metric_col_1.metric(
        "Sesiones",
        summary.get("total_sessions", 0),
    )

    metric_col_2.metric(
        "Preguntas",
        summary.get("total_questions", 0),
    )

    metric_col_3.metric(
        "Mensajes",
        summary.get("total_messages", 0),
    )

    average_latency_ms = summary.get("average_latency_ms")

    metric_col_4.metric(
        "Latencia promedio",
        f"{average_latency_ms:,.0f} ms"
        if average_latency_ms is not None
        else "N/A",
    )

    st.divider()

    activity_col, performance_col = st.columns(2)

    with activity_col:
        st.markdown("### Actividad diaria")

        if daily_activity:
            activity_df = pd.DataFrame(daily_activity)
            activity_df["date"] = pd.to_datetime(activity_df["date"])
            activity_df = activity_df.set_index("date")

            st.line_chart(
                activity_df[
                    [
                        "questions",
                        "answers",
                    ]
                ]
            )
        else:
            st.info("Aún no hay actividad registrada.")

    with performance_col:
        st.markdown("### Indicadores operativos")

        st.metric(
            "Mensajes por sesión",
            summary.get("average_messages_per_session", 0),
        )

        st.metric(
            "Chunks recuperados",
            summary.get("average_retrieved_chunks", 0),
        )

        st.metric(
            "Respuestas generadas",
            summary.get("total_answers", 0),
        )

    st.divider()

    st.markdown("### Sesiones recientes")

    if recent_sessions:
        sessions_df = pd.DataFrame(recent_sessions)

        st.dataframe(
            sessions_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No hay sesiones registradas.")

    st.markdown("### Preguntas recientes")

    if recent_questions:
        questions_df = pd.DataFrame(recent_questions)

        st.dataframe(
            questions_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No hay preguntas registradas.")


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
            health_data = get_api_data("/health")

            if health_data.get("status") == "ok":
                st.success("API disponible")
            else:
                st.warning("La API respondió con estado inesperado.")

        except httpx.HTTPError:
            st.error("No fue posible conectar con la API.")

        st.caption(f"API: {API_BASE_URL}")

    chat_tab, analytics_tab = st.tabs(
        [
            "Chat",
            "Analítica",
        ]
    )

    with chat_tab:
        render_chat()

    with analytics_tab:
        render_analytics()


if __name__ == "__main__":
    main()