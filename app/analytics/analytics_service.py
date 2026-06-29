from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.orm import Session

from app.database.models import ConversationMessage, ConversationSession


class AnalyticsService:
    """
    Calcula métricas agregadas a partir del historial persistido
    de sesiones y mensajes conversacionales.
    """

    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_summary(self) -> dict[str, Any]:
        total_sessions = self.db_session.scalar(
            select(func.count()).select_from(ConversationSession)
        ) or 0

        total_messages = self.db_session.scalar(
            select(func.count()).select_from(ConversationMessage)
        ) or 0

        total_questions = self.db_session.scalar(
            select(func.count())
            .select_from(ConversationMessage)
            .where(ConversationMessage.role == "user")
        ) or 0

        total_answers = self.db_session.scalar(
            select(func.count())
            .select_from(ConversationMessage)
            .where(ConversationMessage.role == "assistant")
        ) or 0

        average_latency_ms = self.db_session.scalar(
            select(func.avg(ConversationMessage.latency_ms))
            .where(
                ConversationMessage.role == "assistant",
                ConversationMessage.latency_ms.is_not(None),
            )
        )

        average_retrieved_chunks = self.db_session.scalar(
            select(func.avg(ConversationMessage.retrieved_chunks))
            .where(
                ConversationMessage.role == "assistant",
                ConversationMessage.retrieved_chunks.is_not(None),
            )
        )

        average_messages_per_session = (
            round(total_messages / total_sessions, 2)
            if total_sessions > 0
            else 0
        )

        return {
            "total_sessions": int(total_sessions),
            "total_messages": int(total_messages),
            "total_questions": int(total_questions),
            "total_answers": int(total_answers),
            "average_messages_per_session": average_messages_per_session,
            "average_latency_ms": (
                round(float(average_latency_ms), 2)
                if average_latency_ms is not None
                else None
            ),
            "average_retrieved_chunks": (
                round(float(average_retrieved_chunks), 2)
                if average_retrieved_chunks is not None
                else None
            ),
        }

    def get_daily_activity(self) -> list[dict[str, Any]]:
        activity_date = cast(
            ConversationMessage.created_at,
            Date,
        ).label("activity_date")

        statement = (
            select(
                activity_date,
                func.count().label("messages"),
                func.sum(
                    case(
                        (
                            ConversationMessage.role == "user",
                            1,
                        ),
                        else_=0,
                    )
                ).label("questions"),
                func.sum(
                    case(
                        (
                            ConversationMessage.role == "assistant",
                            1,
                        ),
                        else_=0,
                    )
                ).label("answers"),
            )
            .group_by(activity_date)
            .order_by(activity_date.asc())
        )

        rows = self.db_session.execute(statement).all()

        return [
            {
                "date": row.activity_date.isoformat(),
                "messages": int(row.messages or 0),
                "questions": int(row.questions or 0),
                "answers": int(row.answers or 0),
            }
            for row in rows
        ]

    def get_recent_sessions(
        self,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        latest_message_at = func.max(
            ConversationMessage.created_at
        ).label("latest_message_at")

        message_count = func.count(
            ConversationMessage.message_id
        ).label("message_count")

        question_count = func.sum(
            case(
                (
                    ConversationMessage.role == "user",
                    1,
                ),
                else_=0,
            )
        ).label("question_count")

        statement = (
            select(
                ConversationSession.session_id,
                ConversationSession.created_at,
                ConversationSession.updated_at,
                latest_message_at,
                message_count,
                question_count,
            )
            .outerjoin(
                ConversationMessage,
                ConversationSession.session_id
                == ConversationMessage.session_id,
            )
            .group_by(
                ConversationSession.session_id,
                ConversationSession.created_at,
                ConversationSession.updated_at,
            )
            .order_by(
                latest_message_at.desc().nullslast()
            )
            .limit(limit)
        )

        rows = self.db_session.execute(statement).all()

        return [
            {
                "session_id": str(row.session_id),
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat(),
                "latest_message_at": (
                    row.latest_message_at.isoformat()
                    if row.latest_message_at
                    else None
                ),
                "message_count": int(row.message_count or 0),
                "question_count": int(row.question_count or 0),
            }
            for row in rows
        ]

    def get_recent_questions(
        self,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        statement = (
            select(
                ConversationMessage.session_id,
                ConversationMessage.content,
                ConversationMessage.created_at,
            )
            .where(ConversationMessage.role == "user")
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )

        rows = self.db_session.execute(statement).all()

        return [
            {
                "session_id": str(row.session_id),
                "question": row.content,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]