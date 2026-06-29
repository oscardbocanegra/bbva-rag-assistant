from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """
    Crea y reutiliza el Engine de SQLAlchemy para PostgreSQL.
    """
    settings = get_settings()

    database_url = (
        f"postgresql+psycopg://"
        f"{settings.postgres_user}:"
        f"{settings.postgres_password}@"
        f"{settings.postgres_host}:"
        f"{settings.postgres_port}/"
        f"{settings.postgres_db}"
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """
    Fábrica reutilizable de sesiones para repositorios y endpoints.
    """
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency-style generator para asegurar cierre de sesión.
    """
    session = get_session_factory()()

    try:
        yield session
    finally:
        session.close()