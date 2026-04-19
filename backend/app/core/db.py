"""
Database engine and session factory.
Supports SQLite (local) and PostgreSQL (server) via DATABASE_URL env var.
SQLModel is used as the ORM — models define both the DB table and Pydantic schema base.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings


def _build_engine() -> AsyncEngine:
    url = settings.database_url

    # SQLite needs special handling for async + same-thread access
    if url.startswith("sqlite"):
        # Convert sync sqlite:/// to async sqlite+aiosqlite:///
        async_url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return create_async_engine(
            async_url,
            echo=False,
            # StaticPool required for SQLite in-memory or single-file async use
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    # PostgreSQL — convert to asyncpg driver
    async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
        "postgres://", "postgresql+asyncpg://", 1
    )
    return create_async_engine(async_url, echo=False, pool_pre_ping=True)


engine = _build_engine()


async def init_db() -> None:
    """Create all tables on startup (dev convenience — prod uses Alembic migrations)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
