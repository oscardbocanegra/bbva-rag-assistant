from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.analytics_service import AnalyticsService
from app.database.connection import get_db_session

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"],
)


@router.get("/summary")
def get_summary(
    db_session: Session = Depends(get_db_session),
) -> dict:
    return AnalyticsService(db_session).get_summary()


@router.get("/daily-activity")
def get_daily_activity(
    db_session: Session = Depends(get_db_session),
) -> list[dict]:
    return AnalyticsService(db_session).get_daily_activity()


@router.get("/recent-sessions")
def get_recent_sessions(
    limit: int = 20,
    db_session: Session = Depends(get_db_session),
) -> list[dict]:
    return AnalyticsService(db_session).get_recent_sessions(
        limit=limit
    )


@router.get("/recent-questions")
def get_recent_questions(
    limit: int = 20,
    db_session: Session = Depends(get_db_session),
) -> list[dict]:
    return AnalyticsService(db_session).get_recent_questions(
        limit=limit
    )