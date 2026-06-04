"""
CyberGhost OSINT Enterprise — Async Database Layer
SQLAlchemy 2.0 async engine + session management
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import structlog
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings

log = structlog.get_logger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_async_engine(
    str(settings.db.url),
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    echo=settings.db.echo,
    pool_pre_ping=True,  # detect stale connections
    pool_recycle=3600,   # recycle connections hourly
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Base Model ────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    type_annotation_map: dict[type, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dict — excludes private attributes."""
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }


# ── Session Dependency ────────────────────────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an async database session.
    Session is automatically committed/rolled back.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Lifecycle ─────────────────────────────────────────────────────────────────


async def create_all_tables() -> None:
    """Create all tables — use Alembic for production migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("database_tables_created")


async def drop_all_tables() -> None:
    """Drop all tables — DANGEROUS, use only in tests."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    log.warning("database_tables_dropped")


async def check_database_health() -> dict[str, Any]:
    """Health check for database connectivity."""
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1 as health"))
            row = result.fetchone()
            return {"status": "healthy", "result": row[0] if row else None}
    except Exception as e:
        log.error("database_health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}
